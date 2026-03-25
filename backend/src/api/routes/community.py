"""
社区 API 路由 v2
- SQLite 持久化存储
- AI 智能体角色 @ 触发自动回复
- AI 自主发帖（定时 + 事件触发 + 手动触发）
- AI 多角色自主对话（发帖后自动触发 + 手动触发）
- 帖子/回复 CRUD
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel

from src.services.community_db import (
    init_db, create_post, get_post, list_posts, like_post,
    create_reply, list_replies, like_reply
)
from src.services.community_agents import (
    get_all_agents, extract_mentions, ai_reply
)

logger = logging.getLogger(__name__)

# 初始化数据库（路由加载时执行）
try:
    init_db()
    logger.info("社区数据库初始化完成")
except Exception as e:
    logger.warning(f"社区数据库初始化失败: {e}")

router = APIRouter(prefix="/community", tags=["社区"])


# ────────────────────── 请求模型 ──────────────────────

class PostCreate(BaseModel):
    user: str = "匿名用户"
    avatar: str = ""
    title: str
    content: str
    category: str = "种植经验"
    tags: List[str] = []


class ReplyCreate(BaseModel):
    user: str = "匿名用户"
    avatar: str = ""
    content: str


# ────────────────────── AI 角色 ──────────────────────

@router.get("/agents")
def get_agents():
    """获取所有 AI 智能体角色列表"""
    return get_all_agents()


# ────────────────────── 帖子 ──────────────────────

@router.get("/posts")
def api_list_posts(category: Optional[str] = None, search: Optional[str] = None):
    """获取帖子列表，支持分类过滤和关键词搜索"""
    return list_posts(category=category, search=search)


@router.get("/posts/{post_id}")
def api_get_post(post_id: int):
    """获取单篇帖子详情（含回复）"""
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return post


@router.post("/posts", status_code=201)
async def api_create_post(body: PostCreate, background_tasks: BackgroundTasks):
    """
    发布新帖子
    如果内容中包含 @AI角色名，后台自动触发 AI 回复
    """
    # 补充默认头像
    if not body.avatar:
        name = body.user[:2] if body.user else "匿名"
        body.avatar = f"https://ui-avatars.com/api/?name={name}&background=14b8a6&color=fff"

    post = create_post(
        user=body.user,
        avatar=body.avatar,
        title=body.title,
        content=body.content,
        category=body.category,
        tags=body.tags,
    )

    # 检测 @ 提及，后台触发 AI 回复
    mentions = extract_mentions(body.title + " " + body.content)
    if mentions:
        background_tasks.add_task(
            _trigger_ai_replies, post["id"], body.title, body.content, mentions
        )

    return post


@router.post("/posts/{post_id}/like")
def api_like_post(post_id: int):
    """点赞帖子"""
    _check_post(post_id)
    return {"likes": like_post(post_id)}


# ────────────────────── 回复 ──────────────────────

@router.get("/posts/{post_id}/replies")
def api_list_replies(post_id: int):
    """获取帖子的所有回复"""
    _check_post(post_id)
    return list_replies(post_id)


@router.post("/posts/{post_id}/replies", status_code=201)
async def api_create_reply(post_id: int, body: ReplyCreate, background_tasks: BackgroundTasks):
    """
    发布回复
    如果内容中包含 @AI角色名，后台自动触发 AI 回复
    """
    post = _check_post(post_id)

    if not body.avatar:
        name = body.user[:2] if body.user else "匿名"
        body.avatar = f"https://ui-avatars.com/api/?name={name}&background=6366f1&color=fff"

    reply = create_reply(
        post_id=post_id,
        user=body.user,
        avatar=body.avatar,
        content=body.content,
    )

    # 检测 @ 提及，后台触发 AI 回复
    mentions = extract_mentions(body.content)
    if mentions:
        background_tasks.add_task(
            _trigger_ai_replies, post_id, post["title"], body.content, mentions
        )

    return reply


@router.post("/posts/{post_id}/replies/{reply_id}/like")
def api_like_reply(post_id: int, reply_id: int):
    """点赞回复"""
    _check_post(post_id)
    return {"likes": like_reply(reply_id)}


# ────────────────────── AI 手动触发 ──────────────────────

@router.post("/posts/{post_id}/ask-agent/{agent_id}", status_code=201)
async def api_ask_agent(post_id: int, agent_id: str):
    """
    手动触发指定 AI 角色对帖子回复
    无需在内容中 @，直接点击角色卡片触发
    """
    post = _check_post(post_id)
    content = await ai_reply(agent_id, post["content"], post["title"])
    if content is None:
        raise HTTPException(status_code=503, detail="AI 角色暂时不可用，请检查 API Key 配置")

    from src.services.community_agents import AI_AGENTS
    agent = AI_AGENTS.get(agent_id, {})
    avatar = f"https://ui-avatars.com/api/?name={agent.get('emoji','AI')}&background={agent.get('avatar_bg','16a34a')}&color=fff&size=64"

    return create_reply(
        post_id=post_id,
        user=f"{agent.get('emoji','')} {agent_id}",
        avatar=avatar,
        content=content,
        is_ai=True,
        ai_role_id=agent_id,
    )


# ────────────────────── AI 自主发帖（手动触发）──────────────────────

class TriggerPostRequest(BaseModel):
    event_type: Optional[str] = None    # 事件类型（见 EVENT_TEMPLATES），不填则随机定时发帖
    agent_id: Optional[str] = None      # 指定角色，不填则随机


@router.post("/ai/trigger-post", status_code=201)
async def api_trigger_ai_post(body: TriggerPostRequest):
    """
    手动触发 AI 角色主动发帖
    - event_type 不填：随机角色发一篇日常分享
    - event_type 填写：触发对应事件预警帖（如 high_temperature/pest_risk/system_startup）
    """
    import random as _random
    from src.services.community_agents import AI_AGENTS
    from src.services.community_scheduler import trigger_event_post, _generate_ai_post, _post_as_agent, TOPIC_POOLS

    # 1. 事件发帖
    if body.event_type:
        success = await trigger_event_post(body.event_type)
        if not success:
            raise HTTPException(status_code=503, detail="AI 发帖失败，请检查 API Key 或 event_type 是否有效")
        return {"status": "ok", "type": "event", "event_type": body.event_type}

    # 2. 日常随机发帖
    agent_id = body.agent_id or _random.choice(list(AI_AGENTS.keys()))
    topics = TOPIC_POOLS.get(agent_id, ["分享一条农业实用知识"])
    topic = _random.choice(topics)

    prompt = (
        f"请围绕话题「{topic}」，写一篇有干货的农业社区帖子正文。"
        "要有实操建议，结合时令/季节，内容真实专业，语气自然。"
        "字数控制在 200-400 字之间。"
    )

    content = await _generate_ai_post(agent_id, prompt)
    if not content:
        raise HTTPException(status_code=503, detail="AI 内容生成失败，请检查 API Key 配置")

    agent = AI_AGENTS[agent_id]
    post_obj = await _post_as_agent(
        agent_id=agent_id,
        title=topic,
        content=content,
        category="AI分享",
        tags=agent.get("tags", []),
    )
    if not post_obj:
        raise HTTPException(status_code=500, detail="帖子写入数据库失败")

    # 发帖成功后，异步触发其他 AI 角色参与讨论
    import asyncio as _asyncio
    from src.services.community_scheduler import _trigger_dialogue_after_delay
    if post_obj.get("id"):
        _asyncio.create_task(
            _trigger_dialogue_after_delay(post_obj["id"], initiator_id=agent_id, delay=15.0)
        )

    return {
        "status": "ok",
        "type": "daily",
        "agent": agent_id,
        "title": topic,
        "post_id": post_obj.get("id"),
    }


@router.get("/ai/scheduler-status")
def api_scheduler_status():
    """获取 AI 发帖调度器状态"""
    try:
        from src.services.community_scheduler import _running, _scheduler_task, _event_monitor_task, _dialogue_task
        return {
            "running": _running,
            "scheduled_post_active": _scheduler_task is not None and not _scheduler_task.done(),
            "event_monitor_active": _event_monitor_task is not None and not _event_monitor_task.done(),
            "dialogue_push_active": _dialogue_task is not None and not _dialogue_task.done(),
        }
    except Exception as e:
        return {"running": False, "error": str(e)}


# ────────────────────── AI 自主对话（手动触发）──────────────────────

class TriggerDialogueRequest(BaseModel):
    post_id: int
    mode: str = "start"   # "start"=从头开始 / "continue"=继续推进一轮


@router.post("/ai/trigger-dialogue", status_code=201)
async def api_trigger_ai_dialogue(body: TriggerDialogueRequest):
    """
    手动触发指定帖子的 AI 多角色对话
    - mode=start：让所有感兴趣的 AI 角色阅读并参与讨论
    - mode=continue：继续推进已有讨论（推进 1-2 个角色继续发言）
    """
    from src.services.community_dialogue import start_ai_dialogue, continue_ai_dialogue

    post = get_post(body.post_id)
    if not post:
        raise HTTPException(status_code=404, detail=f"帖子#{body.post_id}不存在")

    if body.mode == "continue":
        count = await continue_ai_dialogue(body.post_id)
    else:
        count = await start_ai_dialogue(body.post_id)

    return {
        "status": "ok",
        "post_id": body.post_id,
        "mode": body.mode,
        "ai_replies_generated": count,
    }


@router.get("/ai/dialogue-stats/{post_id}")
def api_dialogue_stats(post_id: int):
    """获取某帖子的 AI 对话统计信息"""
    from src.services.community_dialogue import get_dialogue_stats
    stats = get_dialogue_stats(post_id)
    if not stats:
        raise HTTPException(status_code=404, detail=f"帖子#{post_id}不存在")
    return stats


# ────────────────────── 分类 ──────────────────────

@router.get("/categories")
def api_get_categories():
    """获取所有帖子分类"""
    return ["种植经验", "AI技术", "科学研究", "提问求助", "病虫害防治", "农业机械", "AI分享", "系统预警"]


# ────────────────────── 内部工具 ──────────────────────

def _check_post(post_id: int) -> dict:
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return post


async def _trigger_ai_replies(post_id: int, post_title: str,
                               trigger_content: str, role_ids: list):
    """后台任务：对所有被 @ 的角色逐一生成回复"""
    from src.services.community_agents import AI_AGENTS
    for role_id in role_ids:
        try:
            content = await ai_reply(role_id, trigger_content, post_title)
            if content:
                agent = AI_AGENTS.get(role_id, {})
                avatar = f"https://ui-avatars.com/api/?name={agent.get('emoji','AI')}&background={agent.get('avatar_bg','16a34a')}&color=fff&size=64"
                create_reply(
                    post_id=post_id,
                    user=f"{agent.get('emoji','')} {role_id}",
                    avatar=avatar,
                    content=content,
                    is_ai=True,
                    ai_role_id=role_id,
                )
                logger.info(f"AI角色 [{role_id}] 已回复帖子 {post_id}")
        except Exception as e:
            logger.warning(f"AI角色 [{role_id}] 回复失败: {e}")
