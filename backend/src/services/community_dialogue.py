"""
AI 智能体自主对话引擎
────────────────────────────────────────────────────────
功能：
  1. AI 看帖回复：任何新帖发布后，各 AI 角色"阅读"帖子，
     根据自己的专业方向决定是否参与讨论并自动回复
  2. AI 接力对话：一个 AI 回复后，其他 AI 读到该回复，
     决定是否进一步补充/反驳/提问，形成多轮讨论链
  3. 防止刷屏：单帖每个 AI 最多回复 2 次，
     总讨论轮次上限 6 轮
  4. 主题相关性过滤：只有与 AI 专业方向相关的帖子才触发回复

调用入口：
  await start_ai_dialogue(post_id)       # 针对指定帖子启动 AI 对话
  await continue_ai_dialogue(post_id)    # 对已有讨论继续推进一轮
"""

import asyncio
import logging
import random
from typing import Optional, Dict, List

from src.services.community_db import get_post, create_reply, list_replies
from src.services.community_agents import AI_AGENTS
from src.core.services.cloud_ai_service import chat_completion

logger = logging.getLogger(__name__)

# ── 配置常量 ──────────────────────────────────────────────
# 每个帖子最多触发的 AI 对话轮次
MAX_DIALOGUE_ROUNDS = 6
# 单帖中每个 AI 角色最多回复次数
MAX_REPLIES_PER_AGENT_PER_POST = 2
# AI 回复之间的思考延迟（秒），模拟真实阅读时间
REPLY_DELAY_MIN = 3
REPLY_DELAY_MAX = 8
# 触发对话的概率（避免每帖都爆发讨论）
DIALOGUE_TRIGGER_PROBABILITY = 0.7

# ── 角色专业关键词（判断帖子是否与该角色相关）──────────
AGENT_INTEREST_KEYWORDS: Dict[str, List[str]] = {
    "农业专家": ["种植", "产量", "作物", "收成", "土壤", "水稻", "蔬菜", "果树",
                 "种子", "播种", "栽培", "有机", "大棚", "农业"],
    "植保顾问": ["病虫害", "农药", "防治", "斑点", "叶片", "枯萎", "虫", "病",
                 "蚜虫", "锈病", "白粉病", "根腐", "药剂", "绿色防控"],
    "气象分析师": ["天气", "温度", "湿度", "降水", "干旱", "霜冻", "高温", "台风",
                   "气象", "灌溉", "节气", "气候", "预警", "天"],
    "施肥顾问": ["施肥", "肥料", "营养", "氮", "磷", "钾", "有机肥", "微量元素",
                 "追肥", "底肥", "水溶肥", "缺素", "土壤肥力"],
    "技术答疑": ["系统", "API", "配置", "部署", "DeepSeek", "Docker", "功能",
                 "如何", "使用", "错误", "教程", "代码", "设置"],
}

# ── AI 对话时的特殊系统提示（区别于普通问答模式）──────
DIALOGUE_SYSTEM_PROMPTS: Dict[str, str] = {
    "农业专家": (
        "你是农业社区里资深的种植专家，正在参与一场关于农业的专业讨论。"
        "你读了其他人的发言，现在轮到你补充。"
        "风格：亲切务实，可以认同别人的观点并补充实操经验，"
        "也可以温和指出不完善的地方并给出更好的方案。"
        "控制在150字以内，语气自然，像在群聊里聊天。"
    ),
    "植保顾问": (
        "你是植保顾问，正在与其他农业专家在社区里讨论问题。"
        "你的视角是植物病虫害防治，看到讨论中有可以补充的植保知识时主动发言。"
        "如果没有植保相关内容，可以提问或引导话题往病虫害防控方向走。"
        "控制在150字以内，条理清晰，像老朋友聊天。"
    ),
    "气象分析师": (
        "你是气象分析师，正在农业社区参与讨论。"
        "你的专长是气象与农业的结合，从天气、气候角度为讨论补充有价值的视角。"
        "可以引用季节特点、近期天气趋势来支撑或补充其他人的观点。"
        "控制在130字以内，善用数字和具体时间窗口。"
    ),
    "施肥顾问": (
        "你是施肥专家，正在社区里和其他专家讨论农业问题。"
        "你关注作物营养和土壤肥力，看到讨论时从施肥角度贡献你的专业意见。"
        "可以指出营养管理对当前讨论话题的影响，给出具体的配方建议。"
        "控制在150字以内，专业但不枯燥。"
    ),
    "技术答疑": (
        "你是系统技术支持，正在社区里参与讨论。"
        "你了解这套 AI 农业系统的技术细节，可以从系统功能、数据支持、"
        "AI 辅助决策角度为讨论补充技术层面的洞察。"
        "控制在150字以内，简洁清晰，适当提及系统具体功能。"
    ),
}


# ─────────────────────────────────────────────────────────────
# 核心函数
# ─────────────────────────────────────────────────────────────

def _is_agent_interested(agent_id: str, text: str) -> bool:
    """判断某 AI 角色对给定文本是否感兴趣（基于关键词匹配）"""
    keywords = AGENT_INTEREST_KEYWORDS.get(agent_id, [])
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _count_agent_replies_in_post(agent_id: str, post_id: int) -> int:
    """统计某 AI 角色在指定帖子里已回复了几次"""
    try:
        replies = list_replies(post_id)
        agent = AI_AGENTS.get(agent_id, {})
        agent_name = f"{agent.get('emoji', '')} {agent.get('name', agent_id)}"
        return sum(1 for r in replies if r.get("user") == agent_name and r.get("is_ai"))
    except Exception:
        return 0


def _get_discussion_context(post: dict, max_replies: int = 6) -> str:
    """构建帖子 + 近期讨论的上下文文本"""
    lines = [
        f"【帖子标题】{post.get('title', '')}",
        f"【作者】{post.get('user', '用户')}",
        f"【帖子内容】{post.get('content', '')}",
    ]
    replies = post.get("replies", [])
    if replies:
        lines.append("\n【已有讨论（最新{}条）】".format(min(len(replies), max_replies)))
        for r in replies[-max_replies:]:
            lines.append(f"  {r.get('user', '?')}: {r.get('content', '')}")
    return "\n".join(lines)


async def _ai_decide_and_reply(agent_id: str, post: dict) -> Optional[str]:
    """
    让指定 AI 角色决定是否参与讨论，如果参与则生成回复内容
    返回：回复文本 or None（决定不参与）
    """
    post_id = post["id"]

    # 1. 限额检查
    if _count_agent_replies_in_post(agent_id, post_id) >= MAX_REPLIES_PER_AGENT_PER_POST:
        logger.debug(f"[AI对话] {agent_id} 在帖子#{post_id}已达回复上限，跳过")
        return None

    # 2. 兴趣判断（基于帖子标题+内容+现有讨论）
    full_text = (
        post.get("title", "") + " "
        + post.get("content", "") + " "
        + " ".join(r.get("content", "") for r in post.get("replies", []))
    )
    if not _is_agent_interested(agent_id, full_text):
        logger.debug(f"[AI对话] {agent_id} 对帖子#{post_id}不感兴趣，跳过")
        return None

    # 3. 构建上下文，让 AI 决定是否参与并生成回复
    context = _get_discussion_context(post)
    agent = AI_AGENTS[agent_id]

    prompt = (
        f"{context}\n\n"
        f"---\n"
        f"现在请你以 {agent['name']} 的身份参与这个讨论。\n"
        f"如果你认为当前讨论与你的专业方向高度相关，有值得补充的知识点或不同观点，"
        f"请直接输出你的回复内容（不要有开头称呼，直接说观点）。\n"
        f"如果你认为当前话题超出你的专业范围，或者已有讨论很充分了，"
        f"请输出：[PASS]（代表你决定不参与）。"
    )

    result = await chat_completion(
        prompt=prompt,
        system_prompt=DIALOGUE_SYSTEM_PROMPTS.get(agent_id, agent["system_prompt"]),
        temperature=0.75,
        max_tokens=300,
    )

    if not result.get("success"):
        logger.warning(f"[AI对话] {agent_id} 生成回复失败: {result.get('error', '')}")
        return None

    content = result.get("content", "").strip()
    if not content or content.startswith("[PASS]"):
        logger.debug(f"[AI对话] {agent_id} 决定不参与帖子#{post_id}的讨论")
        return None

    return content


async def _post_ai_reply(agent_id: str, post_id: int, content: str) -> bool:
    """以 AI 角色身份发布一条讨论回复"""
    agent = AI_AGENTS.get(agent_id)
    if not agent:
        return False
    avatar = (
        f"https://ui-avatars.com/api/"
        f"?name={agent['emoji']}"
        f"&background={agent['avatar_bg']}"
        f"&color=fff&size=64"
    )
    try:
        create_reply(
            post_id=post_id,
            user=f"{agent['emoji']} {agent['name']}",
            avatar=avatar,
            content=content,
            is_ai=True,
            ai_role_id=agent_id,
        )
        logger.info(f"[AI对话] {agent['name']} 回复了帖子#{post_id}")
        return True
    except Exception as e:
        logger.error(f"[AI对话] 回复写库失败: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# 公共 API
# ─────────────────────────────────────────────────────────────

async def start_ai_dialogue(post_id: int, initiator_id: Optional[str] = None) -> int:
    """
    针对指定帖子启动 AI 多角色对话
    - initiator_id: 发帖的 AI 角色 ID，跳过发帖者本人参与（避免自言自语）
    - 返回：实际产生的 AI 回复数量
    """
    post = get_post(post_id)
    if not post:
        logger.warning(f"[AI对话] 帖子#{post_id}不存在")
        return 0

    # 打乱角色顺序，避免固定顺序响应
    agent_ids = [a for a in AI_AGENTS.keys() if a != initiator_id]
    random.shuffle(agent_ids)

    reply_count = 0
    current_round = len(post.get("replies", []))

    if current_round >= MAX_DIALOGUE_ROUNDS:
        logger.debug(f"[AI对话] 帖子#{post_id}对话轮次已满({current_round})，跳过")
        return 0

    for agent_id in agent_ids:
        # 达到上限就停止
        if current_round + reply_count >= MAX_DIALOGUE_ROUNDS:
            break

        # 模拟 AI"阅读思考"时间
        delay = random.uniform(REPLY_DELAY_MIN, REPLY_DELAY_MAX)
        await asyncio.sleep(delay)

        # 重新拉取最新帖子（包含最新回复，用于上下文）
        post = get_post(post_id)
        if not post:
            break

        content = await _ai_decide_and_reply(agent_id, post)
        if content:
            success = await _post_ai_reply(agent_id, post_id, content)
            if success:
                reply_count += 1

    logger.info(f"[AI对话] 帖子#{post_id} 本轮 AI 参与了{reply_count}次讨论")
    return reply_count


async def continue_ai_dialogue(post_id: int) -> int:
    """
    对已有讨论继续推进一轮（由调度器定时调用，或手动触发）
    只有讨论未超上限且已有 AI 参与的帖子才会继续
    """
    post = get_post(post_id)
    if not post:
        return 0

    replies = post.get("replies", [])
    ai_replies = [r for r in replies if r.get("is_ai")]

    # 没有 AI 参与过的帖子，用 start 而不是 continue
    if not ai_replies:
        return await start_ai_dialogue(post_id)

    # 已达上限，不再继续
    if len(replies) >= MAX_DIALOGUE_ROUNDS:
        return 0

    # 随机选一个还没超过回复上限的 AI 角色继续讨论
    participated = {r.get("ai_role_id") for r in ai_replies}
    all_agents = list(AI_AGENTS.keys())
    candidates = [
        a for a in all_agents
        if _count_agent_replies_in_post(a, post_id) < MAX_REPLIES_PER_AGENT_PER_POST
    ]
    if not candidates:
        return 0

    random.shuffle(candidates)
    for agent_id in candidates[:2]:  # 每次最多推进 2 个角色
        await asyncio.sleep(random.uniform(REPLY_DELAY_MIN, REPLY_DELAY_MAX))
        post = get_post(post_id)
        if not post:
            break
        content = await _ai_decide_and_reply(agent_id, post)
        if content:
            await _post_ai_reply(agent_id, post_id, content)

    return 1


async def trigger_dialogue_for_recent_posts(limit: int = 3) -> int:
    """
    对最近的帖子触发 AI 对话（调度器定时调用）
    - 随机选几篇讨论不够热闹的帖子
    - 触发 AI 多角色参与讨论
    """
    from src.services.community_db import list_posts

    posts = list_posts()
    if not posts:
        return 0

    # 过滤：选出 AI 回复数少于 MAX_DIALOGUE_ROUNDS 的帖子
    candidates = [
        p for p in posts[:20]  # 只考虑最近20篇
        if len([r for r in p.get("replies", []) if r.get("is_ai")]) < MAX_DIALOGUE_ROUNDS
    ]

    if not candidates:
        return 0

    # 随机选几篇
    selected = random.sample(candidates, min(limit, len(candidates)))
    total = 0
    for post in selected:
        if random.random() < DIALOGUE_TRIGGER_PROBABILITY:
            count = await start_ai_dialogue(post["id"])
            total += count

    return total


def get_dialogue_stats(post_id: int) -> Dict:
    """获取某帖子的 AI 对话统计信息"""
    post = get_post(post_id)
    if not post:
        return {}

    replies = post.get("replies", [])
    ai_replies = [r for r in replies if r.get("is_ai")]
    human_replies = [r for r in replies if not r.get("is_ai")]

    participants = {}
    for r in ai_replies:
        role = r.get("ai_role_id", "unknown")
        participants[role] = participants.get(role, 0) + 1

    return {
        "post_id": post_id,
        "total_replies": len(replies),
        "ai_replies": len(ai_replies),
        "human_replies": len(human_replies),
        "dialogue_rounds": len(replies),
        "max_rounds": MAX_DIALOGUE_ROUNDS,
        "is_maxed": len(replies) >= MAX_DIALOGUE_ROUNDS,
        "participants": participants,
    }
