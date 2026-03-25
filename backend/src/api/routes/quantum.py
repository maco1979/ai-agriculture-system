"""
量子服务 API 路由
==================
提供量子架构能力的 HTTP 接口

端点：
- POST /api/quantum/fuse - 多模态融合
- POST /api/quantum/diagnose - 病害诊断
- POST /api/quantum/route - 智能路由
- GET /api/quantum/info - 系统信息
- GET /api/quantum/stats - 路由器统计
"""

import sys
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

import torch

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from src.core.quantum import (
        get_quantum_service,
        AgricultureQuantumService,
        DecisionResult,
        RouteResult,
    )
    QUANTUM_AVAILABLE = True
except ImportError as e:
    QUANTUM_AVAILABLE = False
    print(f"⚠️ 量子模块导入失败: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 请求/响应模型
# ─────────────────────────────────────────────────────────────────────────────

class FusionRequest(BaseModel):
    """多模态融合请求"""
    vision_features: Optional[List[List[float]]] = Field(None, description="视觉特征 (N, 512)")
    sensor_features: Optional[List[List[float]]] = Field(None, description="传感器特征 (N, 64)")
    spectrum_features: Optional[List[List[float]]] = Field(None, description="光谱特征 (N, 128)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "vision_features": [[0.1] * 512 for _ in range(5)],
                "sensor_features": [[0.5] * 64 for _ in range(5)],
            }
        }


class FusionResponse(BaseModel):
    """多模态融合响应"""
    success: bool
    fused_shape: List[int]
    entropy: float
    uncertainty: str
    processing_time_ms: float
    metrics: Dict[str, Any]


class DiagnoseRequest(BaseModel):
    """病害诊断请求"""
    features: List[float] = Field(..., description="视觉特征 (512,)")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文")
    
    class Config:
        json_schema_extra = {
            "example": {
                "features": [0.1] * 512,
                "context": {"crop_type": "番茄", "growth_day": 45}
            }
        }


class DiagnoseResponse(BaseModel):
    """病害诊断响应"""
    success: bool
    decision: str
    confidence: float
    entropy: float
    uncertainty_level: str
    early_exit_layer: Optional[int]
    probability_distribution: Optional[Dict[str, float]]
    processing_time_ms: float


class RouteRequest(BaseModel):
    """路由请求"""
    query: str = Field(..., description="查询内容")
    strategy: Optional[str] = Field("adaptive", description="路由策略: greedy/probabilistic/ensemble/adaptive")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "番茄叶片发黄是什么原因？",
                "strategy": "adaptive"
            }
        }


class RouteResponse(BaseModel):
    """路由响应"""
    success: bool
    path_name: str
    confidence: float
    entropy: float
    latency_ms: float
    output: Optional[Dict[str, Any]]
    is_fallback: bool
    error: Optional[str]


class SystemInfoResponse(BaseModel):
    """系统信息响应"""
    device: str
    version: str
    components: Dict[str, Any]
    total_params: int
    quantum_core_available: bool


class RouterStatsResponse(BaseModel):
    """路由器统计响应"""
    total_paths: int
    available_paths: int
    circuit_breakers: List[str]
    paths_detail: Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# 路由器
# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/quantum", tags=["量子服务"])


def get_service() -> AgricultureQuantumService:
    """获取量子服务实例"""
    if not QUANTUM_AVAILABLE:
        raise HTTPException(status_code=503, detail="量子模块不可用")
    return get_quantum_service()


# ─────────────────────────────────────────────────────────────────────────────
# 端点
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/fuse", response_model=FusionResponse)
async def fuse_multimodal(request: FusionRequest, service: AgricultureQuantumService = Depends(get_service)):
    """
    多模态特征融合
    
    融合视觉、传感器、光谱等多种数据源的特征。
    使用量子叠加注意力 (QSA) 和量子纠缠层 (QEL) 实现高效融合。
    """
    start_time = datetime.now()
    
    try:
        # 转换输入
        vision = None
        sensor = None
        spectrum = None
        
        if request.vision_features:
            vision = torch.tensor(request.vision_features, dtype=torch.float32)
        if request.sensor_features:
            sensor = torch.tensor(request.sensor_features, dtype=torch.float32)
        if request.spectrum_features:
            spectrum = torch.tensor(request.spectrum_features, dtype=torch.float32)
        
        # 融合
        result = service.fuse_multimodal(
            vision_features=vision,
            sensor_features=sensor,
            spectrum_features=spectrum,
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return FusionResponse(
            success=True,
            fused_shape=list(result["fused_features_shape"]),
            entropy=float(result["entropy"]),
            uncertainty=result["uncertainty"],
            processing_time_ms=processing_time,
            metrics=result["metrics"],
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"融合失败: {str(e)}")


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose_disease(request: DiagnoseRequest, service: AgricultureQuantumService = Depends(get_service)):
    """
    病害诊断
    
    使用量子决策引擎进行病害诊断。
    返回诊断结果、置信度和不确定性量化。
    """
    start_time = datetime.now()
    
    try:
        # 转换输入
        features = torch.tensor(request.features, dtype=torch.float32).unsqueeze(0)
        
        # 诊断
        result = service.diagnose_disease(features, request.context)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # 提取概率分布
        prob_dist = None
        if result.superposition_probs is not None:
            probs = result.superposition_probs.cpu().numpy()
            prob_dist = {
                service.disease_classes[i]: float(probs[i])
                for i in range(len(probs))
            }
        
        return DiagnoseResponse(
            success=True,
            decision=str(result.decision),
            confidence=float(result.confidence),
            entropy=float(result.entropy),
            uncertainty_level=result.uncertainty_level,
            early_exit_layer=result.early_exit_layer,
            probability_distribution=prob_dist,
            processing_time_ms=processing_time,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")


@router.post("/route", response_model=RouteResponse)
async def route_decision(request: RouteRequest, service: AgricultureQuantumService = Depends(get_service)):
    """
    智能路由决策
    
    使用量子干涉路由器选择最优决策路径。
    支持多种路由策略。
    """
    try:
        result = service.route_decision(request.query, request.strategy)
        
        return RouteResponse(
            success=result.error is None,
            path_name=result.path_name,
            confidence=float(result.confidence),
            entropy=float(result.entropy),
            latency_ms=result.latency * 1000,
            output=result.output if isinstance(result.output, dict) else None,
            is_fallback=result.is_fallback,
            error=result.error,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"路由失败: {str(e)}")


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info(service: AgricultureQuantumService = Depends(get_service)):
    """获取系统信息"""
    try:
        info = service.get_system_info()
        info["quantum_core_available"] = QUANTUM_AVAILABLE
        info["version"] = "1.0.0"
        return SystemInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取信息失败: {str(e)}")


@router.get("/stats", response_model=RouterStatsResponse)
async def get_router_stats(service: AgricultureQuantumService = Depends(get_service)):
    """获取路由器统计"""
    try:
        stats = service.get_router_stats()
        return RouterStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "quantum_available": QUANTUM_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 注册到主应用
# ─────────────────────────────────────────────────────────────────────────────

def register_quantum_routes(app):
    """注册量子服务路由到 FastAPI 应用"""
    app.include_router(router)
    return router
