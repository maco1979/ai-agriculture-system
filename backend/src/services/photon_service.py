"""
PHOTON 奖励服务
联邦学习参与者完成训练后，自动发放 PHOTON 奖励代币
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List

_DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/photon.db")


def _get_db():
    """获取 SQLite 连接，自动建表"""
    os.makedirs(os.path.dirname(os.path.abspath(_DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(os.path.abspath(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS photon_balances (
            user_id     TEXT PRIMARY KEY,
            balance     REAL NOT NULL DEFAULT 0,
            total_earned REAL NOT NULL DEFAULT 0,
            last_updated TEXT
        );
        CREATE TABLE IF NOT EXISTS photon_transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     TEXT NOT NULL,
            amount      REAL NOT NULL,
            reason      TEXT NOT NULL,
            round_id    TEXT,
            created_at  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tx_user ON photon_transactions(user_id);
    """)
    conn.commit()
    return conn


# ── 奖励规则 ─────────────────────────────────────────
REWARD_TRAINING_ROUND = 10.0     # 参与一轮联邦训练
REWARD_UPLOAD_DATA   = 2.0       # 上传一条农业数据
REWARD_HIGH_ACCURACY = 5.0       # 本地训练准确率 > 0.9
REWARD_FIRST_ROUND   = 20.0      # 首次参与奖励


def award_training(user_id: str, round_id: str, accuracy: float = 0.0) -> Dict[str, Any]:
    """
    联邦学习训练轮次完成后发放奖励

    Args:
        user_id:  参与者 ID
        round_id: 训练轮次 ID
        accuracy: 本地模型准确率（0~1）

    Returns:
        {photon_earned, new_balance, total_earned}
    """
    amount = REWARD_TRAINING_ROUND
    reasons = [f"联邦训练 {round_id}"]

    if accuracy > 0.9:
        amount += REWARD_HIGH_ACCURACY
        reasons.append("高精度奖励")

    # 检查是否首次参与
    with _get_db() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) as n FROM photon_transactions WHERE user_id=? AND reason LIKE '联邦训练%'",
            (user_id,),
        ).fetchone()["n"]

        if existing == 0:
            amount += REWARD_FIRST_ROUND
            reasons.append("首次参与奖励")

        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO photon_transactions (user_id, amount, reason, round_id, created_at) VALUES (?,?,?,?,?)",
            (user_id, amount, " + ".join(reasons), round_id, now),
        )

        # 更新余额
        conn.execute(
            """INSERT INTO photon_balances (user_id, balance, total_earned, last_updated)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   balance = balance + excluded.balance,
                   total_earned = total_earned + excluded.total_earned,
                   last_updated = excluded.last_updated""",
            (user_id, amount, amount, now),
        )

        row = conn.execute("SELECT * FROM photon_balances WHERE user_id=?", (user_id,)).fetchone()

    return {
        "photon_earned": amount,
        "new_balance": row["balance"],
        "total_earned": row["total_earned"],
        "reasons": reasons,
        "timestamp": now,
    }


def award_data_upload(user_id: str, data_count: int = 1) -> Dict[str, Any]:
    """用户上传农业数据时发放少量奖励"""
    amount = REWARD_UPLOAD_DATA * data_count
    now = datetime.now().isoformat()
    with _get_db() as conn:
        conn.execute(
            "INSERT INTO photon_transactions (user_id, amount, reason, round_id, created_at) VALUES (?,?,?,?,?)",
            (user_id, amount, f"数据贡献奖励 x{data_count}", None, now),
        )
        conn.execute(
            """INSERT INTO photon_balances (user_id, balance, total_earned, last_updated)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   balance = balance + excluded.balance,
                   total_earned = total_earned + excluded.total_earned,
                   last_updated = excluded.last_updated""",
            (user_id, amount, amount, now),
        )
        row = conn.execute("SELECT * FROM photon_balances WHERE user_id=?", (user_id,)).fetchone()
    return {"photon_earned": amount, "new_balance": row["balance"], "total_earned": row["total_earned"]}


def get_balance(user_id: str) -> Dict[str, Any]:
    """查询用户 PHOTON 余额"""
    with _get_db() as conn:
        row = conn.execute("SELECT * FROM photon_balances WHERE user_id=?", (user_id,)).fetchone()
    if row is None:
        return {"user_id": user_id, "balance": 0.0, "total_earned": 0.0, "last_updated": None}
    return dict(row)


def get_transactions(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """查询用户 PHOTON 交易记录"""
    with _get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM photon_transactions WHERE user_id=?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    """获取贡献排行榜（按总收入降序）"""
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT user_id, total_earned, balance FROM photon_balances ORDER BY total_earned DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"rank": i + 1, **dict(r)} for i, r in enumerate(rows)]


def get_global_stats() -> Dict[str, Any]:
    """全局统计，供区块链页面「活跃节点」展示"""
    with _get_db() as conn:
        total_users = conn.execute("SELECT COUNT(*) as n FROM photon_balances").fetchone()["n"]
        total_rounds = conn.execute(
            "SELECT COUNT(DISTINCT round_id) as n FROM photon_transactions WHERE round_id IS NOT NULL"
        ).fetchone()["n"]
        total_photon = conn.execute("SELECT COALESCE(SUM(total_earned),0) as s FROM photon_balances").fetchone()["s"]
    return {
        "active_participants": total_users,
        "training_rounds_completed": total_rounds,
        "total_photon_issued": total_photon,
    }
