"""
农业数据溯源 + PHOTON 奖励 API 路由
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/provenance", tags=["数据溯源"])

# ── Pydantic 模型 ──────────────────────────────────────────────

class InferenceProvenanceRequest(BaseModel):
    data_id: str
    model_id: str
    result_summary: str
    user_id: str = "anonymous"
    file_name: str = ""


class PhotonAwardRequest(BaseModel):
    user_id: str
    round_id: str
    accuracy: float = 0.0


# ── 溯源 API ────────────────────────────────────────────────────

@router.post("/upload", summary="记录数据上传溯源事件")
async def record_upload(
    file: UploadFile = File(...),
    user_id: str = Form(default="anonymous"),
):
    """
    用户上传图片时调用，自动生成 data_id 和区块链溯源记录。
    返回 data_id 供后续推理记录使用。
    """
    try:
        from src.services.provenance_service import record_upload_event
        from src.services.photon_service import award_data_upload

        file_bytes = await file.read()
        result = record_upload_event(
            file_name=file.filename or "unknown",
            file_bytes=file_bytes,
            user_id=user_id,
        )
        # 上传数据也给小额 PHOTON 奖励
        photon = award_data_upload(user_id, data_count=1)
        return {
            "success": True,
            "data_id": result["data_id"],
            "tx_hash": result["tx_hash"],
            "file_hash": result["file_hash"],
            "timestamp": result["timestamp"],
            "photon_earned": photon["photon_earned"],
            "photon_balance": photon["new_balance"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"溯源记录失败: {str(e)}")


@router.post("/inference", summary="记录AI推理溯源事件")
async def record_inference(req: InferenceProvenanceRequest):
    """
    AI 推理完成后调用，将「模型 X 处理了数据 Y」记录到溯源链。
    """
    try:
        from src.services.provenance_service import record_inference_event
        result = record_inference_event(
            data_id=req.data_id,
            model_id=req.model_id,
            result_summary=req.result_summary,
            user_id=req.user_id,
            file_name=req.file_name,
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理溯源记录失败: {str(e)}")


@router.get("/my-data", summary="获取我的数据使用记录")
async def get_my_data(
    user_id: str = Query(default="anonymous"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """
    「我的数据」页面 —— 查询当前用户的全部上传和推理溯源记录。
    """
    try:
        from src.services.provenance_service import get_user_provenance
        records = get_user_provenance(user_id, limit)
        return {
            "success": True,
            "user_id": user_id,
            "records": records,
            "total": len(records),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/data/{data_id}", summary="查询数据完整溯源链")
async def get_data_chain(data_id: str):
    """
    根据 data_id 查询该数据的完整溯源链（上传 → 多次推理记录）。
    """
    try:
        from src.services.provenance_service import get_data_provenance
        records = get_data_provenance(data_id)
        if not records:
            raise HTTPException(status_code=404, detail="溯源记录不存在")
        return {
            "success": True,
            "data_id": data_id,
            "provenance_chain": records,
            "total_steps": len(records),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/stats", summary="获取溯源统计数据（供区块链页面使用）")
async def get_provenance_stats():
    """返回全局溯源统计，包括记录数、用户数、联邦学习参与者数"""
    try:
        from src.services.provenance_service import get_stats
        from src.services.photon_service import get_global_stats
        prov = get_stats()
        photon = get_global_stats()
        return {
            "success": True,
            **prov,
            **photon,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计失败: {str(e)}")


# ── PHOTON 奖励 API ─────────────────────────────────────────────

@router.post("/photon/award-training", summary="联邦学习训练完成发放PHOTON奖励")
async def award_training(req: PhotonAwardRequest):
    """
    联邦学习一轮训练聚合完成后调用，给参与者发放 PHOTON 奖励。
    """
    try:
        from src.services.photon_service import award_training
        result = award_training(
            user_id=req.user_id,
            round_id=req.round_id,
            accuracy=req.accuracy,
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"奖励发放失败: {str(e)}")


@router.get("/photon/balance", summary="查询PHOTON余额")
async def get_photon_balance(user_id: str = Query(default="anonymous")):
    """查询用户当前 PHOTON 余额和历史总收入"""
    try:
        from src.services.photon_service import get_balance, get_transactions
        balance = get_balance(user_id)
        txs = get_transactions(user_id, limit=10)
        return {
            "success": True,
            **balance,
            "recent_transactions": txs,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/photon/leaderboard", summary="PHOTON贡献排行榜")
async def get_leaderboard(limit: int = Query(default=10, ge=1, le=50)):
    """获取贡献排行榜，按 PHOTON 总收入降序"""
    try:
        from src.services.photon_service import get_leaderboard
        board = get_leaderboard(limit)
        return {"success": True, "leaderboard": board}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"排行榜获取失败: {str(e)}")
