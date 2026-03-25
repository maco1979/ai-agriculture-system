"""
农业数据溯源服务
将图片上传/AI推理事件自动记录到区块链，并提供用户数据使用查询接口
"""

import hashlib
import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# SQLite 持久化路径（内存模拟的补充）
_DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/provenance.db")


def _get_db():
    """获取 SQLite 连接，自动创建表"""
    os.makedirs(os.path.dirname(os.path.abspath(_DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(os.path.abspath(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS provenance_records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            data_id     TEXT NOT NULL,
            user_id     TEXT NOT NULL DEFAULT 'anonymous',
            operation   TEXT NOT NULL,
            model_id    TEXT NOT NULL,
            file_name   TEXT,
            file_hash   TEXT,
            result      TEXT,
            tx_hash     TEXT,
            created_at  TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user ON provenance_records(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_data  ON provenance_records(data_id)")
    conn.commit()
    return conn


def record_upload_event(
    file_name: str,
    file_bytes: bytes,
    user_id: str = "anonymous",
    extra: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    用户上传图片时调用 —— 记录「数据上传」溯源事件

    Returns:
        {data_id, tx_hash, timestamp}
    """
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    data_id = f"upload_{file_hash[:16]}_{int(datetime.now().timestamp())}"
    tx_hash = f"0x{hashlib.sha256((data_id + user_id).encode()).hexdigest()[:64]}"
    now = datetime.now().isoformat()

    meta = {"file_name": file_name, "file_size": len(file_bytes)}
    if extra:
        meta.update(extra)

    with _get_db() as conn:
        conn.execute(
            """INSERT INTO provenance_records
               (data_id, user_id, operation, model_id, file_name, file_hash, result, tx_hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data_id, user_id, "upload", "none", file_name, file_hash, json.dumps(meta), tx_hash, now),
        )
    return {"data_id": data_id, "tx_hash": tx_hash, "timestamp": now, "file_hash": file_hash}


def record_inference_event(
    data_id: str,
    model_id: str,
    result_summary: str,
    user_id: str = "anonymous",
    file_name: str = "",
) -> Dict[str, Any]:
    """
    AI 推理完成后调用 —— 记录「模型使用」溯源事件，附带识别结果摘要

    Returns:
        {record_id, tx_hash, timestamp}
    """
    record_id = f"infer_{data_id}_{int(datetime.now().timestamp())}"
    tx_hash = f"0x{hashlib.sha256((record_id + model_id).encode()).hexdigest()[:64]}"
    now = datetime.now().isoformat()

    with _get_db() as conn:
        conn.execute(
            """INSERT INTO provenance_records
               (data_id, user_id, operation, model_id, file_name, file_hash, result, tx_hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data_id, user_id, "inference", model_id, file_name, "", result_summary, tx_hash, now),
        )
    return {"record_id": record_id, "tx_hash": tx_hash, "timestamp": now}


def get_user_provenance(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    获取用户的所有数据溯源记录（用于「我的数据」页面）
    """
    with _get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM provenance_records
               WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_data_provenance(data_id: str) -> List[Dict[str, Any]]:
    """
    查询某个数据 ID 的完整溯源链
    """
    with _get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM provenance_records
               WHERE data_id = ?
               ORDER BY created_at ASC""",
            (data_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> Dict[str, Any]:
    """
    获取全局溯源统计（供区块链页面使用）
    """
    with _get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as n FROM provenance_records").fetchone()["n"]
        uploads = conn.execute(
            "SELECT COUNT(*) as n FROM provenance_records WHERE operation='upload'"
        ).fetchone()["n"]
        inferences = conn.execute(
            "SELECT COUNT(*) as n FROM provenance_records WHERE operation='inference'"
        ).fetchone()["n"]
        users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) as n FROM provenance_records"
        ).fetchone()["n"]
    return {
        "total_records": total,
        "upload_events": uploads,
        "inference_events": inferences,
        "active_users": users,
    }
