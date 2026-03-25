"""
社区 API 路由 v2
- SQLite 持久化存储
- AI 智能体角色 @ 触发自动回复
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


# ────────────────────── 分类 ──────────────────────

@router.get("/categories")
def api_get_categories():
    """获取所有帖子分类"""
    return ["种植经验", "AI技术", "科学研究", "提问求助", "病虫害防治", "农业机械"]


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
