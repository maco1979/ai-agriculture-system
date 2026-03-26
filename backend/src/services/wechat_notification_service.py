"""
微信通知服务
─────────────────────────────────────────────────────────
功能：
  1. 推送任务提案到微信（支持小程序和ClawBot）
  2. 发送执行结果通知
  3. 支持模板消息和订阅消息
  4. 管理用户订阅关系

配置方式（二选一）：
  1. 微信小程序模式（传统方式）：
     - 需要配置 AppID、AppSecret
     - 需要在微信公众平台申请模板消息

  2. ClawBot 集成模式（推荐）：
     - 无需申请凭证
     - 扫码即可绑定
     - 通过 Webhook 发送消息
     - 支持双向交互
"""

import logging
import sqlite3
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio
import os

from src.services.community_db import get_conn, _validate_input

logger = logging.getLogger(__name__)

# ── 配置 ────────────────────────────────────────────────────

# 使用模式选择
# True = 使用 ClawBot 集成（推荐）
# False = 使用传统微信小程序
USE_CLAW_BOT = os.getenv("USE_CLAW_BOT", "true").lower() == "true"

# ClawBot Webhook 配置（WorkBuddy自动生成）
CLAW_BOT_CONFIG = {
    "webhook_url": os.getenv("CLAW_BOT_WEBHOOK", "http://localhost:5678/webhook/wechat"),
    "timeout": 10.0,
}

# 微信小程序配置（传统方式，备用）
WECHAT_CONFIG = {
    "appid": os.getenv("WECHAT_APPID", "YOUR_WECHAT_APPID_HERE"),
    "appsecret": os.getenv("WECHAT_APPSECRET", "YOUR_WECHAT_APPSECRET"),
    "template_id": os.getenv("WECHAT_TEMPLATE_ID", "YOUR_TEMPLATE_ID"),
}

# 微信 API 接口
WECHAT_API = {
    "get_access_token": "https://api.weixin.qq.com/cgi-bin/token",
    "send_template_msg": "https://api.weixin.qq.com/cgi-bin/message/subscribe/send",
}


@dataclass
class WechatUser:
    """微信用户信息"""
    openid: str
    session_key: str
    subscribed: bool = True
    created_at: datetime = None
    last_active: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_active is None:
            self.last_active = datetime.now()


# ── 数据库初始化 ───────────────────────────────────────────

def init_wechat_db():
    """初始化微信相关数据库表"""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS wechat_users (
                openid          TEXT PRIMARY KEY,
                session_key     TEXT,
                subscribed      INTEGER NOT NULL DEFAULT 1,
                created_at      TEXT NOT NULL,
                last_active     TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS wechat_notifications (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                openid          TEXT NOT NULL,
                template_id     TEXT NOT NULL,
                data            TEXT NOT NULL,  -- JSON
                status          TEXT NOT NULL DEFAULT 'pending',  -- pending/sent/failed
                sent_at         TEXT,
                error_msg       TEXT,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (openid) REFERENCES wechat_users(openid) ON DELETE CASCADE
            );
            
            CREATE INDEX IF NOT EXISTS idx_wechat_users_active ON wechat_users(subscribed, last_active);
            CREATE INDEX IF NOT EXISTS idx_wechat_notifications_status ON wechat_notifications(status, created_at);
        """)
    logger.info("微信通知数据库表初始化完成")


# ── Access Token 管理 ────────────────────────────────────

class AccessTokenManager:
    """管理微信 access token"""
    
    def __init__(self):
        self._access_token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def get_access_token(self) -> Optional[str]:
        """获取有效的 access token"""
        async with self._lock:
            # 检查是否有有效的 token
            if self._access_token and self._expires_at and datetime.now() < self._expires_at:
                return self._access_token
            
            # 重新获取 token
            return await self._refresh_access_token()
    
    async def _refresh_access_token(self) -> Optional[str]:
        """从微信 API 获取新的 access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    WECHAT_API["get_access_token"],
                    params={
                        "grant_type": "client_credential",
                        "appid": WECHAT_CONFIG["appid"],
                        "secret": WECHAT_CONFIG["appsecret"],
                    },
                    timeout=10.0,
                )
                
                data = response.json()
                if "access_token" in data:
                    self._access_token = data["access_token"]
                    # token 有效期 7200 秒，提前 5 分钟过期
                    self._expires_at = datetime.now() + timedelta(seconds=7000)
                    logger.info("微信 access token 获取成功")
                    return self._access_token
                else:
                    logger.error(f"获取 access token 失败: {data}")
                    return None
        except Exception as e:
            logger.error(f"获取 access token 异常: {e}")
            return None


# 全局 token 管理器
_token_manager = AccessTokenManager()


# ── 核心功能 ───────────────────────────────────────────────

async def send_task_proposal_notification(
    openid: str,
    proposal_title: str,
    proposal_desc: str,
    task_type: str,
    risk_level: str,
    proposal_id: Optional[str] = None,
) -> bool:
    """
    发送任务提案通知到微信
    
    支持两种模式：
    1. ClawBot模式：通过Webhook发送富文本消息
    2. 小程序模式：发送模板消息（备用）
    
    Args:
        openid: 用户 openid/微信昵称
        proposal_title: 提案标题
        proposal_desc: 提案描述
        task_type: 任务类型
        risk_level: 风险等级
        proposal_id: 提案ID（用于详情查看）
        
    Returns:
        是否发送成功
    """
    
    # ClawBot 模式（推荐）
    if USE_CLAW_BOT:
        return await _send_clawbot_message(
            recipient=openid,
            message_type="task_proposal",
            title=proposal_title,
            description=proposal_desc,
            task_type=task_type,
            risk_level=risk_level,
            proposal_id=proposal_id,
        )
    
    # 传统小程序模式（备用）
    else:
        # 检查用户是否订阅
        if not await check_user_subscribed(openid):
            logger.warning(f"用户 {openid} 未订阅消息，跳过发送")
            return False
        
        # 准备模板消息数据
        template_data = {
            "thing1": {"value": proposal_title[:20]},  # 提案名称，最多20字符
            "thing2": {"value": proposal_desc[:20]},   # 提案描述，最多20字符
            "thing3": {"value": task_type[:20]},       # 任务类型
            "thing4": {"value": risk_level[:20]},      # 风险等级
            "thing5": {"value": datetime.now().strftime("%Y-%m-%d %H:%M")},  # 生成时间
        }
        
        # 发送消息
        return await _send_template_message(
            openid=openid,
            template_id=WECHAT_CONFIG["template_id"],
            data=template_data,
            page_path=f"pages/proposals/proposal-detail?openid={openid}",
        )


async def send_task_result_notification(
    openid: str,
    task_title: str,
    result: str,
    status: str,
) -> bool:
    """
    发送任务执行结果通知
    
    Args:
        openid: 用户 openid/微信昵称
        task_title: 任务标题
        result: 执行结果
        status: 执行状态
        
    Returns:
        是否发送成功
    """
    
    # ClawBot 模式（推荐）
    if USE_CLAW_BOT:
        return await _send_clawbot_message(
            recipient=openid,
            message_type="task_result",
            title=task_title,
            result=result,
            status=status,
        )
    
    # 传统小程序模式（备用）
    else:
        if not await check_user_subscribed(openid):
            return False
        
        # 准备模板消息数据
        template_data = {
            "thing1": {"value": task_title[:20]},      # 任务名称
            "thing2": {"value": status[:20]},          # 执行状态
            "thing3": {"value": result[:20]},          # 执行结果
            "thing4": {"value": datetime.now().strftime("%Y-%m-%d %H:%M")},  # 完成时间
            "thing5": {"value": "点击查看详情"},        # 备注
        }
        
        return await _send_template_message(
            openid=openid,
            template_id=WECHAT_CONFIG["template_id"],
            data=template_data,
            page_path="pages/tasks/task-history",
        )


async def _send_clawbot_message(
    recipient: str,
    message_type: str,
    **kwargs
) -> bool:
    """
    通过 ClawBot Webhook 发送消息
    
    Args:
        recipient: 接收人（微信昵称或openid）
        message_type: 消息类型
        **kwargs: 消息内容
        
    Returns:
        是否发送成功
    """
    
    # 构建富文本消息
    if message_type == "task_proposal":
        message = _build_proposal_message(
            title=kwargs.get("title", ""),
            description=kwargs.get("description", ""),
            task_type=kwargs.get("task_type", ""),
            risk_level=kwargs.get("risk_level", ""),
            proposal_id=kwargs.get("proposal_id", ""),
        )
    elif message_type == "task_result":
        message = _build_result_message(
            title=kwargs.get("title", ""),
            result=kwargs.get("result", ""),
            status=kwargs.get("status", ""),
        )
    else:
        message = str(kwargs)
    
    # 准备消息体
    message_body = {
        "recipient": recipient,
        "message": message,
        "type": message_type,
        "timestamp": datetime.now().isoformat(),
    }
    
    # 添加元数据
    if kwargs.get("proposal_id"):
        message_body["proposal_id"] = kwargs["proposal_id"]
    
    try:
        # 发送到 ClawBot Webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                CLAW_BOT_CONFIG["webhook_url"],
                json=message_body,
                timeout=CLAW_BOT_CONFIG["timeout"],
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"ClawBot消息发送成功: recipient={recipient}")
                    return True
                else:
                    logger.error(f"ClawBot消息发送失败: {result.get('error', '未知错误')}")
                    return False
            else:
                logger.error(f"ClawBot Webhook 响应异常: HTTP {response.status_code}")
                return False
    
    except Exception as e:
        logger.error(f"发送ClawBot消息异常: {e}")
        return False


def _build_proposal_message(
    title: str,
    description: str,
    task_type: str,
    risk_level: str,
    proposal_id: Optional[str] = None,
) -> str:
    """构建任务提案消息"""
    
    risk_emoji = {
        "low": "✅",
        "medium": "⚠️",
        "high": "❌",
    }.get(risk_level, "⚪")
    
    message = f"""🌾 AI农业决策系统

📋 新任务提案
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 {title}

🏷️ 任务类型：{task_type}
{risk_emoji} 风险等级：{risk_level}

💡 {description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
回复以下指令：
👉 "批准" - 立即执行此任务
👉 "拒绝" - 取消此任务
👉 "详情" - 查看完整信息
"""
    
    if proposal_id:
        message += f"\n📎 提案ID：{proposal_id[:8]}"
    
    return message


def _build_result_message(
    title: str,
    result: str,
    status: str,
) -> str:
    """构建任务结果消息"""
    
    status_emoji = {
        "completed": "✅",
        "executing": "🚀",
        "failed": "❌",
        "pending": "⏳",
    }.get(status, "⚪")
    
    return f"""🌾 AI农业决策系统

📊 任务执行结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{status_emoji} {title}

📈 执行结果：{result}

⏰ 完成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
回复：
👉 "历史" - 查看任务历史
👉 "统计" - 查看今日统计
"""


async def _send_template_message(
    openid: str,
    template_id: str,
    data: Dict[str, Any],
    page_path: str = "",
) -> bool:
    """
    发送模板消息（传统小程序模式，备用）
    
    Args:
        openid: 用户 openid
        template_id: 模板ID
        data: 模板数据
        page_path: 跳转页面
        
    Returns:
        是否发送成功
    """
    
    # 获取 access token
    access_token = await _token_manager.get_access_token()
    if not access_token:
        logger.error("无法获取 access token，消息发送失败")
        return False
    
    # 准备消息体
    message_body = {
        "touser": openid,
        "template_id": template_id,
        "data": data,
    }
    
    if page_path:
        message_body["page"] = page_path
    
    # 记录到数据库（用于重试和日志）
    with get_conn() as conn:
        cursor = conn.execute("""
            INSERT INTO wechat_notifications 
            (openid, template_id, data, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        """, (
            openid,
            template_id,
            json.dumps(data, ensure_ascii=False),
            datetime.now().isoformat(),
        ))
        notification_id = cursor.lastrowid
    
    try:
        # 发送到微信 API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WECHAT_API["send_template_msg"],
                params={"access_token": access_token},
                json=message_body,
                timeout=10.0,
            )
            
            result = response.json()
            
            if result.get("errcode") == 0:
                # 发送成功
                with get_conn() as conn:
                    conn.execute("""
                        UPDATE wechat_notifications 
                        SET status = 'sent', sent_at = ?
                        WHERE id = ?
                    """, (datetime.now().isoformat(), notification_id))
                
                logger.info(f"微信消息发送成功: openid={openid}")
                return True
            else:
                # 发送失败
                error_msg = result.get("errmsg", "未知错误")
                with get_conn() as conn:
                    conn.execute("""
                        UPDATE wechat_notifications 
                        SET status = 'failed', error_msg = ?
                        WHERE id = ?
                    """, (error_msg, notification_id))
                
                logger.error(f"微信消息发送失败: {error_msg}")
                return False
    
    except Exception as e:
        logger.error(f"发送微信消息异常: {e}")
        # 更新为失败状态
        with get_conn() as conn:
            conn.execute("""
                UPDATE wechat_notifications 
                SET status = 'failed', error_msg = ?
                WHERE id = ?
            """, (str(e), notification_id))
        return False


# ── 用户管理 ───────────────────────────────────────────────

def save_wechat_user(openid: str, session_key: str) -> bool:
    """保存微信用户信息"""
    try:
        with get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO wechat_users 
                (openid, session_key, subscribed, created_at, last_active)
                VALUES (?, ?, 1, ?, ?)
            """, (
                openid,
                session_key,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ))
        logger.info(f"微信用户信息保存成功: {openid}")
        return True
    except Exception as e:
        logger.error(f"保存微信用户信息失败: {e}")
        return False


def check_user_subscribed(openid: str) -> bool:
    """检查用户是否订阅消息"""
    try:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT subscribed FROM wechat_users WHERE openid = ?",
                (openid,)
            ).fetchone()
            return row and bool(row["subscribed"])
    except Exception:
        return False


def update_user_subscription(openid: str, subscribed: bool) -> bool:
    """更新用户订阅状态"""
    try:
        with get_conn() as conn:
            result = conn.execute("""
                UPDATE wechat_users 
                SET subscribed = ?, last_active = ?
                WHERE openid = ?
            """, (1 if subscribed else 0, datetime.now().isoformat(), openid))
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"更新用户订阅状态失败: {e}")
        return False


def get_subscribed_users(limit: int = 100) -> List[str]:
    """获取所有订阅用户的 openid"""
    try:
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT openid FROM wechat_users 
                WHERE subscribed = 1 
                ORDER BY last_active DESC 
                LIMIT ?
            """, (limit,)).fetchall()
            return [row["openid"] for row in rows]
    except Exception as e:
        logger.error(f"获取订阅用户列表失败: {e}")
        return []


# ── 通知历史查询 ───────────────────────────────────────────

def get_notification_history(
    openid: str,
    limit: int = 20,
    status: str = None,
) -> List[Dict[str, Any]]:
    """获取用户的通知历史"""
    try:
        with get_conn() as conn:
            if status:
                rows = conn.execute("""
                    SELECT * FROM wechat_notifications 
                    WHERE openid = ? AND status = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (openid, status, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM wechat_notifications 
                    WHERE openid = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (openid, limit)).fetchall()
            
            notifications = []
            for row in rows:
                notification = dict(row)
                notification["data"] = json.loads(notification["data"])
                notifications.append(notification)
            
            return notifications
    except Exception as e:
        logger.error(f"获取通知历史失败: {e}")
        return []


# ── 自动初始化 ─────────────────────────────────────────────

init_wechat_db()


# ── ClawBot 快速测试 ─────────────────────────────────────

async def test_clawbot_connection():
    """测试 ClawBot 连接"""
    logger.info("测试 ClawBot 连接...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                CLAW_BOT_CONFIG["webhook_url"].replace("/wechat", "/health"),
                timeout=3.0,
            )
            
            if response.status_code == 200:
                logger.info("✅ ClawBot 连接正常")
                return True
            else:
                logger.warning(f"⚠️  ClawBot 响应异常: HTTP {response.status_code}")
                return False
    except Exception as e:
        logger.warning(f"⚠️  ClawBot 连接失败: {e}")
        logger.info("💡 请确保 WorkBuddy 已启动并登录")
        return False


async def send_test_message_to_wechat(recipient: str = None):
    """
    发送测试消息到微信
    
    Args:
        recipient: 接收人（微信昵称），如果为None则使用配置中的默认用户
    """
    if not recipient:
        # 从数据库获取第一个订阅用户
        users = get_subscribed_users(limit=1)
        if not users:
            logger.warning("没有订阅用户，请先绑定微信账号")
            return False
        recipient = users[0]
    
    logger.info(f"发送测试消息到: {recipient}")
    
    # 发送测试提案
    success = await send_task_proposal_notification(
        openid=recipient,
        proposal_title="🧪 系统测试任务",
        proposal_desc="这是一条测试消息，验证微信集成是否正常工作",
        task_type="测试",
        risk_level="low",
        proposal_id="test-001",
    )
    
    if success:
        logger.info("✅ 测试消息已发送到微信，请检查是否收到")
    else:
        logger.error("❌ 测试消息发送失败")
    
    return success


# ── 命令行测试 ───────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("🌾 AI农业决策系统 - 微信通知服务测试")
        print("=" * 60)
        
        # 检查当前模式
        mode = "ClawBot" if USE_CLAW_BOT else "微信小程序"
        print(f"当前模式: {mode}")
        print("=" * 60)
        
        if USE_CLAW_BOT:
            # 测试 ClawBot 连接
            print("\n🔌 测试 ClawBot 连接...")
            await test_clawbot_connection()
            
            # 发送测试消息
            print("\n📤 发送测试消息...")
            await send_test_message_to_wechat()
            
            print("\n💡 提示:")
            print("   - 确保 WorkBuddy 已启动")
            print("   - 确保已绑定微信账号")
            print("   - 检查微信是否收到测试消息")
        else:
            print("\n💡 当前使用传统小程序模式")
            print("请确保已配置：")
            print("  - WECHAT_APPID")
            print("  - WECHAT_APPSECRET")
            print("  - WECHAT_TEMPLATE_ID")
            print("\n然后运行测试函数：")
            print("  python -m src.services.wechat_notification_service")
        
        print("\n✅ 测试完成")
    
    asyncio.run(main())
