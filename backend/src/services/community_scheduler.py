"""
社区 AI 自主发帖调度器
─────────────────────────────────────────────────────────
功能：
  1. 定时发帖：每小时 AI 角色轮流发一篇日常农业知识帖
  2. 事件触发发帖：检测到传感器/系统异常时自动发预警帖
  3. 开机发帖：首次启动时每个角色发一篇介绍帖（可选）

使用方式：
  在 FastAPI lifespan 里调用 start_scheduler() / stop_scheduler()
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from src.services.community_db import create_post, list_posts
from src.services.community_agents import AI_AGENTS
from src.core.services.cloud_ai_service import chat_completion

logger = logging.getLogger(__name__)

# ── 调度器状态 ─────────────────────────────────────────────
_scheduler_task: Optional[asyncio.Task] = None
_event_monitor_task: Optional[asyncio.Task] = None
_running = False

# 每小时定时发帖间隔（秒）
DAILY_POST_INTERVAL = 3600        # 1小时
# 事件监控检查间隔（秒）
EVENT_CHECK_INTERVAL = 300        # 5分钟
# 每天每个角色最多主动发帖数（防刷屏）
MAX_POSTS_PER_AGENT_PER_DAY = 3


# ─────────────────────────────────────────────────────────────
# 发帖内容生成
# ─────────────────────────────────────────────────────────────

# 各角色的定时发帖主题池（用于定时日常分享）
TOPIC_POOLS = {
    "农业专家": [
        "分享一个提升水稻产量的关键技巧",
        "土壤改良实战经验：如何让板结土地重焕活力",
        "高温天气下作物管理要点分享",
        "冬季大棚蔬菜种植注意事项",
        "有机农业转型：减少化学投入的实用方法",
        "种植密度与产量的关系——你可能踩过的坑",
        "春季播种前的土壤准备工作清单",
        "节水农业技术分享：让每一滴水都有价值",
    ],
    "植保顾问": [
        "本季高发病虫害预警与防治策略",
        "农药减量使用的绿色防控组合方案",
        "识别作物叶片异常：5种常见症状速查",
        "生物防治替代化学农药的实践分享",
        "蚜虫爆发期来临，这些防治误区要避开",
        "病害防治黄金时间：为什么早发现早处理至关重要",
        "土传病害的综合防控指南",
        "防治韭蛆的几种有效方法",
    ],
    "气象分析师": [
        "近期天气对主要农作物影响分析",
        "如何根据天气预报调整灌溉计划",
        "极端天气来临前的农业防灾准备",
        "春寒料峭时期作物保温实用措施",
        "台风前后农业生产的应对策略",
        "利用积温预测作物最佳收获时间",
        "干旱预警：节水抗旱的实操建议",
        "倒春寒识别与作物冻害预防",
    ],
    "施肥顾问": [
        "秋季追肥方案：如何为越冬作物补充能量",
        "叶面施肥的正确打开方式与常见错误",
        "磷钾肥施用时机对产量的关键影响",
        "有机肥与化肥配合使用的科学方法",
        "微量元素缺乏的症状识别与补充方案",
        "施肥过量的危害——土壤盐渍化如何避免",
        "水溶肥选购与使用指南",
        "不同土壤类型的施肥策略差异",
    ],
    "技术答疑": [
        "本系统 AI 决策模块使用技巧分享",
        "如何接入 DeepSeek API 让系统用上大模型",
        "Docker 部署常见问题解答汇总",
        "数据看板指标解读：关键数字的含义",
        "传感器数据异常排查步骤",
        "系统新功能介绍：智能体社区功能上线了",
        "如何利用系统做日常农事记录与分析",
        "边缘计算节点接入配置指南",
    ],
}

# 事件触发发帖的主题模板（用于异常预警）
EVENT_TEMPLATES = {
    "high_temperature": {
        "agent": "气象分析师",
        "title_tpl": "【高温预警】系统检测到温度异常，农业应对指南",
        "prompt_tpl": (
            "系统传感器检测到当前温度达到{value}°C，超过正常农业生产安全范围。"
            "请以气象分析师身份，发一篇紧急应对指南帖子，包含："
            "1. 高温对当季主要作物（水稻/蔬菜/果树）的具体危害"
            "2. 立即可执行的降温降损措施（遮阳网/增加灌溉频次等）"
            "3. 未来几天的管理建议"
            "帖子要有紧迫感，条理清晰，实操性强，400字以内。"
        ),
    },
    "low_humidity": {
        "agent": "施肥顾问",
        "title_tpl": "【干旱预警】土壤湿度偏低，紧急施肥灌溉建议",
        "prompt_tpl": (
            "系统监测到土壤湿度仅为{value}%，已低于作物正常生长需求。"
            "请发一篇应对帖，包含干旱条件下的水肥管理建议，重点是如何减少蒸发、"
            "提升水分利用效率，以及是否需要调整施肥计划。300字以内。"
        ),
    },
    "pest_risk": {
        "agent": "植保顾问",
        "title_tpl": "【病虫害风险提示】当前气象条件有利于病虫害发生",
        "prompt_tpl": (
            "根据当前温湿度组合（温度{temp}°C，湿度{humidity}%），"
            "系统判断近期病虫害发生风险较高。"
            "请发一篇预警帖，说明当前条件下最可能爆发的病虫害种类、"
            "识别要点和提前防控措施。重点推荐绿色低毒方案。350字以内。"
        ),
    },
    "system_startup": {
        "agent": "技术答疑",
        "title_tpl": "🚀 AI 农业决策系统已启动，欢迎来社区交流！",
        "prompt_tpl": (
            "系统刚刚启动，请以技术支持角色发一篇欢迎帖，简短介绍一下："
            "1. 本社区可以做什么（提问、分享、@ AI 角色咨询）"
            "2. 系统有哪几个 AI 角色，各自擅长什么"
            "3. 如何 @ AI 角色获取专业建议"
            "语气热情友好，200字以内。"
        ),
    },
}


async def _generate_ai_post(agent_id: str, prompt: str) -> Optional[str]:
    """调用 LLM 生成帖子正文"""
    agent = AI_AGENTS.get(agent_id)
    if not agent:
        return None

    # 发帖专用系统提示：比回复更长、更结构化
    post_system_prompt = (
        agent["system_prompt"]
        + "\n\n【发帖模式】现在你要主动在农业社区发一篇帖子，不是回复用户，"
        "而是主动分享你的专业知识。帖子要有实质内容，有干货，有实操性。"
        "直接输出帖子正文，不要有标题（标题由系统另行设置）。"
    )

    result = await chat_completion(
        prompt=prompt,
        system_prompt=post_system_prompt,
        temperature=0.8,
        max_tokens=600,
    )

    if result.get("success"):
        return result.get("content", "").strip()
    logger.warning(f"AI 发帖生成失败 agent={agent_id}: {result.get('error','')}")
    return None


async def _post_as_agent(agent_id: str, title: str, content: str,
                          category: str = "AI分享", tags: list = None,
                          is_event: bool = False) -> bool:
    """以 AI 角色身份发帖到 SQLite"""
    agent = AI_AGENTS.get(agent_id)
    if not agent:
        return False

    if tags is None:
        tags = agent.get("tags", [])
    if is_event:
        tags = ["⚠️预警"] + tags

    avatar = (
        f"https://ui-avatars.com/api/"
        f"?name={agent['emoji']}"
        f"&background={agent['avatar_bg']}"
        f"&color=fff&size=64"
    )

    try:
        create_post(
            user=f"{agent['emoji']} {agent['name']}",
            avatar=avatar,
            title=title,
            content=content,
            category=category,
            tags=tags,
        )
        logger.info(f"[AI自主发帖] {agent['name']} 发布: 《{title}》")
        return True
    except Exception as e:
        logger.error(f"[AI自主发帖] 写库失败: {e}")
        return False


def _count_today_posts(agent_id: str) -> int:
    """统计某 AI 角色今天已经发了多少帖（防刷屏）"""
    try:
        posts = list_posts()
        agent = AI_AGENTS.get(agent_id, {})
        agent_name = f"{agent.get('emoji','')} {agent_id}"
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(
            1 for p in posts
            if p.get("user") == agent_name and p.get("created_at", "").startswith(today)
        )
    except Exception:
        return 0


# ─────────────────────────────────────────────────────────────
# 定时发帖循环
# ─────────────────────────────────────────────────────────────

async def _scheduled_post_loop():
    """定时发帖主循环：每小时让一个随机 AI 角色发一篇分享帖"""
    logger.info("[社区调度器] 定时发帖循环已启动，间隔 %ds", DAILY_POST_INTERVAL)

    # 第一次启动延迟（给后端其他模块初始化留时间）
    await asyncio.sleep(30)

    agent_ids = list(AI_AGENTS.keys())
    idx = 0  # 轮流发帖，顺序均衡

    while _running:
        try:
            agent_id = agent_ids[idx % len(agent_ids)]
            idx += 1

            # 今天发帖限额检查
            if _count_today_posts(agent_id) >= MAX_POSTS_PER_AGENT_PER_DAY:
                logger.debug(f"[定时发帖] {agent_id} 今日已达发帖上限，跳过")
                await asyncio.sleep(DAILY_POST_INTERVAL)
                continue

            # 随机选一个话题
            topics = TOPIC_POOLS.get(agent_id, ["分享一条农业小知识"])
            topic = random.choice(topics)

            prompt = (
                f"请围绕话题「{topic}」，写一篇有干货的农业社区帖子正文。"
                "要有实操建议，结合时令/季节，内容真实专业，语气自然。"
                "字数控制在 200-400 字之间。"
            )

            content = await _generate_ai_post(agent_id, prompt)
            if content:
                agent = AI_AGENTS[agent_id]
                await _post_as_agent(
                    agent_id=agent_id,
                    title=topic,
                    content=content,
                    category="AI分享",
                    tags=agent.get("tags", []),
                )

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[定时发帖] 异常: {e}")

        await asyncio.sleep(DAILY_POST_INTERVAL)

    logger.info("[社区调度器] 定时发帖循环已停止")


# ─────────────────────────────────────────────────────────────
# 事件触发发帖
# ─────────────────────────────────────────────────────────────

async def _get_sensor_snapshot() -> dict:
    """
    获取当前传感器/系统数据快照
    优先从 edge_manager 获取真实数据，没有则返回模拟数据
    """
    try:
        from src.api.routes.edge import edge_manager
        nodes = edge_manager.list_nodes()
        if nodes:
            node = nodes[0]
            metrics = node.get("metrics", {})
            return {
                "temperature": metrics.get("temperature", None),
                "humidity": metrics.get("humidity", None),
                "source": "sensor",
            }
    except Exception:
        pass

    # 返回模拟数据（用于演示/无传感器场景）
    return {
        "temperature": random.uniform(18, 35),
        "humidity": random.uniform(30, 85),
        "source": "simulated",
    }


async def _event_monitor_loop():
    """事件监控循环：定期检查传感器数据，触发异常预警帖"""
    logger.info("[社区调度器] 事件监控循环已启动，间隔 %ds", EVENT_CHECK_INTERVAL)

    # 避免启动时重复触发（记录已发出预警的事件类型，冷却时间内不重复发）
    cooldowns: dict = {}  # event_type -> datetime

    # 启动后先发一篇欢迎帖
    await asyncio.sleep(15)
    await trigger_event_post("system_startup")

    while _running:
        try:
            now = datetime.now()
            snapshot = await _get_sensor_snapshot()
            temp = snapshot.get("temperature")
            humidity = snapshot.get("humidity")

            # 规则1：高温预警（>32°C）
            if temp is not None and temp > 32:
                event_key = "high_temperature"
                if _check_cooldown(cooldowns, event_key, hours=4):
                    await trigger_event_post(
                        event_key,
                        context={"value": f"{temp:.1f}"},
                    )
                    cooldowns[event_key] = now

            # 规则2：干旱预警（湿度 < 35%）
            if humidity is not None and humidity < 35:
                event_key = "low_humidity"
                if _check_cooldown(cooldowns, event_key, hours=6):
                    await trigger_event_post(
                        event_key,
                        context={"value": f"{humidity:.1f}"},
                    )
                    cooldowns[event_key] = now

            # 规则3：病虫害风险（高温高湿组合）
            if temp is not None and humidity is not None and temp > 28 and humidity > 75:
                event_key = "pest_risk"
                if _check_cooldown(cooldowns, event_key, hours=8):
                    await trigger_event_post(
                        event_key,
                        context={"temp": f"{temp:.1f}", "humidity": f"{humidity:.1f}"},
                    )
                    cooldowns[event_key] = now

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[事件监控] 异常: {e}")

        await asyncio.sleep(EVENT_CHECK_INTERVAL)

    logger.info("[社区调度器] 事件监控循环已停止")


def _check_cooldown(cooldowns: dict, event_key: str, hours: int) -> bool:
    """检查事件是否已过冷却期"""
    last = cooldowns.get(event_key)
    if last is None:
        return True
    return (datetime.now() - last) > timedelta(hours=hours)


async def trigger_event_post(event_type: str, context: dict = None) -> bool:
    """
    手动或自动触发一次事件发帖
    event_type: EVENT_TEMPLATES 中的 key
    context: 格式化模板所需的变量
    """
    tpl = EVENT_TEMPLATES.get(event_type)
    if not tpl:
        logger.warning(f"未知事件类型: {event_type}")
        return False

    context = context or {}
    agent_id = tpl["agent"]

    try:
        title = tpl["title_tpl"].format(**context)
        prompt = tpl["prompt_tpl"].format(**context)
    except KeyError as e:
        logger.error(f"事件模板格式化失败 {event_type}: {e}")
        return False

    content = await _generate_ai_post(agent_id, prompt)
    if not content:
        return False

    return await _post_as_agent(
        agent_id=agent_id,
        title=title,
        content=content,
        category="系统预警" if "预警" in title else "AI分享",
        tags=AI_AGENTS.get(agent_id, {}).get("tags", []),
        is_event=event_type not in ("system_startup",),
    )


# ─────────────────────────────────────────────────────────────
# 公共 API：start / stop
# ─────────────────────────────────────────────────────────────

def start_scheduler():
    """在 FastAPI startup 事件中调用，启动所有后台任务"""
    global _running, _scheduler_task, _event_monitor_task
    if _running:
        logger.warning("[社区调度器] 已在运行，跳过重复启动")
        return

    _running = True
    _scheduler_task = asyncio.create_task(_scheduled_post_loop())
    _event_monitor_task = asyncio.create_task(_event_monitor_loop())
    logger.info("[社区调度器] 已启动（定时发帖 + 事件监控）")


def stop_scheduler():
    """在 FastAPI shutdown 事件中调用，优雅停止"""
    global _running
    _running = False
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
    if _event_monitor_task and not _event_monitor_task.done():
        _event_monitor_task.cancel()
    logger.info("[社区调度器] 已停止")
