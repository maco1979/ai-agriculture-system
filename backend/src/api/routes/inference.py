"""
推理服务API路由
提供文本生成、图像分类等推理功能
已迁移至云端模型，见 cloud_ai.py
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging

from src.core.services import model_manager
from src.core.services.cloud_ai_service import (
    chat_completion,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inference", tags=["inference"])


class TextGenerationRequest(BaseModel):
    """文本生成请求"""
    model_id: str
    prompt: str
    max_length: Optional[int] = 100
    temperature: Optional[float] = 1.0
    repetition_penalty: Optional[float] = 1.0
    num_return_sequences: Optional[int] = 1
    beam_search: Optional[bool] = False
    beam_width: Optional[int] = 5
    early_stopping: Optional[bool] = True
    no_repeat_ngram_size: Optional[int] = 0
    do_sample: Optional[bool] = False
    top_p: Optional[float] = 1.0
    top_k: Optional[int] = 0


class ImageClassificationRequest(BaseModel):
    """图像分类请求"""
    model_id: str
    image_data: List[List[List[float]]]  # 3D数组: [height, width, channels]
    top_k: Optional[int] = 5


class ImageGenerationRequest(BaseModel):
    """图像生成请求"""
    model_id: str
    num_samples: Optional[int] = 1
    image_size: Optional[int] = 256
    guidance_scale: Optional[float] = 7.5


class BatchInferenceRequest(BaseModel):
    """批量推理请求"""
    model_id: str
    inputs: List[Any]
    batch_size: Optional[int] = 32


class InferenceResponse(BaseModel):
    """推理响应"""
    predictions: Any
    confidence: Optional[float] = None
    processing_time: float
    metadata: Dict[str, Any]


class BatchInferenceResponse(BaseModel):
    """批量推理响应"""
    results: List[InferenceResponse]
    total_count: int
    success_count: int
    error_count: int


@router.post("/text/generation", response_model=InferenceResponse, deprecated=True)
async def text_generation(request: TextGenerationRequest):
    """
    文本生成推理（已弃用）
    请使用 /api/ai/chat 端点替代
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="此端点已弃用，请使用 /api/ai/chat 端点"
    )


@router.post("/image/classification", response_model=InferenceResponse, deprecated=True)
async def image_classification(request: ImageClassificationRequest):
    """
    图像分类推理（已弃用）
    本地推理功能已迁移至云端模型
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="此端点已弃用，本地推理功能已迁移至云端模型"
    )


@router.post("/image/generation", response_model=InferenceResponse, deprecated=True)
async def image_generation(request: ImageGenerationRequest):
    """
    图像生成推理（已弃用）
    本地推理功能已迁移至云端模型
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="此端点已弃用，本地推理功能已迁移至云端模型"
    )


@router.post("/batch", response_model=BatchInferenceResponse, deprecated=True)
async def batch_inference(request: BatchInferenceRequest):
    """
    批量推理（已弃用）
    本地推理功能已迁移至云端模型
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="此端点已弃用，本地推理功能已迁移至云端模型"
    )


@router.get("/stats/{model_id}", deprecated=True)
async def get_inference_stats(model_id: str):
    """
    获取推理统计信息（已弃用）
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="此端点已弃用"
    )


@router.delete("/cache/{model_id}", deprecated=True)
async def clear_inference_cache(model_id: str):
    """
    清除推理缓存（已弃用）
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="此端点已弃用"
    )


@router.delete("/cache", deprecated=True)
async def clear_all_inference_cache():
    """
    清除所有推理缓存（已弃用）
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="此端点已弃用"
    )


# ─── 统一推理端点（自动路由云端/本地模型）────────────────────────────────────

class UnifiedInferenceRequest(BaseModel):
    """统一推理请求 —— 同时支持云端和本地模型"""
    model_id: str
    prompt: str
    system_prompt: Optional[str] = "你是一个专业的AI农业决策助手。"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000


@router.post("/unified", tags=["inference"])
async def unified_inference(request: UnifiedInferenceRequest):
    """
    统一推理端点 —— 自动判断模型来源。

    - 若 model_id 对应的模型元数据中 is_cloud=True，则走云端 API 调用。
    - 否则走本地推理引擎（需要模型权重已加载）。
    """
    import time

    try:
        # 查询模型元数据，判断是否为云端模型
        meta_result = await model_manager.get_model_info(request.model_id)

        if meta_result.get("success") and meta_result.get("model"):
            model_meta = meta_result["model"]
            metadata = model_meta.get("metadata", {})
            is_cloud = metadata.get("is_cloud", False) or model_meta.get("type") == "cloud"
        else:
            is_cloud = False

        start_ts = time.time()

        if is_cloud:
            # ── 云端 API 调用 ──────────────────────────
            provider = metadata.get("provider", "")
            model_name = metadata.get("model_name", request.model_id)

            # 调用云端服务
            result = await chat_completion(
                prompt=request.prompt,
                system_prompt=request.system_prompt or "你是一个专业的AI农业决策助手。",
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            elapsed = round(time.time() - start_ts, 3)
            if result.get("success"):
                return {
                    "success": True,
                    "model_source": "cloud",
                    "provider": provider,
                    "model_id": request.model_id,
                    "model_name": model_name,
                    "content": result.get("content"),
                    "processing_time": elapsed,
                    "usage": result.get("usage"),
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=result.get("error", "云端模型调用失败")
                )

        else:
            # ── 本地推理引擎 ────────────────────────────
            local_result = await model_manager.predict(
                model_id=request.model_id,
                input_data={"prompt": request.prompt, "max_tokens": request.max_tokens}
            )
            elapsed = round(time.time() - start_ts, 3)

            if local_result.get("success"):
                return {
                    "success": True,
                    "model_source": "local",
                    "model_id": request.model_id,
                    "content": local_result.get("output") or local_result.get("predictions"),
                    "processing_time": elapsed,
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=local_result.get("error", "本地推理失败")
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"统一推理失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"统一推理失败: {str(e)}"
        )
