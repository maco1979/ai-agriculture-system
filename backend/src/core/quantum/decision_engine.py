"""
量子决策引擎 (Quantum Collapse Inference - QCI)
==============================================
基于量子坍缩原理的决策推理系统

核心功能：
1. QCI: 量子坍缩推理 - 概率性决策输出
2. 不确定性量化 - 冯·诺依曼熵度量
3. 自适应计算 - 根据不确定性动态调整计算量

农业场景：
- 病害诊断决策（多可能性叠加态 → 确定性坍缩）
- 作物生长状态评估
- 异常检测与告警
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
import math
from enum import Enum

import torch
import torch.nn as nn
import torch.nn.functional as F

# ─────────────────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────────────────

class DecisionType(Enum):
    """决策类型"""
    CLASSIFICATION = "classification"    # 分类决策
    REGRESSION = "regression"            # 回归预测
    MULTI_LABEL = "multi_label"          # 多标签决策
    RANKING = "ranking"                 # 排序决策


@dataclass
class DecisionResult:
    """决策结果"""
    # 坍缩后的确定性输出
    decision: Any
    confidence: float
    
    # 叠加态信息
    superposition_probs: Optional[torch.Tensor] = None  # 各选项概率
    entropy: float = 0.0  # 冯·诺依曼熵
    uncertainty_level: str = "low"  # low/medium/high
    
    # 中间状态
    raw_logits: Optional[torch.Tensor] = None
    intermediate_states: Dict[str, Any] = field(default_factory=dict)
    
    # 决策路径
    collapsed_from_state: bool = False
    early_exit_layer: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "decision": self.decision,
            "confidence": float(self.confidence),
            "entropy": float(self.entropy),
            "uncertainty_level": self.uncertainty_level,
            "collapsed_from_state": self.collapsed_from_state,
            "early_exit_layer": self.early_exit_layer,
        }


@dataclass
class QCIConfig:
    """QCI配置"""
    # 坍缩阈值
    tau_low: float = 0.3   # 低阈值: 熵低于此值直接坍缩
    tau_high: float = 1.0   # 高阈值: 熵高于此值保持叠加态
    
    # 自适应计算
    enable_early_exit: bool = True
    max_layers: int = 6
    early_exit_ratio: float = 0.8  # 80%置信度触发早退
    
    # 决策类型
    decision_type: DecisionType = DecisionType.CLASSIFICATION
    
    # 输出配置
    top_k: int = 3  # 返回top-k选项
    temperature: float = 1.0  # 概率温度


# ─────────────────────────────────────────────────────────────────────────────
# 量子坍缩推理核心
# ─────────────────────────────────────────────────────────────────────────────

class QuantumCollapseInference:
    """
    量子坍缩推理引擎
    
    工作原理：
    1. 多层量子块处理后得到叠加态 |ψ⟩
    2. 计算冯·诺依曼熵 S(ρ) = -Tr(ρ log ρ)
    3. 根据熵值决定是否坍缩：
       - S < τ_low: 高确定性，直接坍缩
       - τ_low ≤ S ≤ τ_high: 中等确定性，保持叠加或选择性坍缩
       - S > τ_high: 高不确定性，保持叠加态或增加计算
    4. 坍缩操作将量子态投影到经典输出
    """
    
    def __init__(self, config: Optional[QCIConfig] = None):
        self.config = config or QCIConfig()
        cfg = self.config
        
        # 隐藏状态
        self.current_state: Optional[torch.Tensor] = None
        self.state_history: List[torch.Tensor] = []
        self.layer_entropies: List[float] = []
        
        # 统计
        self.total_collapses = 0
        self.total_early_exits = 0
        
    def reset(self):
        """重置状态"""
        self.current_state = None
        self.state_history = []
        self.layer_entropies = []
        
    def compute_von_neumann_entropy(self, state: torch.Tensor, dim: int = -1) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        计算冯·诺依曼熵
        
        对于纯态 |ψ⟩ = Σᵢ αᵢ |i⟩:
        S = -Σᵢ |αᵢ|² log |αᵢ|²
        """
        # Born 归一化
        state_flat = state.flatten(start_dim=1) if state.dim() > 2 else state
        
        # 计算振幅的模平方
        if state_flat.dtype.is_complex:
            probs = (state_flat * state_flat.conj()).abs().sum(dim=-1)
        else:
            probs = state_flat.abs().square().sum(dim=-1)
        
        # 归一化
        probs = probs / (probs.sum(dim=-1, keepdim=True) + 1e-10)
        
        # 计算熵
        entropy = -(probs * torch.log(probs + 1e-10)).sum(dim=-1)
        
        # 归一化熵
        dim_size = state_flat.shape[-1]
        max_entropy = math.log(dim_size)
        normalized_entropy = entropy / (max_entropy + 1e-10)
        
        return normalized_entropy.mean(), probs
    
    def should_collapse(self, entropy: float) -> Tuple[bool, str]:
        """判断是否应该坍缩"""
        cfg = self.config
        
        if entropy < cfg.tau_low:
            return True, f"高确定性 (熵={entropy:.3f} < τ_low={cfg.tau_low})"
        elif entropy > cfg.tau_high:
            return False, f"高不确定性 (熵={entropy:.3f} > τ_high={cfg.tau_high})"
        else:
            collapse_prob = (entropy - cfg.tau_low) / (cfg.tau_high - cfg.tau_low)
            should = torch.rand(1).item() < collapse_prob
            return should, f"概率坍缩 (p={collapse_prob:.2f})"
    
    def collapse_to_classification(
        self, 
        state: torch.Tensor, 
        class_names: Optional[List[str]] = None
    ) -> DecisionResult:
        """坍缩到分类决策"""
        cfg = self.config
        
        # 展平
        if state.dim() > 1:
            state = state[0] if state.shape[0] == 1 else state.mean(dim=0)
        
        # 计算概率分布
        probs = F.softmax(state.abs(), dim=-1)
        
        # 应用温度
        if cfg.temperature != 1.0:
            logits = state / cfg.temperature
            probs = F.softmax(logits.abs(), dim=-1)
        
        # 计算熵
        entropy, _ = self.compute_von_neumann_entropy(state.unsqueeze(0))
        entropy = entropy.item()
        
        # 判断坍缩
        should_collapse, reason = self.should_collapse(entropy)
        
        if not should_collapse:
            top_k = min(cfg.top_k, len(probs))
            top_probs, top_indices = torch.topk(probs, top_k)
            
            class_names = class_names or [f"class_{i}" for i in range(len(probs))]
            
            return DecisionResult(
                decision={
                    "top_predictions": [
                        {"class": class_names[idx], "prob": prob.item()}
                        for idx, prob in zip(top_indices, top_probs)
                    ],
                    "reason": reason,
                },
                confidence=top_probs[0].item(),
                superposition_probs=probs,
                entropy=entropy,
                uncertainty_level="medium" if entropy < 0.5 else "high",
            )
        
        # 坍缩
        self.total_collapses += 1
        
        if entropy < cfg.tau_low * 0.5:
            decision_idx = probs.argmax().item()
            confidence = probs[decision_idx].item()
        else:
            decision_idx = torch.multinomial(probs, 1).item()
            confidence = probs[decision_idx].item()
        
        class_names = class_names or [f"class_{i}" for i in range(len(probs))]
        decision_class = class_names[decision_idx]
        
        uncertainty_level = "low" if entropy < 0.3 else "medium" if entropy < 0.6 else "high"
        
        return DecisionResult(
            decision=decision_class,
            confidence=confidence,
            superposition_probs=probs,
            entropy=entropy,
            uncertainty_level=uncertainty_level,
            collapsed_from_state=True,
        )


class QuantumDecisionEngine(nn.Module):
    """量子决策引擎"""
    
    def __init__(
        self,
        input_dim: int,
        num_classes: int,
        hidden_dim: int = 256,
        num_layers: int = 4,
        config: Optional[QCIConfig] = None,
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.num_classes = num_classes
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.config = config or QCIConfig()
        
        # 输入投影
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # 量子处理层
        self.quantum_layers = nn.ModuleList([
            QuantumProcessingLayer(hidden_dim)
            for _ in range(num_layers)
        ])
        
        # QCI 引擎
        self.qci = QuantumCollapseInference(self.config)
        
        # 输出层
        self.output_proj = nn.Linear(hidden_dim, num_classes)
        
        # 层归一化
        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim)
            for _ in range(num_layers)
        ])
        
    def forward(
        self,
        features: torch.Tensor,
        class_names: Optional[List[str]] = None,
        return_all_layers: bool = False,
    ) -> DecisionResult:
        """决策前向传播"""
        # 处理序列输入
        if features.dim() == 3:
            features = features.mean(dim=1)
        
        # 输入投影
        x = self.input_proj(features)
        x = F.gelu(x)
        
        # 多层量子处理
        all_states = []
        
        for i, (layer, norm) in enumerate(zip(self.quantum_layers, self.layer_norms)):
            state = layer(x)
            x = norm(x + state)
            
            # 计算熵
            entropy, _ = self.qci.compute_von_neumann_entropy(x.unsqueeze(0))
            entropy = entropy.item()
            self.qci.layer_entropies.append(entropy)
            
            # 早退检查
            if self.config.enable_early_exit:
                if entropy < (1 - self.config.early_exit_ratio):
                    self.qci.total_early_exits += 1
                    result = self.qci.collapse_to_classification(
                        self.output_proj(x), class_names
                    )
                    result.early_exit_layer = i
                    return result
            
            all_states.append(x)
        
        # 最终输出
        logits = self.output_proj(x)
        
        return self.qci.collapse_to_classification(logits, class_names)
    
    def get_entropy_profile(self) -> List[float]:
        """获取各层熵分布"""
        return self.qci.layer_entropies.copy()


class QuantumProcessingLayer(nn.Module):
    """量子处理层"""
    
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim
        self.unitary_weight = nn.Parameter(torch.randn(dim, dim) * 0.02)
        self.gate = nn.Sequential(
            nn.Linear(dim, dim * 2),
            nn.GLU(),
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        weight = self.unitary_weight @ self.unitary_weight.T
        weight = weight / (weight.norm() + 1e-8)
        x_transformed = x @ weight
        gated = self.gate(x_transformed)
        return gated


def create_agriculture_disease_engine() -> Tuple[QuantumDecisionEngine, List[str]]:
    """创建农业病害决策引擎"""
    config = QCIConfig(
        tau_low=0.3,
        tau_high=1.0,
        enable_early_exit=True,
        decision_type=DecisionType.CLASSIFICATION,
        top_k=3,
    )
    
    disease_classes = [
        "healthy", "leaf_spot", "powdery_mildew", "blight",
        "root_rot", "bacterial_infection", "viral_infection",
        "nutrient_deficiency", "water_stress", "pest_damage",
    ]
    
    engine = QuantumDecisionEngine(
        input_dim=512, num_classes=len(disease_classes),
        hidden_dim=256, num_layers=4, config=config,
    )
    
    return engine, disease_classes


if __name__ == "__main__":
    print("=" * 60)
    print("量子决策引擎测试")
    print("=" * 60)
    
    engine, disease_classes = create_agriculture_disease_engine()
    engine.eval()
    
    print(f"\n引擎配置:")
    print(f"  决策类型: {engine.config.decision_type.value}")
    print(f"  早退启用: {engine.config.enable_early_exit}")
    print(f"  类别数: {len(disease_classes)}")
    
    torch.manual_seed(42)
    features = torch.randn(1, 512)
    
    with torch.no_grad():
        result = engine(features, disease_classes)
    
    print(f"\n决策结果:")
    print(f"  决策: {result.decision}")
    print(f"  置信度: {result.confidence:.3f}")
    print(f"  熵: {result.entropy:.4f}")
    print(f"  不确定性: {result.uncertainty_level}")
    
    entropy_profile = engine.get_entropy_profile()
    print(f"\n各层熵分布: {[f'{e:.4f}' for e in entropy_profile]}")
    
    print("\n✅ 量子决策引擎测试完成")
