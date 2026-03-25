"""
农业量子服务 (Agriculture Quantum Service)
=========================================
整合量子架构与AI农业系统的服务层

提供统一的接口封装：
1. 量子多模态融合
2. 量子决策引擎
3. 量子路由器
"""

import sys
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
import time

import torch
import torch.nn as nn

# 导入量子组件
from .fusion_layer import QuantumFusionLayer, QuantumFusionConfig
from .decision_engine import QuantumDecisionEngine, QCIConfig, DecisionType, DecisionResult, create_agriculture_disease_engine
from .quantum_router import QuantumInterferenceRouter, RouterConfig, RouteStrategy, RouteResult, create_agriculture_router

# ─────────────────────────────────────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgricultureQuantumConfig:
    """农业量子服务配置"""
    # 融合层配置
    fusion_hidden_dim: int = 256
    fusion_num_heads: int = 8
    qsa_topk_ratio: float = 0.1
    
    # 决策引擎配置
    decision_hidden_dim: int = 256
    decision_num_layers: int = 4
    collapse_threshold_low: float = 0.3
    collapse_threshold_high: float = 1.0
    
    # 路由器配置
    router_strategy: str = "adaptive"
    circuit_breaker_threshold: float = 0.3
    
    # 设备
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    # 缓存
    enable_cache: bool = True
    cache_ttl: int = 300  # 缓存有效期(秒)


# ─────────────────────────────────────────────────────────────────────────────
# 服务类
# ─────────────────────────────────────────────────────────────────────────────

class AgricultureQuantumService:
    """
    农业量子服务
    
    整合量子融合、量子决策、量子路由三大能力。
    提供简洁的API用于农业场景的智能决策。
    """
    
    def __init__(self, config: Optional[AgricultureQuantumConfig] = None):
        self.config = config or AgricultureQuantumConfig()
        cfg = self.config
        
        self.device = torch.device(cfg.device)
        
        # 初始化组件
        self._init_fusion()
        self._init_decision_engine()
        self._init_router()
        
        # 缓存
        self._cache: Dict[str, Tuple[Any, float]] = {}
        
        print(f"🌾 农业量子服务初始化完成")
        print(f"   设备: {self.device}")
        print(f"   融合维度: {cfg.fusion_hidden_dim}")
        print(f"   决策层数: {cfg.decision_num_layers}")
    
    def _init_fusion(self):
        """初始化量子融合层"""
        fusion_config = QuantumFusionConfig(
            hidden_dim=self.config.fusion_hidden_dim,
            num_heads=self.config.fusion_num_heads,
            qsa_topk_ratio=self.config.qsa_topk_ratio,
            device=self.config.device,
        )
        self.fusion_layer = QuantumFusionLayer(fusion_config)
        self.fusion_layer = self.fusion_layer.to(self.device)
        self.fusion_layer.eval()
    
    def _init_decision_engine(self):
        """初始化决策引擎"""
        disease_classes = [
            "healthy",              # 健康
            "leaf_spot",            # 叶斑病
            "powdery_mildew",       # 白粉病
            "blight",               # 枯萎病
            "root_rot",             # 根腐病
            "bacterial_infection",  # 细菌感染
            "viral_infection",     # 病毒感染
            "nutrient_deficiency",  # 营养缺乏
            "water_stress",         # 水分胁迫
            "pest_damage",          # 虫害
        ]
        
        qci_config = QCIConfig(
            tau_low=self.config.collapse_threshold_low,
            tau_high=self.config.collapse_threshold_high,
            enable_early_exit=True,
            decision_type=DecisionType.CLASSIFICATION,
            top_k=3,
        )
        
        self.decision_engine = QuantumDecisionEngine(
            input_dim=512,
            num_classes=len(disease_classes),
            hidden_dim=self.config.decision_hidden_dim,
            num_layers=self.config.decision_num_layers,
            config=qci_config,
        )
        self.decision_engine = self.decision_engine.to(self.device)
        self.decision_engine.eval()
        
        self.disease_classes = disease_classes
    
    def _init_router(self):
        """初始化路由器"""
        strategy_map = {
            "greedy": RouteStrategy.GREEDY,
            "probabilistic": RouteStrategy.PROBABILISTIC,
            "ensemble": RouteStrategy.ENSEMBLE,
            "adaptive": RouteStrategy.ADAPTIVE,
        }
        
        router_config = RouterConfig(
            strategy=strategy_map.get(self.config.router_strategy, RouteStrategy.ADAPTIVE),
            circuit_breaker_threshold=self.config.circuit_breaker_threshold,
        )
        
        self.router = QuantumInterferenceRouter(router_config)
        
        # 注册农业决策路径
        self.router.register_path("quantum_decision", self._quantum_decision_handler)
        self.router.register_path("fast_rule", self._fast_rule_handler)
        self.router.register_path("expert_llm", self._expert_llm_handler)
    
    # ── 处理器 ──
    
    def _quantum_decision_handler(self, query: Dict) -> Dict:
        """量子决策处理器"""
        features = torch.randn(1, 512).to(self.device)
        with torch.no_grad():
            result = self.decision_engine(features, self.disease_classes)
        return result.to_dict()
    
    def _fast_rule_handler(self, query: Dict) -> Dict:
        """快速规则处理器"""
        return {
            "decision": "rule_based",
            "confidence": 0.7,
            "response_time_ms": 5,
        }
    
    def _expert_llm_handler(self, query: Dict) -> Dict:
        """专家LLM处理器"""
        return {
            "decision": "llm_analysis",
            "confidence": 0.85,
            "response_time_ms": 500,
        }
    
    # ── 公开 API ──
    
    def fuse_multimodal(
        self,
        vision_features: Optional[torch.Tensor] = None,
        sensor_features: Optional[torch.Tensor] = None,
        spectrum_features: Optional[torch.Tensor] = None,
    ) -> Dict[str, Any]:
        """
        多模态特征融合
        
        Args:
            vision_features: 视觉特征 (B, N, 512)
            sensor_features: 传感器特征 (B, N, 64)
            spectrum_features: 光谱特征 (B, N, 128)
            
        Returns:
            融合结果字典
        """
        with torch.no_grad():
            result = self.fusion_layer(
                vision_features=vision_features,
                sensor_features=sensor_features,
                spectrum_features=spectrum_features,
            )
        
        return {
            "fused_features_shape": result["fused"].shape,
            "entropy": float(result["entropy"]),
            "entropy_normalized": float(result["entropy_normalized"]),
            "uncertainty": result["uncertainty"],
            "metrics": {k: float(v) if isinstance(v, (int, float)) else str(v) 
                       for k, v in result["metrics"].items()},
        }
    
    def diagnose_disease(
        self,
        features: torch.Tensor,
        context: Optional[Dict] = None,
    ) -> DecisionResult:
        """
        病害诊断决策
        
        Args:
            features: 视觉特征 (B, 512)
            context: 额外上下文
            
        Returns:
            DecisionResult
        """
        if features.dim() == 2 and features.shape[0] == 1:
            features = features[0]
        
        with torch.no_grad():
            result = self.decision_engine(features, self.disease_classes)
        
        return result
    
    def route_decision(
        self,
        query: Any,
        strategy: Optional[str] = None,
    ) -> RouteResult:
        """
        智能路由决策
        
        Args:
            query: 查询
            strategy: 路由策略 (overrides config)
            
        Returns:
            RouteResult
        """
        if strategy:
            strategy_map = {
                "greedy": RouteStrategy.GREEDY,
                "probabilistic": RouteStrategy.PROBABILISTIC,
                "ensemble": RouteStrategy.ENSEMBLE,
                "adaptive": RouteStrategy.ADAPTIVE,
            }
            self.router.config.strategy = strategy_map.get(strategy, RouteStrategy.ADAPTIVE)
        
        return self.router.route(query)
    
    def get_router_stats(self) -> Dict:
        """获取路由器统计"""
        return self.router.get_stats()
    
    def get_system_info(self) -> Dict:
        """获取系统信息"""
        fusion_params = sum(p.numel() for p in self.fusion_layer.parameters())
        decision_params = sum(p.numel() for p in self.decision_engine.parameters())
        
        return {
            "device": str(self.device),
            "components": {
                "fusion_layer": {
                    "params": fusion_params,
                    "hidden_dim": self.config.fusion_hidden_dim,
                    "num_heads": self.config.fusion_num_heads,
                },
                "decision_engine": {
                    "params": decision_params,
                    "hidden_dim": self.config.decision_hidden_dim,
                    "num_layers": self.config.decision_num_layers,
                    "num_classes": len(self.disease_classes),
                },
                "router": {
                    "strategy": self.router.config.strategy.value,
                    "num_paths": len(self.router.paths),
                },
            },
            "total_params": fusion_params + decision_params,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 单例
# ─────────────────────────────────────────────────────────────────────────────

_service_instance: Optional[AgricultureQuantumService] = None


def get_quantum_service(config: Optional[AgricultureQuantumConfig] = None) -> AgricultureQuantumService:
    """获取全局量子服务实例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = AgricultureQuantumService(config)
    return _service_instance


# ─────────────────────────────────────────────────────────────────────────────
# 测试
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("农业量子服务测试")
    print("=" * 60)
    
    # 创建服务
    config = AgricultureQuantumConfig(
        fusion_hidden_dim=256,
        decision_num_layers=4,
        router_strategy="adaptive",
    )
    
    service = AgricultureQuantumService(config)
    
    # 系统信息
    print(f"\n系统信息:")
    info = service.get_system_info()
    print(f"  设备: {info['device']}")
    print(f"  总参数: {info['total_params']:,}")
    
    # 多模态融合测试
    print(f"\n多模态融合测试:")
    vision = torch.randn(1, 5, 512).to(service.device)
    sensor = torch.randn(1, 5, 64).to(service.device)
    spectrum = torch.randn(1, 5, 128).to(service.device)
    
    fusion_result = service.fuse_multimodal(
        vision_features=vision,
        sensor_features=sensor,
        spectrum_features=spectrum,
    )
    
    print(f"  融合特征: {fusion_result['fused_features_shape']}")
    print(f"  熵: {fusion_result['entropy']:.4f}")
    print(f"  不确定性: {fusion_result['uncertainty']}")
    
    # 病害诊断测试
    print(f"\n病害诊断测试:")
    features = torch.randn(1, 512).to(service.device)
    diagnosis = service.diagnose_disease(features)
    
    print(f"  决策: {diagnosis.decision}")
    print(f"  置信度: {diagnosis.confidence:.3f}")
    print(f"  熵: {diagnosis.entropy:.4f}")
    print(f"  不确定性: {diagnosis.uncertainty_level}")
    
    # 路由测试
    print(f"\n路由测试:")
    query = "番茄叶片发黄应该怎么处理？"
    route_result = service.route_decision(query)
    
    print(f"  路径: {route_result.path_name}")
    print(f"  置信度: {route_result.confidence:.3f}")
    print(f"  熵: {route_result.entropy:.3f}")
    print(f"  延迟: {route_result.latency*1000:.2f}ms")
    
    # 路由器统计
    print(f"\n路由器统计:")
    stats = service.get_router_stats()
    print(f"  可用路径: {stats['available_paths']}/{stats['total_paths']}")
    
    print("\n✅ 农业量子服务测试完成")
