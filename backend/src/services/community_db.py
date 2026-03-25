"""
社区 SQLite 数据库服务
帖子、回复持久化存储，重启后数据不丢失
"""

import sqlite3
import os
import json
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# 输入验证常量
MAX_SEARCH_LENGTH = 100
MAX_TITLE_LENGTH = 200
MAX_CONTENT_LENGTH = 10000
MAX_USER_LENGTH = 50

# 数据库文件路径（存放在 backend/data/ 目录）
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "community.db"


def get_conn() -> sqlite3.Connection:
    """获取数据库连接，Row 模式方便转 dict"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """初始化表结构（幂等）"""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS posts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user        TEXT    NOT NULL DEFAULT '匿名用户',
                avatar      TEXT    NOT NULL DEFAULT '',
                title       TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                category    TEXT    NOT NULL DEFAULT '种植经验',
                tags        TEXT    NOT NULL DEFAULT '[]',   -- JSON array
                likes       INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS replies (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id     INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                user        TEXT    NOT NULL DEFAULT '匿名用户',
                avatar      TEXT    NOT NULL DEFAULT '',
                content     TEXT    NOT NULL,
                likes       INTEGER NOT NULL DEFAULT 0,
                is_ai       INTEGER NOT NULL DEFAULT 0,   -- 1 = AI 角色回复
                ai_role_id  TEXT,                         -- AI 角色 ID
                created_at  TEXT    NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_replies_post ON replies(post_id);
        """)
    _seed_demo_posts()


# ────────────────────────────── 帖子 CRUD ──────────────────────────────

def _validate_input(text: str, max_length: int, field_name: str) -> str:
    """验证并清理输入文本"""
    if not text:
        return text
    # 截断超长内容
    if len(text) > max_length:
        text = text[:max_length]
    # 移除潜在危险的控制字符
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
    return text


def create_post(user: str, avatar: str, title: str, content: str,
                category: str, tags: List[str]) -> Dict[str, Any]:
    # 输入验证
    user = _validate_input(user, MAX_USER_LENGTH, "user")
    title = _validate_input(title, MAX_TITLE_LENGTH, "title")
    content = _validate_input(content, MAX_CONTENT_LENGTH, "content")
    category = _validate_input(category, 50, "category")
    # 验证标签
    if tags:
        tags = [t[:30] for t in tags[:10]]  # 最多10个标签，每个最多30字符

    with get_conn() as conn:
        now = datetime.now().isoformat()
        cur = conn.execute(
            "INSERT INTO posts(user,avatar,title,content,category,tags,created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (user, avatar, title, content, category, json.dumps(tags, ensure_ascii=False), now)
        )
        return get_post(cur.lastrowid)


def get_post(post_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
        if not row:
            return None
        return _row_to_post(dict(row), conn)


def list_posts(category: Optional[str] = None,
               search: Optional[str] = None) -> List[Dict[str, Any]]:
    # 验证并限制搜索参数
    if search:
        search = _validate_input(search, MAX_SEARCH_LENGTH, "search")
        # 移除可能导致性能问题的通配符
        search = search.replace('%', '').replace('_', '')
    if category:
        category = _validate_input(category, 50, "category")

    with get_conn() as conn:
        sql = "SELECT * FROM posts WHERE 1=1"
        params: list = []
        if category:
            sql += " AND category=?"
            params.append(category)
        if search:
            sql += " AND (title LIKE ? OR content LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        sql += " ORDER BY id DESC"
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_post(dict(r), conn) for r in rows]


def like_post(post_id: int) -> int:
    with get_conn() as conn:
        conn.execute("UPDATE posts SET likes=likes+1 WHERE id=?", (post_id,))
        row = conn.execute("SELECT likes FROM posts WHERE id=?", (post_id,)).fetchone()
        return row["likes"] if row else 0


# ────────────────────────────── 回复 CRUD ──────────────────────────────

def create_reply(post_id: int, user: str, avatar: str, content: str,
                 is_ai: bool = False, ai_role_id: Optional[str] = None) -> Dict[str, Any]:
    # 输入验证
    user = _validate_input(user, MAX_USER_LENGTH, "user")
    content = _validate_input(content, MAX_CONTENT_LENGTH, "content")
    if ai_role_id:
        ai_role_id = _validate_input(ai_role_id, 50, "ai_role_id")

    with get_conn() as conn:
        now = datetime.now().isoformat()
        cur = conn.execute(
            "INSERT INTO replies(post_id,user,avatar,content,is_ai,ai_role_id,created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (post_id, user, avatar, content, 1 if is_ai else 0, ai_role_id, now)
        )
        row = conn.execute("SELECT * FROM replies WHERE id=?", (cur.lastrowid,)).fetchone()
        return _row_to_reply(dict(row))


def list_replies(post_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM replies WHERE post_id=? ORDER BY id ASC", (post_id,)
        ).fetchall()
        return [_row_to_reply(dict(r)) for r in rows]


def like_reply(reply_id: int) -> int:
    with get_conn() as conn:
        conn.execute("UPDATE replies SET likes=likes+1 WHERE id=?", (reply_id,))
        row = conn.execute("SELECT likes FROM replies WHERE id=?", (reply_id,)).fetchone()
        return row["likes"] if row else 0


# ────────────────────────────── 内部工具 ──────────────────────────────

def _row_to_post(row: dict, conn: sqlite3.Connection) -> Dict[str, Any]:
    row["tags"] = json.loads(row.get("tags") or "[]")
    row["liked"] = False
    replies = conn.execute(
        "SELECT * FROM replies WHERE post_id=? ORDER BY id ASC", (row["id"],)
    ).fetchall()
    row["replies"] = [_row_to_reply(dict(r)) for r in replies]
    # 相对时间
    row["time"] = _relative_time(row["created_at"])
    return row


def _row_to_reply(row: dict) -> Dict[str, Any]:
    row["is_ai"] = bool(row.get("is_ai", 0))
    row["time"] = _relative_time(row["created_at"])
    return row


def _relative_time(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        diff = (datetime.now() - dt).total_seconds()
        if diff < 60:
            return "刚刚"
        if diff < 3600:
            return f"{int(diff/60)}分钟前"
        if diff < 86400:
            return f"{int(diff/3600)}小时前"
        return f"{int(diff/86400)}天前"
    except Exception:
        return iso


def _seed_demo_posts():
    """首次启动写入演示帖子（只在表为空时执行）"""
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        if count > 0:
            return
        demo = [
            ("农业科技达人", "https://ui-avatars.com/api/?name=农业&background=22c55e&color=fff",
             "使用 AI 病虫害诊断功能，帮助我减少了40%的农药使用",
             '今年夏天水稻出现了一种我从来没见过的斑点，上传图片到系统后，AI 几秒就给出了"稻瘟病早期"的诊断，并推荐了低毒防治方案。最终农药用量比去年同期减少了40%，产量反而提升了，强烈推荐大家试试！',
             "种植经验", ["病虫害", "水稻", "AI诊断"]),
            ("区块链开发者", "https://ui-avatars.com/api/?name=开发&background=6366f1&color=fff",
             "项目的区块链溯源模块解析 — 数据如何做到不可篡改",
             "深入研究了一下本项目的区块链集成方案，核心是 Hyperledger Fabric 联盟链，每次农产品流通节点都会上链存证。有兴趣的朋友可以查看 blockchain 模块源码。",
             "AI技术", ["区块链", "溯源", "Hyperledger"]),
            ("新手求助", "https://ui-avatars.com/api/?name=新手&background=ef4444&color=fff",
             "请问 DeepSeek API Key 怎么获取？",
             "刚下载了项目，看 .env.example 里说推荐用 DeepSeek，但不知道去哪里注册申请 API Key，有没有大佬指导一下？@植保顾问",
             "提问求助", ["DeepSeek", "API", "新手"]),
        ]
        now = datetime.now().isoformat()
        for user, avatar, title, content, cat, tags in demo:
            conn.execute(
                "INSERT INTO posts(user,avatar,title,content,category,tags,created_at) VALUES(?,?,?,?,?,?,?)",
                (user, avatar, title, content, cat, json.dumps(tags, ensure_ascii=False), now)
            )
