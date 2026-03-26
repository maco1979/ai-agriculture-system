"""
任务提案生成服务
─────────────────────────────────────────────────────────
功能：
  1. 分析 AI 讨论内容，识别可执行的任务
  2. 生成结构化任务提案（包含执行参数、预期效果、风险评估）
  3. 将提案存储到数据库，等待用户审批
  4. 审批通过后，自动执行任务

调用时机：
  - AI 讨论完成后，community_dialogue.py 调用
  - 用户手动触发提案生成
"""

import sqlite3
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

from src.services.community_db import get_conn, _validate_input
from src.core.services.cloud_ai_service import chat_completion

logger = logging.getLogger(__name__)


class ProposalStatus(Enum):
    PENDING = "pending"        # 等待审批
    APPROVED = "approved"      # 已批准
    REJECTED = "rejected"      # 已拒绝
    EXECUTING = "executing"    # 执行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 执行失败


class TaskType(Enum):
    IRRIGATION = "irrigation"          # 灌溉
    FERTILIZATION = "fertilization"    # 施肥
    PEST_CONTROL = "pest_control"      # 病虫害防治
    PRUNING = "pruning"                # 修剪
    HARVEST = "harvest"                # 收获
    MONITORING = "monitoring"          # 监测
    ALERT = "alert"                    # 预警


@dataclass
class TaskProposal:
    """任务提案数据结构"""
    proposal_id: str
    post_id: int
    title: str
    description: str
    task_type: TaskType
    parameters: Dict[str, Any]      # 执行参数
    expected_outcome: str           # 预期效果
    risk_level: str                 # 风险等级: low/medium/high
    estimated_duration: int         # 预计耗时(分钟)
    created_at: datetime
    status: ProposalStatus
    approved_by: Optional[str]      # 审批人
    approved_at: Optional[datetime]
    executed_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[str]           # 执行结果
    wechat_pushed: bool = False     # 是否已推送微信
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "post_id": self.post_id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type.value,
            "parameters": self.parameters,
            "expected_outcome": self.expected_outcome,
            "risk_level": self.risk_level,
            "estimated_duration": self.estimated_duration,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "wechat_pushed": self.wechat_pushed,
        }


# ── 任务类型识别关键词 ──────────────────────────────────────
TASK_KEYWORDS = {
    TaskType.IRRIGATION: ["灌溉", "浇水", "湿度", "干旱", "缺水", "水分"],
    TaskType.FERTILIZATION: ["施肥", "肥料", "营养", "追肥", "氮", "磷", "钾"],
    TaskType.PEST_CONTROL: ["病虫害", "防治", "农药", "杀虫", "杀菌", "蚜虫", "病害"],
    TaskType.PRUNING: ["修剪", "整枝", "打顶", "摘心", "疏果"],
    TaskType.HARVEST: ["收获", "采摘", "收割", "成熟", "采收"],
    TaskType.MONITORING: ["监测", "观察", "检查", "巡查", "检测"],
    TaskType.ALERT: ["预警", "警报", "注意", "提醒", "警告"],
}

# ── 核心函数 ──────────────────────────────────────────────

def _build_discussion_context(post_id: int) -> str:
    """构建帖子+讨论上下文"""
    from src.services.community_db import get_post
    
    post = get_post(post_id)
    if not post:
        return ""
    
    lines = [
        f"帖子标题: {post.get('title', '')}",
        f"帖子内容: {post.get('content', '')}",
        "\n讨论内容:",
    ]
    
    replies = post.get("replies", [])
    for i, reply in enumerate(replies[-8:], 1):  # 最近8条
        lines.append(f"{i}. {reply.get('user', '未知')}: {reply.get('content', '')}")
    
    return "\n".join(lines)


def _identify_task_type(text: str) -> TaskType:
    """识别任务类型"""
    text_lower = text.lower()
    scores = {task_type: 0 for task_type in TaskType}
    
    for task_type, keywords in TASK_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                scores[task_type] += 1
    
    # 返回得分最高的任务类型，默认为监测
    return max(scores, key=scores.get, default=TaskType.MONITORING)


async def _generate_proposal_with_ai(post_id: int, context: str) -> Optional[Dict[str, Any]]:
    """调用 AI 分析讨论内容，生成任务提案"""
    
    prompt = f"""
作为农业智能助手，请分析以下社区讨论内容，识别出一个可执行的具体农业任务，并生成详细的任务提案。

{context}

要求：
1. 任务必须是具体、可执行的农业操作（如：灌溉、施肥、病虫害防治等）
2. 提供详细的执行参数（时间、用量、方法等）
3. 说明预期效果和收益
4. 评估风险等级（low/medium/high）
5. 预计完成时间（分钟）

请按以下 JSON 格式输出：
```json
{{
  "title": "任务标题",
  "description": "任务详细描述",
  "task_type": "irrigation|fertilization|pest_control|pruning|harvest|monitoring|alert",
  "parameters": {{
    "location": "执行位置",
    "timing": "执行时间",
    "dosage": "用量/剂量",
    "method": "执行方法",
    "notes": "备注说明"
  }},
  "expected_outcome": "预期效果和收益",
  "risk_level": "low|medium|high",
  "estimated_duration": 120
}}
```

如果讨论内容不足以生成具体任务，请输出: [NO_TASK]
"""
    
    result = await chat_completion(
        prompt=prompt,
        system_prompt="你是一个专业的农业任务规划助手，擅长从讨论中提取可执行的任务并生成详细的执行方案。只输出 JSON 或 [NO_TASK]，不要有任何额外说明。",
        temperature=0.3,
        max_tokens=800,
    )
    
    if not result.get("success"):
        logger.warning(f"AI 生成提案失败: {result.get('error', '')}")
        return None
    
    content = result.get("content", "").strip()
    
    if "[NO_TASK]" in content:
        logger.info(f"帖子#{post_id} 经AI分析，暂无可执行任务")
        return None
    
    # 提取 JSON
    try:
        # 移除可能的 markdown 代码块标记
        json_str = re.sub(r"```json\n?|\n?```", "", content).strip()
        proposal_data = json.loads(json_str)
        
        # 验证必要字段
        required_fields = ["title", "description", "task_type", "parameters", "expected_outcome", "risk_level", "estimated_duration"]
        for field in required_fields:
            if field not in proposal_data:
                logger.warning(f"AI 生成的提案缺少必要字段: {field}")
                return None
        
        return proposal_data
    except json.JSONDecodeError as e:
        logger.warning(f"解析 AI 生成的 JSON 失败: {e}\n内容: {content}")
        return None


def init_task_proposal_db():
    """初始化任务提案数据库表"""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS task_proposals (
                proposal_id     TEXT PRIMARY KEY,
                post_id         INTEGER NOT NULL,
                title           TEXT NOT NULL,
                description     TEXT NOT NULL,
                task_type       TEXT NOT NULL,
                parameters      TEXT NOT NULL,  -- JSON
                expected_outcome TEXT NOT NULL,
                risk_level      TEXT NOT NULL,
                estimated_duration INTEGER NOT NULL,
                created_at      TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'pending',
                approved_by     TEXT,
                approved_at     TEXT,
                executed_at     TEXT,
                completed_at    TEXT,
                result          TEXT,
                wechat_pushed   INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_task_proposals_post ON task_proposals(post_id);
            CREATE INDEX IF NOT EXISTS idx_task_proposals_status ON task_proposals(status);
            CREATE INDEX IF NOT EXISTS idx_task_proposals_created ON task_proposals(created_at);
        """)
    logger.info("任务提案数据库表初始化完成")


async def generate_task_proposal(post_id: int) -> Optional[TaskProposal]:
    """
    为指定帖子生成任务提案
    
    Args:
        post_id: 帖子ID
        
    Returns:
        生成的提案对象，如果无法生成则返回 None
    """
    # 检查是否已存在提案
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT proposal_id FROM task_proposals WHERE post_id = ? AND status != 'rejected'",
            (post_id,)
        ).fetchone()
        if existing:
            logger.info(f"帖子#{post_id} 已存在提案 {existing['proposal_id']}，跳过生成")
            return None
    
    # 构建讨论上下文
    context = _build_discussion_context(post_id)
    if not context:
        logger.warning(f"无法获取帖子#{post_id}的上下文")
        return None
    
    # 调用 AI 生成提案
    proposal_data = await _generate_proposal_with_ai(post_id, context)
    if not proposal_data:
        return None
    
    # 识别任务类型
    task_type = _identify_task_type(
        proposal_data["title"] + " " + proposal_data["description"]
    )
    
    # 创建提案对象
    proposal = TaskProposal(
        proposal_id=str(uuid.uuid4()),
        post_id=post_id,
        title=_validate_input(proposal_data["title"], 200, "title"),
        description=_validate_input(proposal_data["description"], 2000, "description"),
        task_type=task_type,
        parameters=proposal_data["parameters"],
        expected_outcome=proposal_data["expected_outcome"],
        risk_level=proposal_data["risk_level"],
        estimated_duration=int(proposal_data["estimated_duration"]),
        created_at=datetime.now(),
        status=ProposalStatus.PENDING,
        approved_by=None,
        approved_at=None,
        executed_at=None,
        completed_at=None,
        result=None,
        wechat_pushed=False,
    )
    
    # 保存到数据库
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO task_proposals 
            (proposal_id, post_id, title, description, task_type, parameters,
             expected_outcome, risk_level, estimated_duration, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proposal.proposal_id,
            proposal.post_id,
            proposal.title,
            proposal.description,
            proposal.task_type.value,
            json.dumps(proposal.parameters, ensure_ascii=False),
            proposal.expected_outcome,
            proposal.risk_level,
            proposal.estimated_duration,
            proposal.created_at.isoformat(),
            proposal.status.value,
        ))
    
    logger.info(f"✅ 为帖子#{post_id} 生成任务提案: {proposal.title} (ID: {proposal.proposal_id})")
    return proposal


def get_pending_proposals(limit: int = 20) -> List[Dict[str, Any]]:
    """获取待审批的任务提案列表"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM task_proposals 
            WHERE status = 'pending' 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,)).fetchall()
        
        proposals = []
        for row in rows:
            proposal = dict(row)
            proposal["parameters"] = json.loads(proposal["parameters"])
            proposals.append(proposal)
        
        return proposals


def get_proposal(proposal_id: str) -> Optional[Dict[str, Any]]:
    """获取单个提案详情"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM task_proposals WHERE proposal_id = ?",
            (proposal_id,)
        ).fetchone()
        if not row:
            return None
        
        proposal = dict(row)
        proposal["parameters"] = json.loads(proposal["parameters"])
        return proposal


async def approve_proposal(proposal_id: str, approved_by: str) -> bool:
    """
    审批任务提案
    
    Args:
        proposal_id: 提案ID
        approved_by: 审批人（用户ID或名称）
        
    Returns:
        是否成功
    """
    with get_conn() as conn:
        result = conn.execute("""
            UPDATE task_proposals 
            SET status = 'approved', approved_by = ?, approved_at = ?
            WHERE proposal_id = ? AND status = 'pending'
        """, (approved_by, datetime.now().isoformat(), proposal_id))
        
        if result.rowcount == 0:
            logger.warning(f"提案 {proposal_id} 审批失败，可能不存在或状态不是 pending")
            return False
    
    logger.info(f"✅ 提案 {proposal_id} 已被 {approved_by} 批准")
    
    # 触发任务执行（异步）
    asyncio.create_task(_execute_task_after_approval(proposal_id))
    
    return True


async def reject_proposal(proposal_id: str, rejected_by: str, reason: str = "") -> bool:
    """拒绝任务提案"""
    with get_conn() as conn:
        result = conn.execute("""
            UPDATE task_proposals 
            SET status = 'rejected', result = ?
            WHERE proposal_id = ? AND status = 'pending'
        """, (reason, proposal_id))
        
        if result.rowcount == 0:
            return False
    
    logger.info(f"❌ 提案 {proposal_id} 已被 {rejected_by} 拒绝: {reason}")
    return True


async def _execute_task_after_approval(proposal_id: str):
    """批准后执行任务（异步）"""
    await asyncio.sleep(2)  # 短暂延迟，模拟准备时间
    
    proposal = get_proposal(proposal_id)
    if not proposal:
        logger.error(f"执行任务失败，提案 {proposal_id} 不存在")
        return
    
    # 更新状态为执行中
    with get_conn() as conn:
        conn.execute("""
            UPDATE task_proposals 
            SET status = 'executing', executed_at = ?
            WHERE proposal_id = ?
        """, (datetime.now().isoformat(), proposal_id))
    
    logger.info(f"🚀 开始执行任务: {proposal['title']}")
    
    # 模拟任务执行
    try:
        # 根据任务类型调用相应的执行函数
        task_type = TaskType(proposal['task_type'])
        parameters = proposal['parameters']
        
        # 这里调用实际的执行逻辑（ irrigation, fertilization 等）
        result = await _simulate_task_execution(task_type, parameters)
        
        # 更新为完成状态
        with get_conn() as conn:
            conn.execute("""
                UPDATE task_proposals 
                SET status = 'completed', completed_at = ?, result = ?
                WHERE proposal_id = ?
            """, (datetime.now().isoformat(), result, proposal_id))
        
        logger.info(f"✅ 任务 {proposal_id} 执行完成: {result}")
        
    except Exception as e:
        logger.error(f"任务 {proposal_id} 执行失败: {e}")
        
        # 更新为失败状态
        with get_conn() as conn:
            conn.execute("""
                UPDATE task_proposals 
                SET status = 'failed', result = ?
                WHERE proposal_id = ?
            """, (str(e), proposal_id))


async def _simulate_task_execution(task_type: TaskType, parameters: Dict[str, Any]) -> str:
    """模拟任务执行（实际项目中替换为真实执行逻辑）"""
    
    # 模拟执行时间
    await asyncio.sleep(3)
    
    # 根据任务类型返回模拟结果
    if task_type == TaskType.IRRIGATION:
        location = parameters.get("location", "未知区域")
        duration = parameters.get("duration", 30)
        return f"灌溉完成：{location} 区域已灌溉 {duration} 分钟"
    
    elif task_type == TaskType.FERTILIZATION:
        location = parameters.get("location", "未知区域")
        dosage = parameters.get("dosage", "标准剂量")
        return f"施肥完成：{location} 区域已施用 {dosage}"
    
    elif task_type == TaskType.PEST_CONTROL:
        pest_type = parameters.get("pest_type", "病虫害")
        method = parameters.get("method", "防治")
        return f"防治完成：{pest_type} 已进行 {method}"
    
    elif task_type == TaskType.PRUNING:
        location = parameters.get("location", "未知区域")
        return f"修剪完成：{location} 区域已完成修剪作业"
    
    elif task_type == TaskType.HARVEST:
        crop = parameters.get("crop", "作物")
        return f"收获完成：{crop} 已收获并存储"
    
    elif task_type == TaskType.MONITORING:
        target = parameters.get("target", "监测目标")
        return f"监测完成：{target} 状态正常"
    
    elif task_type == TaskType.ALERT:
        message = parameters.get("message", "预警信息")
        return f"预警已发送：{message}"
    
    return f"任务执行完成：{task_type.value}"


# 自动初始化数据库表
init_task_proposal_db()
