"""
量子路由器 (Quantum Interference Router - QIR)
==============================================
基于量子干涉原理的智能路由决策系统

核心功能：
1. QIR: 量子干涉路由 - 多路径干涉选择最优决策
2. 熔断保护 - 防止异常流量导致系统崩溃
3. 自适应路径选择 - 根据历史表现动态调整

农业场景：
- 多种农业决策路径选择（灌溉/施肥/用药/收获）
- 异常情况自动熔断
- 多模型协同路由
"""

import sys
import os
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import random
import math

import torch
import torch.nn as nn
import torch.nn.functional as F

# ─────────────────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────────────────

class RouteStrategy(Enum):
    """路由策略"""
    GREEDY = "greedy"           # 贪婪选择最优
    PROBABILISTIC = "prob"      # 概率采样
    ENSEMBLE = "ensemble"       # 集成多个路径
    ADAPTIVE = "adaptive"       # 自适应选择


@dataclass
class RouterPath:
    """路由路径定义"""
    name: str
    handler: Callable
    weight: float = 1.0
    success_count: int = 0
    failure_count: int = 0
    avg_latency: float = 0.0
    is_available: bool = True
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5
    
    @property
    def cost_score(self) -> float:
        """成本评分 (越低越好)"""
        return 1.0 / (self.avg_latency + 0.001)


@dataclass
class RouterConfig:
    """路由器配置"""
    strategy: RouteStrategy = RouteStrategy.ADAPTIVE
    max_retries: int = 3
    circuit_breaker_threshold: float = 0.3  # 成功率低于此值触发熔断
    circuit_breaker_timeout: int = 60        # 熔断恢复时间(秒)
    enable_interference: bool = True         # 启用干涉路由
    min_path_confidence: float = 0.3         # 最低置信度
    ensemble_top_k: int = 3                 # 集成选择前k个


@dataclass
class RouteResult:
    """路由结果"""
    path_name: str
    output: Any
    confidence: float
    latency: float
    entropy: float = 0.0
    is_fallback: bool = False
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 量子干涉路由器
# ─────────────────────────────────────────────────────────────────────────────

class QuantumInterferenceRouter:
    """
    量子干涉路由器
    
    原理：
    1. 将多个候选路径建模为量子态
    2. 通过干涉效应增强有利路径，消弱不利路径
    3. 最终坍缩为确定性的路径选择
    
    优势：
    - 自动平衡探索与利用
    - 不确定性量化
    - 异常自动熔断
    """
    
    def __init__(self, config: Optional[RouterConfig] = None):
        self.config = config or RouterConfig()
        self.paths: Dict[str, RouterPath] = {}
        self.path_history: List[Dict] = []
        self.circuit_breakers: Dict[str, float] = {}  # path_name -> breaker_timeout
        
    def register_path(self, name: str, handler: Callable, initial_weight: float = 1.0):
        """注册路由路径"""
        self.paths[name] = RouterPath(
            name=name,
            handler=handler,
            weight=initial_weight,
        )
        
    def unregister_path(self, name: str):
        """注销路由路径"""
        if name in self.paths:
            del self.paths[name]
            
    def update_path_stats(self, name: str, success: bool, latency: float):
        """更新路径统计"""
        if name not in self.paths:
            return
            
        path = self.paths[name]
        total = path.success_count + path.failure_count + 1
        
        # 指数滑动平均更新
        path.avg_latency = (path.avg_latency * total + latency) / (total + 1)
        
        if success:
            path.success_count += 1
        else:
            path.failure_count += 1
            
        # 检查是否需要熔断
        if path.success_rate < self.config.circuit_breaker_threshold:
            self._trip_circuit_breaker(name)
            
    def _trip_circuit_breaker(self, name: str):
        """触发熔断"""
        if name in self.paths:
            self.paths[name].is_available = False
            self.circuit_breakers[name] = time.time() + self.config.circuit_breaker_timeout
            print(f"⚡ 熔断器触发: {name}")
            
    def _check_circuit_breaker(self, name: str) -> bool:
        """检查熔断器状态"""
        if name not in self.circuit_breakers:
            return True
            
        if time.time() > self.circuit_breakers[name]:
            # 熔断超时，恢复
            if name in self.paths:
                self.paths[name].is_available = True
            del self.circuit_breakers[name]
            print(f"🔄 熔断恢复: {name}")
            return True
            
        return False
    
    def _compute_interference(self, query_embedding: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        计算量子干涉振幅
        
        核心思想：
        - 每个路径有一个"本征态"向量
        - 查询向量与路径向量的内积作为干涉振幅
        - 相长干涉增强概率，相消干涉减弱概率
        """
        device = query_embedding.device
        
        # 为每个路径生成/更新本征态
        path_names = list(self.paths.keys())
        num_paths = len(path_names)
        
        if num_paths == 0:
            return {}
            
        # 使用路径统计构建本征态
        eigenstates = []
        for name in path_names:
            path = self.paths[name]
            
            # 本征态 = [成功率, 速度评分, 权重, 可用性]
            state = torch.tensor([
                path.success_rate,
                min(path.cost_score / 10, 1.0),  # 归一化
                path.weight / (sum(p.weight for p in self.paths.values()) + 1e-8),
                1.0 if path.is_available else 0.0,
            ], dtype=torch.float32, device=device)
            eigenstates.append(state)
        
        # 构建路径态矩阵 (num_paths, 4)
        path_states = torch.stack(eigenstates)  # (num_paths, feature_dim)
        
        # 归一化为量子态
        path_states = path_states / (path_states.norm(dim=-1, keepdim=True) + 1e-8)
        
        # 查询向量 (扩展到相同维度并确保2D)
        if query_embedding.dim() == 1:
            query_expanded = query_embedding.unsqueeze(0)  # (1, feature_dim)
        else:
            query_expanded = query_embedding
        
        # 计算干涉振幅 (复数内积)
        # 振幅 = Re(<query|path>) + i * Im(<query|path>)
        real_part = torch.mm(query_expanded, path_states.T).squeeze(0)  # 确保1D
        
        # 干涉增强: 根据成功率和可用性调整
        availability = torch.tensor([
            1.0 if self.paths[name].is_available else 0.0 
            for name in path_names
        ], device=device)
        
        interference_amplitude = real_part * availability
        
        # 计算概率分布
        probabilities = F.softmax(interference_amplitude, dim=0)
        
        return {name: prob.item() for name, prob in zip(path_names, probabilities)}
    
    def _compute_von_neumann_entropy(self, probabilities: torch.Tensor) -> float:
        """计算概率分布的熵 (对应量子态的冯·诺依曼熵)"""
        # 添加小量避免 log(0)
        p = probabilities + 1e-10
        entropy = -(p * torch.log(p)).sum().item()
        # 归一化
        max_entropy = math.log(len(p) + 1e-8)
        return entropy / (max_entropy + 1e-8)
    
    def route(
        self, 
        query: Any,
        query_context: Optional[Dict] = None,
    ) -> RouteResult:
        """
        执行路由选择
        
        Args:
            query: 查询输入
            query_context: 查询上下文 (用于生成嵌入)
            num_results: 返回结果数量
            
        Returns:
            RouteResult 或 List[RouteResult]
        """
        if not self.paths:
            raise ValueError("没有注册任何路由路径")
            
        # 检查可用的路径
        available_paths = {
            name: path for name, path in self.paths.items()
            if path.is_available and self._check_circuit_breaker(name)
        }
        
        if not available_paths:
            raise RuntimeError("所有路径均不可用或熔断中")
        
        # 生成查询嵌入
        if isinstance(query, str):
            # 简单的词袋嵌入
            query_embedding = torch.rand(4)  # 简化实现
        elif isinstance(query, torch.Tensor):
            query_embedding = query.flatten()[:4]
        else:
            query_embedding = torch.rand(4)
            
        query_embedding = query_embedding / (query_embedding.norm() + 1e-8)
        
        # 策略选择
        if self.config.strategy == RouteStrategy.GREEDY:
            return self._route_greedy(query, query_embedding, available_paths)
        elif self.config.strategy == RouteStrategy.PROBABILISTIC:
            return self._route_probabilistic(query, query_embedding, available_paths)
        elif self.config.strategy == RouteStrategy.ENSEMBLE:
            return self._route_ensemble(query, query_embedding, available_paths)
        else:  # ADAPTIVE
            return self._route_adaptive(query, query_embedding, available_paths)
    
    def _route_greedy(
        self, 
        query: Any, 
        query_embedding: torch.Tensor,
        available_paths: Dict[str, RouterPath]
    ) -> RouteResult:
        """贪婪选择最优路径"""
        probabilities = self._compute_interference(query_embedding)
        
        # 选择概率最高的路径
        best_path_name = max(probabilities, key=probabilities.get)
        path = self.paths[best_path_name]
        
        # 执行
        start_time = time.time()
        try:
            output = path.handler(query)
            latency = time.time() - start_time
            self.update_path_stats(best_path_name, success=True, latency=latency)
            
            return RouteResult(
                path_name=best_path_name,
                output=output,
                confidence=probabilities[best_path_name],
                latency=latency,
                entropy=self._compute_von_neumann_entropy(
                    torch.tensor(list(probabilities.values()))
                ),
            )
        except Exception as e:
            latency = time.time() - start_time
            self.update_path_stats(best_path_name, success=False, latency=latency)
            
            return RouteResult(
                path_name=best_path_name,
                output=None,
                confidence=0.0,
                latency=latency,
                error=str(e),
                is_fallback=True,
            )
    
    def _route_probabilistic(
        self, 
        query: Any, 
        query_embedding: torch.Tensor,
        available_paths: Dict[str, RouterPath]
    ) -> RouteResult:
        """概率采样选择"""
        probabilities = self._compute_interference(query_embedding)
        prob_tensor = torch.tensor(list(probabilities.values()))
        
        # 采样
        idx = torch.multinomial(prob_tensor, 1).item()
        path_name = list(probabilities.keys())[idx]
        path = self.paths[path_name]
        
        # 执行
        start_time = time.time()
        try:
            output = path.handler(query)
            latency = time.time() - start_time
            self.update_path_stats(path_name, success=True, latency=latency)
            
            return RouteResult(
                path_name=path_name,
                output=output,
                confidence=probabilities[path_name],
                latency=latency,
                entropy=self._compute_von_neumann_entropy(prob_tensor),
            )
        except Exception as e:
            latency = time.time() - start_time
            self.update_path_stats(path_name, success=False, latency=latency)
            
            return RouteResult(
                path_name=path_name,
                output=None,
                confidence=0.0,
                latency=latency,
                error=str(e),
                is_fallback=True,
            )
    
    def _route_ensemble(
        self, 
        query: Any, 
        query_embedding: torch.Tensor,
        available_paths: Dict[str, RouterPath]
    ) -> RouteResult:
        """集成多个路径 (返回加权结果)"""
        probabilities = self._compute_interference(query_embedding)
        prob_tensor = torch.tensor(list(probabilities.values()))
        
        # 选择前k个
        k = min(self.config.ensemble_top_k, len(probabilities))
        topk_values, topk_indices = torch.topk(prob_tensor, k)
        topk_paths = [list(probabilities.keys())[i] for i in topk_indices.tolist()]
        
        # 加权集成执行
        results = []
        total_weight = topk_values.sum().item()
        
        for i, path_name in enumerate(topk_paths):
            path = self.paths[path_name]
            weight = (topk_values[i] / total_weight).item()
            
            start_time = time.time()
            try:
                output = path.handler(query)
                latency = time.time() - start_time
                self.update_path_stats(path_name, success=True, latency=latency)
                
                results.append({
                    "path": path_name,
                    "output": output,
                    "weight": weight,
                    "confidence": probabilities[path_name],
                    "latency": latency,
                })
            except Exception as e:
                latency = time.time() - start_time
                self.update_path_stats(path_name, success=False, latency=latency)
                
                results.append({
                    "path": path_name,
                    "output": None,
                    "weight": weight,
                    "confidence": 0.0,
                    "latency": latency,
                    "error": str(e),
                })
        
        # 返回第一个成功的结果作为主输出
        successful = [r for r in results if r["output"] is not None]
        if successful:
            primary = successful[0]
            return RouteResult(
                path_name=primary["path"],
                output=primary["output"],
                confidence=primary["confidence"],
                latency=primary["latency"],
                entropy=self._compute_von_neumann_entropy(prob_tensor),
            )
        else:
            return RouteResult(
                path_name="ensemble",
                output=results,
                confidence=0.0,
                latency=0.0,
                entropy=self._compute_von_neumann_entropy(prob_tensor),
                is_fallback=True,
                error="All ensemble paths failed",
            )
    
    def _route_adaptive(
        self, 
        query: Any, 
        query_embedding: torch.Tensor,
        available_paths: Dict[str, RouterPath]
    ) -> RouteResult:
        """自适应路由 - 根据情况选择最佳策略"""
        probabilities = self._compute_interference(query_embedding)
        prob_tensor = torch.tensor(list(probabilities.values()))
        entropy = self._compute_von_neumann_entropy(prob_tensor)
        
        # 高熵 = 不确定，使用集成
        # 低熵 = 确信，使用贪婪
        if entropy > 0.7:
            return self._route_ensemble(query, query_embedding, available_paths)
        else:
            return self._route_greedy(query, query_embedding, available_paths)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取路由器统计信息"""
        return {
            "total_paths": len(self.paths),
            "available_paths": sum(1 for p in self.paths.values() if p.is_available),
            "circuit_breakers": list(self.circuit_breakers.keys()),
            "paths_detail": {
                name: {
                    "success_rate": path.success_rate,
                    "avg_latency": path.avg_latency,
                    "is_available": path.is_available,
                }
                for name, path in self.paths.items()
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# 农业决策路由示例
# ─────────────────────────────────────────────────────────────────────────────

def create_agriculture_router() -> QuantumInterferenceRouter:
    """创建农业决策路由器"""
    config = RouterConfig(
        strategy=RouteStrategy.ADAPTIVE,
        circuit_breaker_threshold=0.3,
        ensemble_top_k=2,
    )
    router = QuantumInterferenceRouter(config)
    
    # 注册农业决策路径
    router.register_path("expert_llm", lambda x: {"decision": "expert_analysis", "confidence": 0.9})
    router.register_path("fast_rule", lambda x: {"decision": "rule_based", "confidence": 0.7})
    router.register_path("hybrid", lambda x: {"decision": "hybrid_approach", "confidence": 0.85})
    
    return router


# ─────────────────────────────────────────────────────────────────────────────
# 测试代码
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("量子干涉路由器测试")
    print("=" * 60)
    
    # 创建路由器
    router = create_agriculture_router()
    
    print(f"\n路由器配置:")
    print(f"  策略: {router.config.strategy.value}")
    print(f"  熔断阈值: {router.config.circuit_breaker_threshold}")
    print(f"  注册路径: {list(router.paths.keys())}")
    
    # 测试路由
    test_queries = [
        "番茄叶片发黄是什么原因？",
        "灌溉建议",
        "温室温度调控",
    ]
    
    print(f"\n路由测试:")
    for query in test_queries:
        result = router.route(query)
        print(f"\n  查询: {query}")
        print(f"  路径: {result.path_name}")
        print(f"  置信度: {result.confidence:.3f}")
        print(f"  熵: {result.entropy:.3f}")
        print(f"  延迟: {result.latency*1000:.2f}ms")
        if result.output:
            print(f"  输出: {result.output}")
    
    # 模拟失败触发熔断
    print(f"\n模拟熔断测试:")
    for i in range(5):
        router.paths["fast_rule"].failure_count += 1
        
    router.update_path_stats("fast_rule", success=False, latency=0.1)
    
    if not router.paths["fast_rule"].is_available:
        print(f"  ✅ 熔断器已触发: fast_rule")
    
    # 统计信息
    print(f"\n路由器统计:")
    stats = router.get_stats()
    print(f"  可用路径: {stats['available_paths']}/{stats['total_paths']}")
    for name, detail in stats['paths_detail'].items():
        print(f"    {name}: 成功率={detail['success_rate']:.2f}, 延迟={detail['avg_latency']*1000:.2f}ms")
    
    print("\n✅ 量子路由器测试完成")
