"""
任务提案 API 路由
提供任务审批、查询、执行等功能
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging

from src.services.task_proposal_service import (
    get_pending_proposals,
    get_proposal,
    approve_proposal,
    reject_proposal,
    ProposalStatus,
)
from src.services.wechat_notification_service import (
    send_task_proposal_notification,
    send_task_result_notification,
    get_subscribed_users,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


# ── 查询接口 ───────────────────────────────────────────────

@router.get("/proposals/pending", summary="获取待审批的任务提案列表")
async def list_pending_proposals(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    获取所有待审批的任务提案列表
    
    Returns:
        提案列表，包含详细信息
    """
    try:
        proposals = get_pending_proposals(limit=limit)
        return {
            "success": True,
            "count": len(proposals),
            "proposals": proposals,
        }
    except Exception as e:
        logger.error(f"获取待审批提案列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposals/{proposal_id}", summary="获取单个提案详情")
async def get_proposal_detail(proposal_id: str):
    """
    获取指定ID的任务提案详细信息
    
    Args:
        proposal_id: 提案ID
        
    Returns:
        提案详细信息
    """
    try:
        proposal = get_proposal(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="提案不存在")
        
        return {
            "success": True,
            "proposal": proposal,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取提案详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── 审批接口 ───────────────────────────────────────────────

@router.post("/proposals/{proposal_id}/approve", summary="批准任务提案")
async def approve_task_proposal(
    proposal_id: str,
    user_id: str = Query(..., description="审批人用户ID"),
    push_wechat: bool = Query(True, description="是否推送微信通知"),
):
    """
    批准任务提案，触发任务执行
    
    Args:
        proposal_id: 提案ID
        user_id: 审批人用户ID
        push_wechat: 是否推送微信通知
        
    Returns:
        审批结果
    """
    try:
        # 检查提案是否存在
        proposal = get_proposal(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="提案不存在")
        
        if proposal["status"] != ProposalStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="提案状态不是待审批")
        
        # 批准提案
        success = await approve_proposal(proposal_id, user_id)
        if not success:
            raise HTTPException(status_code=500, detail="审批失败")
        
        # 发送微信通知（如果启用）
        if push_wechat:
            try:
                # 获取订阅用户
                users = get_subscribed_users()
                if users:
                    # 发送执行开始通知
                    await send_task_result_notification(
                        openid=users[0],  # 发送给第一个订阅用户（实际项目中根据业务逻辑选择）
                        task_title=proposal["title"],
                        result="任务已开始执行",
                        status="执行中",
                    )
            except Exception as e:
                logger.warning(f"微信通知发送失败: {e}")
        
        logger.info(f"任务提案 {proposal_id} 已被 {user_id} 批准并启动执行")
        
        return {
            "success": True,
            "message": "提案已批准，任务开始执行",
            "proposal_id": proposal_id,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批准提案失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/{proposal_id}/reject", summary="拒绝任务提案")
async def reject_task_proposal(
    proposal_id: str,
    user_id: str = Query(..., description="审批人用户ID"),
    reason: str = Query("", description="拒绝原因"),
):
    """
    拒绝任务提案
    
    Args:
        proposal_id: 提案ID
        user_id: 审批人用户ID
        reason: 拒绝原因
        
    Returns:
        拒绝结果
    """
    try:
        # 检查提案是否存在
        proposal = get_proposal(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="提案不存在")
        
        if proposal["status"] != ProposalStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="提案状态不是待审批")
        
        # 拒绝提案
        success = await reject_proposal(proposal_id, user_id, reason)
        if not success:
            raise HTTPException(status_code=500, detail="拒绝失败")
        
        logger.info(f"任务提案 {proposal_id} 已被 {user_id} 拒绝: {reason}")
        
        return {
            "success": True,
            "message": "提案已拒绝",
            "proposal_id": proposal_id,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"拒绝提案失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── 微信推送接口 ───────────────────────────────────────────

@router.post("/wechat/push-proposal", summary="推送任务提案到微信")
async def push_proposal_to_wechat(
    proposal_id: str = Query(..., description="提案ID"),
):
    """
    手动推送任务提案到微信小程序
    
    Args:
        proposal_id: 提案ID
        
    Returns:
        推送结果
    """
    try:
        # 获取提案详情
        proposal = get_proposal(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="提案不存在")
        
        # 获取订阅用户
        users = get_subscribed_users()
        if not users:
            return {
                "success": False,
                "message": "没有订阅用户",
            }
        
        # 发送通知给所有订阅用户
        success_count = 0
        for openid in users:
            try:
                success = await send_task_proposal_notification(
                    openid=openid,
                    proposal_title=proposal["title"],
                    proposal_desc=proposal["description"],
                    task_type=proposal["task_type"],
                    risk_level=proposal["risk_level"],
                )
                if success:
                    success_count += 1
            except Exception as e:
                logger.warning(f"发送给 {openid} 失败: {e}")
        
        # 更新推送状态
        if success_count > 0:
            with get_conn() as conn:
                conn.execute("""
                    UPDATE task_proposals 
                    SET wechat_pushed = 1 
                    WHERE proposal_id = ?
                """, (proposal_id,))
        
        logger.info(f"提案 {proposal_id} 已推送给 {success_count} 个微信用户")
        
        return {
            "success": True,
            "message": f"推送成功，已发送给 {success_count} 个用户",
            "count": success_count,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"微信推送失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── 任务历史查询 ───────────────────────────────────────────

@router.get("/proposals/history", summary="获取任务历史记录")
async def get_task_history(
    user_id: Optional[str] = Query(None, description="用户ID，用于过滤审批的任务"),
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
):
    """
    获取任务历史记录（包括已审批、执行中的、已完成的任务）
    
    Args:
        user_id: 用户ID（可选）
        status: 状态过滤（可选）
        limit: 数量限制
        
    Returns:
        任务历史列表
    """
    try:
        with get_conn() as conn:
            # 构建查询条件
            conditions = []
            params = []
            
            if user_id:
                conditions.append("approved_by = ?")
                params.append(user_id)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            else:
                # 默认不显示 pending 状态的（未审批的）
                conditions.append("status != 'pending'")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 执行查询
            rows = conn.execute(f"""
                SELECT * FROM task_proposals 
                WHERE {where_clause}
                ORDER BY created_at DESC 
                LIMIT ?
            """, (*params, limit)).fetchall()
            
            proposals = []
            for row in rows:
                proposal = dict(row)
                proposal["parameters"] = json.loads(proposal["parameters"])
                proposals.append(proposal)
            
            return {
                "success": True,
                "count": len(proposals),
                "proposals": proposals,
            }
    
    except Exception as e:
        logger.error(f"获取任务历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── 统计接口 ───────────────────────────────────────────────

@router.get("/stats", summary="获取任务统计信息")
async def get_task_statistics():
    """
    获取任务统计信息
    
    Returns:
        统计信息
    """
    try:
        with get_conn() as conn:
            # 各状态的任务数量
            status_counts = {}
            for status in ["pending", "approved", "executing", "completed", "failed", "rejected"]:
                row = conn.execute(
                    "SELECT COUNT(*) as count FROM task_proposals WHERE status = ?",
                    (status,)
                ).fetchone()
                status_counts[status] = row["count"]
            
            # 今日任务数
            today = datetime.now().strftime("%Y-%m-%d")
            row = conn.execute("""
                SELECT COUNT(*) as count FROM task_proposals 
                WHERE DATE(created_at) = ?
            """, (today,)).fetchone()
            today_count = row["count"]
            
            # 已推送微信的任务数
            row = conn.execute("""
                SELECT COUNT(*) as count FROM task_proposals 
                WHERE wechat_pushed = 1
            """).fetchone()
            pushed_count = row["count"]
            
            return {
                "success": True,
                "statistics": {
                    "status_counts": status_counts,
                    "today_count": today_count,
                    "wechat_pushed_count": pushed_count,
                },
            }
    
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
