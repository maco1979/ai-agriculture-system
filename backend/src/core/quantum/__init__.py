"""
量子架构模块 (Quantum Architecture Module)
==========================================

整合量子架构与AI农业系统的核心模块。

主要组件：
- QuantumFusionLayer: 量子多模态融合层
- QuantumDecisionEngine: 量子决策引擎
- QuantumInterferenceRouter: 量子干涉路由器
- QuantumOptimizer: 量子梯度下降优化器
- AgricultureQuantumService: 农业量子服务

使用示例：

    from src.core.quantum import get_quantum_service
    
    # 获取服务
    service = get_quantum_service()
    
    # 多模态融合
    result = service.fuse_multimodal(
        vision_features=vision,
        sensor_features=sensor,
    )
    
    # 病害诊断
    diagnosis = service.diagnose_disease(features)
    
    # 智能路由
    route = service.route_decision(query)

文档：
- QUANTUM_INTEGRATION_PLAN.md: 整合方案设计
"""

# 版本信息
__version__ = "1.0.0"

# 核心组件
from .fusion_layer import (
    QuantumFusionLayer,
    QuantumFusionConfig,
    create_quantum_fusion,
)

from .decision_engine import (
    QuantumDecisionEngine,
    QuantumCollapseInference,
    QCIConfig,
    DecisionResult,
    DecisionType,
    create_agriculture_disease_engine,
)

from .quantum_router import (
    QuantumInterferenceRouter,
    RouterConfig,
    RouterPath,
    RouteResult,
    RouteStrategy,
    create_agriculture_router,
)

from .quantum_optimizer import (
    QuantumGradientDescent,
    QGDConfig,
    QGDLinear,
    UnitaryParameter,
    create_quantum_optimizer,
)

from .agriculture_adapter import (
    AgricultureQuantumService,
    AgricultureQuantumConfig,
    get_quantum_service,
)

# ─────────────────────────────────────────────────────────────────────────────
# 快速访问
# ─────────────────────────────────────────────────────────────────────────────

def create_service(config=None):
    """创建农业量子服务（快捷函数）"""
    return AgricultureQuantumService(config)

def create_fusion_layer(**kwargs):
    """创建量子融合层（快捷函数）"""
    config = QuantumFusionConfig(**kwargs)
    return QuantumFusionLayer(config)

def create_decision_engine(**kwargs):
    """创建决策引擎（快捷函数）"""
    engine, classes = create_agriculture_disease_engine()
    return engine, classes

def create_optimizer(model, **kwargs):
    """创建量子优化器（快捷函数）"""
    config = QGDConfig(**kwargs)
    return QuantumGradientDescent(model.parameters(), config)


# ─────────────────────────────────────────────────────────────────────────────
# 模块信息
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    # 版本
    "__version__",
    
    # 配置类
    "QuantumFusionConfig",
    "QCIConfig",
    "RouterConfig",
    "QGDConfig",
    "AgricultureQuantumConfig",
    
    # 核心类
    "QuantumFusionLayer",
    "QuantumDecisionEngine",
    "QuantumCollapseInference",
    "QuantumInterferenceRouter",
    "QuantumGradientDescent",
    "QGDLinear",
    "UnitaryParameter",
    "AgricultureQuantumService",
    
    # 数据类
    "DecisionResult",
    "RouteResult",
    "RouterPath",
    
    # 枚举
    "DecisionType",
    "RouteStrategy",
    
    # 工厂函数
    "get_quantum_service",
    "create_service",
    "create_quantum_fusion",
    "create_fusion_layer",
    "create_agriculture_disease_engine",
    "create_agriculture_router",
    "create_quantum_optimizer",
    "create_optimizer",
]
