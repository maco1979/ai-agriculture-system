"""
Fine-Tune 路由 — /api/v1/fine-tune
提供通过 HTTP 调用 OrganicAICore 微调功能的 REST 接口。
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import logging

from src.core.ai_organic_core import get_organic_ai_core

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fine-tune", tags=["fine-tune"])


# ─────────────────────────────── 请求/响应模型 ────────────────────────────────

class FineTuneRequest(BaseModel):
    """微调请求体"""
    exploration_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="探索率 [0, 1]")
    exploration_min: Optional[float] = Field(None, ge=0.0, le=1.0, description="最小探索率")
    exploration_decay: Optional[float] = Field(None, gt=0.0, le=1.0, description="探索衰减系数")
    utilization_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="资源利用权重")
    iteration_interval: Optional[int] = Field(None, ge=1, le=300, description="迭代间隔（秒）")
    memory_retrieval_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="记忆检索阈值")
    max_long_term_memory_size: Optional[int] = Field(None, gt=0, description="长期记忆容量上限")
    multimodal_weights: Optional[Dict[str, float]] = Field(None, description="多模态权重字典")
    hardware_learning_enabled: Optional[bool] = Field(None, description="是否启用硬件学习")
    multimodal_fusion_enabled: Optional[bool] = Field(None, description="是否启用多模态融合")
    perform_evolution: Optional[bool] = Field(None, description="是否执行网络结构演化")
    evolution_strategy: Optional[str] = Field(None, description="演化策略: adaptive/random/gradient/evolutionary")


class FineTuneResponse(BaseModel):
    success: bool
    updated_params: Dict[str, Any] = {}
    evolution_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ValidationResponse(BaseModel):
    is_valid: bool
    error_message: str


# ─────────────────────────────── 端点 ────────────────────────────────────────

@router.get("/status", summary="获取微调相关状态")
async def get_fine_tune_status():
    """返回 OrganicAICore 当前状态及可微调参数的当前值。"""
    core = await get_organic_ai_core()
    status = core.get_status()
    # 附加可微调参数的当前快照
    status["tunable_params"] = {
        "exploration_rate": getattr(core, "_current_exploration_rate", 0.1),
        "exploration_min": getattr(core, "_exploration_min", 0.05),
        "exploration_decay": getattr(core, "_exploration_decay", 0.995),
        "utilization_weight": getattr(core, "_utilization_weight", 0.5),
        "iteration_interval": core.iteration_interval,
        "memory_retrieval_threshold": getattr(core, "_memory_retrieval_threshold", 0.7),
        "max_long_term_memory_size": getattr(core, "max_long_term_memory_size", 5000),
        "multimodal_weights": getattr(core, "_multimodal_weights", {
            "vision": 0.25, "speech": 0.25, "text": 0.25, "sensor": 0.25
        }),
        "hardware_learning_enabled": core.hardware_learning_enabled,
        "multimodal_fusion_enabled": getattr(core, "multimodal_fusion_enabled", True),
    }
    return status


@router.post("/run", response_model=FineTuneResponse, summary="执行微调")
async def run_fine_tune(request: FineTuneRequest):
    """
    对 OrganicAICore 执行一次参数微调。

    - 支持单次调整多个参数
    - 所有参数均为可选；只传需要修改的字段即可
    - 若 perform_evolution=true，将同时触发网络结构演化
    """
    core = await get_organic_ai_core()

    # 将请求体转为字典，去除 None 值
    params = {k: v for k, v in request.dict().items() if v is not None}

    try:
        result = await core.fine_tune(params)
        return FineTuneResponse(**result)
    except Exception as e:
        logger.error(f"fine_tune 调用失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidationResponse, summary="仅验证参数，不执行微调")
async def validate_params(request: FineTuneRequest):
    """
    预检微调参数合法性，不对模型做任何修改。
    适合在实际微调前确认参数是否正确。
    """
    core = await get_organic_ai_core()
    params = {k: v for k, v in request.dict().items() if v is not None}
    is_valid, error_msg = core._validate_fine_tune_params(params)
    return ValidationResponse(is_valid=is_valid, error_message=error_msg)


@router.post("/quick/{preset}", summary="快捷微调预设")
async def quick_fine_tune(preset: str):
    """
    使用预定义方案快速微调。

    可用预设:
    - **explore**      — 提高探索率（适合新环境）
    - **exploit**      — 降低探索率（适合稳定运行）
    - **fast**         — 缩短迭代间隔，加快响应
    - **stable**       — 延长迭代间隔，节省资源
    - **evolve**       — 触发网络结构演化
    - **reset**        — 恢复推荐默认值
    """
    presets = {
        "explore": {
            "exploration_rate": 0.3,
            "exploration_min": 0.1,
            "exploration_decay": 0.99,
        },
        "exploit": {
            "exploration_rate": 0.05,
            "exploration_min": 0.02,
            "exploration_decay": 0.999,
        },
        "fast": {
            "iteration_interval": 15,
        },
        "stable": {
            "iteration_interval": 120,
        },
        "evolve": {
            "perform_evolution": True,
            "evolution_strategy": "adaptive",
        },
        "reset": {
            "exploration_rate": 0.1,
            "exploration_min": 0.05,
            "exploration_decay": 0.995,
            "utilization_weight": 0.5,
            "iteration_interval": 60,
            "memory_retrieval_threshold": 0.7,
            "multimodal_weights": {
                "vision": 0.25, "speech": 0.25, "text": 0.25, "sensor": 0.25
            },
            "hardware_learning_enabled": True,
            "multimodal_fusion_enabled": True,
        },
    }

    if preset not in presets:
        raise HTTPException(
            status_code=400,
            detail=f"未知预设 '{preset}'，可用预设: {list(presets.keys())}"
        )

    core = await get_organic_ai_core()
    result = await core.fine_tune(presets[preset])
    result["preset_used"] = preset
    return result
