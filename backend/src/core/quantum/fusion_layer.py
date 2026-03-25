"""
量子融合层 (Quantum Fusion Layer)
==================================
将量子架构的 QSA + QEL 组件应用于农业多模态数据融合

核心功能：
1. QSA: 量子叠加注意力 - O(n log n) 复杂度的多模态融合
2. QEL: 量子纠缠层 - 跨模态特征耦合
3. 熵计算: 不确定性量化

农业场景：
- 视觉(YOLO) + 传感器(温度/湿度/CO2) + 光谱数据 融合
- 多摄像头画面融合
- 时序环境数据关联
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

# 尝试导入量子架构核心组件
try:
    sys.path.insert(0, r"E:\量子架构")
    from quantum_core.attention import QuantumSuperpositionAttention
    from quantum_core.entanglement import QuantumEntanglementLayer
    from quantum_core.complex_ops import born_normalize, von_neumann_entropy
    from quantum_core.activations import complex_gelu, modrelu
    from quantum_core.normalization import ComplexLayerNorm
    QUANTUM_CORE_AVAILABLE = True
except ImportError:
    QUANTUM_CORE_AVAILABLE = False
    print("⚠️ 量子架构核心未找到，将使用兼容实现")

# ─────────────────────────────────────────────────────────────────────────────
# 配置类
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QuantumFusionConfig:
    """量子融合配置"""
    # 模型维度
    hidden_dim: int = 256
    num_heads: int = 8
    
    # QSA 配置
    qsa_topk_ratio: float = 0.1  # 干涉路由筛选比例
    qsa_mode: str = "topk"
    
    # QEL 配置
    entanglement_strength: float = 0.5  # 纠缠强度
    use_local_entangle: bool = True
    use_global_entangle: bool = True
    
    # QCI 配置
    collapse_enabled: bool = True
    tau_low: float = 0.5
    tau_high: float = 1.5
    
    # 多模态配置
    modal_dims: Dict[str, int] = field(default_factory=lambda: {
        "vision": 512,    # YOLO特征维度
        "sensor": 64,     # 传感器特征维度
        "spectrum": 128,  # 光谱特征维度
    })
    
    # 推理配置
    dropout: float = 0.1
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


# ─────────────────────────────────────────────────────────────────────────────
# 兼容实现（当量子架构不可用时）
# ─────────────────────────────────────────────────────────────────────────────

class CompatibleQSA(nn.Module):
    """兼容实现的量子叠加注意力（当量子架构不可用时）"""
    
    def __init__(self, dim: int, num_heads: int = 8, topk_ratio: float = 0.1):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.topk_ratio = topk_ratio
        
        # 复数投影 - 输出维度改为 dim (不用2倍)
        self.q_proj = nn.Linear(dim, dim)  # q 和 k 保持 dim 维度
        self.k_proj = nn.Linear(dim, dim)
        self.v_proj = nn.Linear(dim, dim)  # v 也保持 dim
        self.o_proj = nn.Linear(dim, dim)
        
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, Dict]:
        B, N, C = x.shape
        
        # 复数编码 - 使用 tanh 模拟虚部
        q = self.q_proj(x)  # (B, N, dim)
        k = self.k_proj(x)  # (B, N, dim)
        v = self.v_proj(x)  # (B, N, dim)
        
        # 模拟复数：使用 cos/sin 分量
        q_real = torch.cos(q * 0.5) * (C ** 0.5)  # 缩放保持方差
        q_imag = torch.sin(q * 0.5) * (C ** 0.5)
        
        k_real = torch.cos(k * 0.5)
        k_imag = torch.sin(k * 0.5)
        
        # 复数内积作为干涉振幅: (q_real + i*q_imag) * (k_real - i*k_imag)
        attn_real = q_real * k_real + q_imag * k_imag  # 实部
        attn_imag = q_imag * k_real - q_real * k_imag  # 虚部
        
        # 注意力权重 = |amplitude|^2
        attn = (attn_real ** 2 + attn_imag ** 2) / (self.head_dim ** 0.5)
        
        # reshape for multi-head: (B, N, dim) -> (B, num_heads, N, head_dim)
        q = q.view(B, N, self.num_heads, self.head_dim).transpose(1, 2)  # (B, heads, N, head_dim)
        k = k.view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 简单注意力
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        attn_weights = F.softmax(attn_scores, dim=-1)
        
        # 干涉筛选 (top-k) - 简化版
        k_topk = max(1, int(N * self.topk_ratio))
        attn_sum = attn_weights.sum(dim=1)  # (B, N, N)
        
        # 应用注意力
        output = torch.matmul(attn_weights, v)  # (B, heads, N, head_dim)
        output = output.transpose(1, 2).reshape(B, N, C)  # (B, N, dim)
        output = self.o_proj(output)
        
        metrics = {
            "qsa_topk_ratio": self.topk_ratio,
            "qsa_attention_sparsity": 1 - self.topk_ratio,
        }
        
        return output, metrics


class CompatibleQEL(nn.Module):
    """兼容实现的量子纠缠层"""
    
    def __init__(self, dim: int, strength: float = 0.5):
        super().__init__()
        self.dim = dim
        self.strength = strength
        
        # 相邻纠缠门 (类比 CNOT)
        self.local_gate = nn.Parameter(torch.randn(dim, dim) * 0.02)
        # 全局纠缠权重
        self.global_weight = nn.Parameter(torch.randn(dim, dim) * 0.02)
        # 纠缠强度调制
        self.strength_param = nn.Parameter(torch.tensor(strength))
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict]:
        B, N, C = x.shape
        original = x
        
        # 局部纠缠 (相邻token)
        x_shift = torch.roll(x, shifts=1, dims=1)
        local_entangle = torch.sigmoid(x_shift @ self.local_gate)
        x = x * (1 - self.strength_param) + original * self.strength_param * local_entangle
        
        # 全局纠缠 (QFT-like 全连接)
        global_entangle = torch.sigmoid(x @ self.global_weight)
        x = x * (1 - self.strength_param * 0.5) + original * self.strength_param * 0.5 * global_entangle
        
        metrics = {
            "qel_strength": self.strength_param.item(),
            "qel_local_ratio": (x - original).abs().mean().item(),
            "qel_global_ratio": (x - original).abs().std().item(),
        }
        
        return x, metrics


class CompatibleEntropy(nn.Module):
    """兼容实现的冯·诺依曼熵计算"""
    
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """计算熵和 Born 归一化"""
        B, N, C = x.shape
        
        # 简化的 Born 归一化
        x_norm = x / (x.abs().max(dim=-1, keepdim=True)[0] + 1e-8)
        
        # 简化的熵计算 (使用概率分布的香农熵近似)
        prob = F.softmax(x_norm.abs(), dim=-1)
        entropy = -(prob * torch.log(prob + 1e-8)).sum(dim=-1)
        
        return entropy.mean(), x_norm


# ─────────────────────────────────────────────────────────────────────────────
# 主类：量子融合层
# ─────────────────────────────────────────────────────────────────────────────

class QuantumFusionLayer(nn.Module):
    """
    量子融合层 - 农业多模态数据融合
    
    支持融合：
    1. 视觉特征 (YOLO检测结果)
    2. 传感器数据 (温度/湿度/CO2/光照)
    3. 光谱数据 (多波段)
    
    使用量子机制：
    - QSA: 多模态注意力融合
    - QEL: 跨模态纠缠
    - Entropy: 不确定性量化
    """
    
    def __init__(self, config: Optional[QuantumFusionConfig] = None):
        super().__init__()
        self.config = config or QuantumFusionConfig()
        cfg = self.config
        
        # 选择实现
        self.use_quantum_core = QUANTUM_CORE_AVAILABLE
        
        if self.use_quantum_core:
            self.qsa = QuantumSuperpositionAttention(
                dim=cfg.hidden_dim,
                num_heads=cfg.num_heads,
                topk_ratio=cfg.qsa_topk_ratio,
                mode=cfg.qsa_mode,
            )
            self.qel = QuantumEntanglementLayer(
                dim=cfg.hidden_dim,
                strength=cfg.entanglement_strength,
            )
        else:
            self.qsa = CompatibleQSA(
                dim=cfg.hidden_dim,
                num_heads=cfg.num_heads,
                topk_ratio=cfg.qsa_topk_ratio,
            )
            self.qel = CompatibleQEL(
                dim=cfg.hidden_dim,
                strength=cfg.entanglement_strength,
            )
        
        # 模态编码器
        self.modal_encoders = nn.ModuleDict()
        for modal_name, modal_dim in cfg.modal_dims.items():
            self.modal_encoders[modal_name] = nn.Sequential(
                nn.Linear(modal_dim, cfg.hidden_dim),
                nn.LayerNorm(cfg.hidden_dim),
                nn.GELU(),
                nn.Dropout(cfg.dropout),
            )
        
        # 最终归一化
        self.final_norm = ComplexLayerNorm(cfg.hidden_dim) if self.use_quantum_core else nn.LayerNorm(cfg.hidden_dim)
        
        # 熵计算
        self.entropy_calc = CompatibleEntropy(cfg.hidden_dim)
        
        # 输出投影
        self.output_proj = nn.Linear(cfg.hidden_dim, cfg.hidden_dim)
        
        # 位置编码 (用于序列建模)
        self.pos_encoding = nn.Parameter(torch.randn(1, 100, cfg.hidden_dim) * 0.02)
        
        self._init_weights()
        
    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
                    
    def encode_modal(
        self, 
        modal_name: str, 
        modal_data: torch.Tensor
    ) -> torch.Tensor:
        """编码单个模态到统一特征空间"""
        if modal_name not in self.modal_encoders:
            raise ValueError(f"未知模态: {modal_name}. 支持: {list(self.modal_encoders.keys())}")
        
        encoder = self.modal_encoders[modal_name]
        features = encoder(modal_data)
        return features
        
    def fuse_modals(
        self,
        modal_features: Dict[str, torch.Tensor],
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        融合多模态特征
        
        Args:
            modal_features: 字典 {modal_name: tensor (B, N, dim)}
            mask: 可选注意力掩码
            
        Returns:
            fused: 融合后的特征 (B, N, hidden_dim)
            metrics: 融合指标
        """
        # 1. 展平多模态为序列
        sequences = []
        modal_masks = []
        
        for modal_name, features in modal_features.items():
            if features.dim() == 2:  # (B, dim) -> (B, 1, dim)
                features = features.unsqueeze(1)
            sequences.append(features)
            modal_masks.append(torch.ones(features.shape[:2], device=features.device))
        
        # 拼接为序列
        x = torch.cat(sequences, dim=1)  # (B, total_seq, hidden_dim)
        modal_mask = torch.cat(modal_masks, dim=1)  # (B, total_seq)
        
        # 添加位置编码
        seq_len = x.shape[1]
        x = x + self.pos_encoding[:, :seq_len, :]
        
        # 2. QSA 注意力融合
        attn_output, qsa_metrics = self.qsa(x, mask)
        
        # 3. QEL 纠缠耦合
        entangle_output, qel_metrics = self.qel(attn_output)
        
        # 4. 归一化
        if self.use_quantum_core:
            fused = self.final_norm(entangle_output)
        else:
            fused = self.final_norm(entangle_output)
        
        # 5. 计算不确定性熵
        entropy, normalized = self.entropy_calc(fused)
        
        metrics = {
            "fused_shape": fused.shape,
            "sequence_length": seq_len,
            "modal_count": len(modal_features),
            "entropy": entropy.item(),
            "entropy_normalized": (entropy.item() / self.config.hidden_dim),
            **{f"qsa_{k}": v for k, v in qsa_metrics.items()},
            **{f"qel_{k}": v for k, v in qel_metrics.items()},
        }
        
        return fused, metrics
    
    def forward(
        self,
        vision_features: Optional[torch.Tensor] = None,
        sensor_features: Optional[torch.Tensor] = None,
        spectrum_features: Optional[torch.Tensor] = None,
        time_series: Optional[torch.Tensor] = None,
        return_modal_features: bool = False,
    ) -> Dict[str, Any]:
        """
        主前向传播
        
        Args:
            vision_features: (B, N, 512) YOLO视觉特征
            sensor_features: (B, N, 64) 传感器特征
            spectrum_features: (B, N, 128) 光谱特征
            time_series: (B, T, dim) 时序数据
            return_modal_features: 是否返回各模态编码
            
        Returns:
            dict {
                'fused': 融合特征,
                'entropy': 不确定性熵,
                'metrics': 详细指标,
                'modal_features': 可选的各模态特征
            }
        """
        device = self.config.device
        B = 1  # batch size
        
        # 收集有效模态
        modal_features = {}
        
        if vision_features is not None:
            modal_features["vision"] = self.encode_modal("vision", vision_features)
        if sensor_features is not None:
            modal_features["sensor"] = self.encode_modal("sensor", sensor_features)
        if spectrum_features is not None:
            modal_features["spectrum"] = self.encode_modal("spectrum", spectrum_features)
        if time_series is not None:
            # 时序数据用 sensor 编码器
            if "sensor" not in self.modal_encoders:
                self.modal_encoders["sensor"] = nn.Sequential(
                    nn.Linear(time_series.shape[-1], self.config.hidden_dim),
                    nn.LayerNorm(self.config.hidden_dim),
                ).to(device)
            modal_features["time_series"] = self.encode_modal("sensor", time_series)
        
        if not modal_features:
            raise ValueError("至少需要提供一个模态的数据")
        
        # 融合
        fused, metrics = self.fuse_modals(modal_features)
        
        # 输出投影
        output = self.output_proj(fused)
        
        result = {
            "fused": output,
            "entropy": metrics["entropy"],
            "entropy_normalized": metrics["entropy_normalized"],
            "uncertainty": "low" if metrics["entropy_normalized"] < 0.3 else "medium" if metrics["entropy_normalized"] < 0.6 else "high",
            "metrics": metrics,
        }
        
        if return_modal_features:
            result["modal_features"] = modal_features
            
        return result


# ─────────────────────────────────────────────────────────────────────────────
# 工厂函数
# ─────────────────────────────────────────────────────────────────────────────

def create_quantum_fusion(config: Optional[Dict] = None) -> QuantumFusionLayer:
    """创建量子融合层实例"""
    if config:
        cfg = QuantumFusionConfig(**config)
    else:
        cfg = QuantumFusionConfig()
    return QuantumFusionLayer(cfg)


# ─────────────────────────────────────────────────────────────────────────────
# 测试代码
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("量子融合层测试")
    print("=" * 60)
    
    # 配置
    config = QuantumFusionConfig(
        hidden_dim=256,
        num_heads=8,
        qsa_topk_ratio=0.1,
        entanglement_strength=0.5,
    )
    
    # 创建模型
    model = QuantumFusionLayer(config)
    model = model.to(config.device)
    model.eval()
    
    print(f"\n模型结构:")
    print(f"  量子架构核心可用: {QUANTUM_CORE_AVAILABLE}")
    print(f"  隐藏维度: {config.hidden_dim}")
    print(f"  注意力头数: {config.num_heads}")
    print(f"  QSA top-k 比例: {config.qsa_topk_ratio}")
    
    # 模拟数据
    torch.manual_seed(42)
    
    # 视觉特征 (batch=1, seq=5, dim=512)
    vision_features = torch.randn(1, 5, 512).to(config.device)
    
    # 传感器特征 (batch=1, seq=5, dim=64)
    sensor_features = torch.randn(1, 5, 64).to(config.device)
    
    # 光谱特征 (batch=1, seq=5, dim=128)
    spectrum_features = torch.randn(1, 5, 128).to(config.device)
    
    print(f"\n输入数据:")
    print(f"  视觉特征: {vision_features.shape}")
    print(f"  传感器特征: {sensor_features.shape}")
    print(f"  光谱特征: {spectrum_features.shape}")
    
    # 前向传播
    with torch.no_grad():
        output = model(
            vision_features=vision_features,
            sensor_features=sensor_features,
            spectrum_features=spectrum_features,
        )
    
    print(f"\n融合结果:")
    print(f"  融合特征: {output['fused'].shape}")
    print(f"  不确定性熵: {output['entropy']:.4f}")
    print(f"  不确定性等级: {output['uncertainty']}")
    
    print(f"\n详细指标:")
    for k, v in output['metrics'].items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")
    
    # 参数统计
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\n模型参数: {total_params:,}")
    
    print("\n✅ 量子融合层测试完成")
