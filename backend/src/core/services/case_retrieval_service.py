"""
农业病例/历史案例检索服务 — nomic-embed-text + 内存向量库
=========================================================

功能：
  1. 将历史农业决策案例嵌入为向量（nomic-embed-text）
  2. 通过余弦相似度检索最相关的历史案例
  3. 作为 SmartPipeline 的 RAG 层，为 qwen2.5 提供参考案例
  4. 支持在线追加（决策结束后把当前案例入库）

设计原则：
  - 纯内存向量库（numpy cosine），无需 Chroma/Faiss 依赖
  - Ollama nomic-embed-text 做嵌入（274MB，本地运行）
  - 支持持久化到磁盘（json + npy），下次启动直接加载
  - 嵌入失败时静默降级，不影响主链路
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np

logger = logging.getLogger(__name__)

# ── 配置 ─────────────────────────────────────────────────────────────────────
EMBED_MODEL = "nomic-embed-text"
EMBED_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/embeddings"
EMBED_TIMEOUT = float(os.getenv("EMBED_TIMEOUT", "30"))
DEFAULT_CASE_DIR = str(
    Path(__file__).resolve().parent.parent.parent.parent / "models" / "case_db"
)


# ── 数据结构 ─────────────────────────────────────────────────────────────────

@dataclass
class AgriCase:
    """单条农业历史案例"""
    case_id: str
    task: str
    sensor_data: Dict[str, float]
    decision: str
    confidence: float
    recommendation: str
    outcome: str = ""          # 实际结果（如"实施后产量+15%"），可选
    crop_type: str = ""        # 作物类型（如"番茄"）
    created_at: float = field(default_factory=time.time)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_text(self) -> str:
        """将案例转化为可嵌入的文本描述"""
        parts = [
            f"任务: {self.task}",
            f"决策: {self.decision}",
            f"建议: {self.recommendation}",
        ]
        if self.crop_type:
            parts.append(f"作物: {self.crop_type}")
        if self.outcome:
            parts.append(f"实际结果: {self.outcome}")
        # 追加关键传感器值
        key_fields = {
            "irrigation": ["soil_moisture", "temperature", "humidity"],
            "disease_risk": ["humidity", "temperature", "leaf_wetness"],
            "fertilization": ["soil_n", "soil_p", "soil_k", "soil_ph"],
            "harvest_timing": ["accumulated_temperature", "days_since_flowering", "fruit_color_index"],
        }
        for k in key_fields.get(self.task, []):
            if k in self.sensor_data:
                parts.append(f"{k}={self.sensor_data[k]:.2f}")
        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "task": self.task,
            "sensor_data": self.sensor_data,
            "decision": self.decision,
            "confidence": round(self.confidence, 4),
            "recommendation": self.recommendation,
            "outcome": self.outcome,
            "crop_type": self.crop_type,
            "created_at": self.created_at,
            **self.extra,
        }


@dataclass
class RetrievalResult:
    """检索结果"""
    cases: List[Dict[str, Any]]
    scores: List[float]
    embed_time_ms: float
    search_time_ms: float
    source: str = "nomic-embed-text"  # "nomic-embed-text" or "keyword"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "top_k": len(self.cases),
            "cases": [
                {**c, "similarity": round(s, 4)}
                for c, s in zip(self.cases, self.scores)
            ],
            "embed_time_ms": round(self.embed_time_ms, 2),
            "search_time_ms": round(self.search_time_ms, 2),
        }


# ── 案例检索服务 ──────────────────────────────────────────────────────────────

class CaseRetrievalService:
    """
    农业历史案例向量检索服务

    使用 nomic-embed-text（274MB Ollama 模型）生成嵌入，
    支持按任务过滤 + 余弦相似度 Top-K 检索。
    """

    def __init__(self, case_dir: Optional[str] = None):
        self._case_dir = Path(case_dir or DEFAULT_CASE_DIR)
        self._case_dir.mkdir(parents=True, exist_ok=True)

        self._cases: List[AgriCase] = []
        self._vectors: Optional[np.ndarray] = None  # shape: (N, D)

        self._client = httpx.AsyncClient(timeout=EMBED_TIMEOUT)
        self._embed_available: Optional[bool] = None  # 懒检测

        # 启动时加载预存案例
        self._load_from_disk()

        logger.info(
            f"CaseRetrievalService 初始化 | 库: {len(self._cases)} 条案例 "
            f"| 向量维度: {self._vectors.shape[1] if self._vectors is not None else 'N/A'}"
        )

    # ── 嵌入 ──────────────────────────────────────────────────────────────────

    async def _embed(self, text: str) -> Optional[np.ndarray]:
        """调用 nomic-embed-text 生成嵌入向量，失败返回 None"""
        try:
            resp = await self._client.post(
                EMBED_URL,
                json={"model": EMBED_MODEL, "prompt": text},
                timeout=EMBED_TIMEOUT,
            )
            resp.raise_for_status()
            vec = np.array(resp.json()["embedding"], dtype=np.float32)
            return vec / (np.linalg.norm(vec) + 1e-8)  # L2 归一化
        except Exception as e:
            if self._embed_available is not False:
                logger.warning(f"nomic-embed-text 不可用: {e}")
                self._embed_available = False
            return None

    # ── 添加案例 ──────────────────────────────────────────────────────────────

    async def add_case(self, case: AgriCase) -> bool:
        """添加案例并更新向量索引"""
        t0 = time.time()
        text = case.to_text()
        vec = await self._embed(text)

        self._cases.append(case)
        if vec is not None:
            if self._vectors is None:
                self._vectors = vec.reshape(1, -1)
            else:
                self._vectors = np.vstack([self._vectors, vec])
            self._embed_available = True
        else:
            # 嵌入失败时用零向量占位（不影响案例存储）
            if self._vectors is None:
                self._vectors = np.zeros((1, 768), dtype=np.float32)
            else:
                dim = self._vectors.shape[1]
                self._vectors = np.vstack([self._vectors, np.zeros(dim, dtype=np.float32)])

        elapsed = (time.time() - t0) * 1000
        logger.debug(f"案例入库: {case.case_id} | {elapsed:.1f}ms")
        self._save_to_disk()
        return vec is not None

    def add_case_sync(self, case: AgriCase) -> None:
        """同步版本（不做嵌入，直接入库供规则检索用）"""
        self._cases.append(case)
        if self._vectors is None:
            self._vectors = np.zeros((1, 768), dtype=np.float32)
        else:
            dim = self._vectors.shape[1]
            self._vectors = np.vstack([self._vectors, np.zeros(dim, dtype=np.float32)])
        self._save_to_disk()

    # ── 检索 ──────────────────────────────────────────────────────────────────

    async def search(
        self,
        query_text: str,
        task: Optional[str] = None,
        top_k: int = 3,
        min_similarity: float = 0.5,
    ) -> RetrievalResult:
        """
        向量相似度检索，返回最相似的 top_k 个案例。

        Args:
            query_text:  查询文本（传感器描述 + 任务描述）
            task:        只返回该任务的案例（可选）
            top_k:       返回数量
            min_similarity: 最低相似度阈值
        """
        t0 = time.time()

        # 确定候选集（按任务过滤）
        if task:
            candidates_idx = [i for i, c in enumerate(self._cases) if c.task == task]
        else:
            candidates_idx = list(range(len(self._cases)))

        if not candidates_idx:
            return RetrievalResult(
                cases=[], scores=[], embed_time_ms=0.0, search_time_ms=0.0, source="empty"
            )

        # 生成查询向量
        t_embed = time.time()
        q_vec = await self._embed(query_text)
        embed_ms = (time.time() - t_embed) * 1000

        if q_vec is None or self._vectors is None:
            # 降级：返回最新的 top_k 个
            top_cases = [self._cases[i].to_dict() for i in candidates_idx[-top_k:]]
            return RetrievalResult(
                cases=top_cases,
                scores=[0.0] * len(top_cases),
                embed_time_ms=embed_ms,
                search_time_ms=0.0,
                source="keyword_fallback",
            )

        # 余弦相似度
        t_search = time.time()
        candidate_vecs = self._vectors[candidates_idx]  # (M, D)
        sims = (candidate_vecs @ q_vec).tolist()        # (M,) 归一化后点积 = cosine

        # 过滤 + 排序
        scored = [(candidates_idx[i], sims[i]) for i in range(len(candidates_idx))
                  if sims[i] >= min_similarity]
        scored.sort(key=lambda x: -x[1])
        top = scored[:top_k]

        search_ms = (time.time() - t_search) * 1000
        total_ms = (time.time() - t0) * 1000

        return RetrievalResult(
            cases=[self._cases[idx].to_dict() for idx, _ in top],
            scores=[s for _, s in top],
            embed_time_ms=embed_ms,
            search_time_ms=search_ms,
            source="nomic-embed-text",
        )

    async def search_by_sensors(
        self,
        sensor_data: Dict[str, float],
        task: str,
        context_hint: str = "",
        top_k: int = 3,
    ) -> RetrievalResult:
        """
        直接用传感器数据构建查询文本后检索
        """
        # 构建自然语言查询
        parts = [f"任务: {task}"]
        for k, v in sensor_data.items():
            parts.append(f"{k}={v:.2f}")
        if context_hint:
            parts.append(context_hint)
        query_text = " | ".join(parts)
        return await self.search(query_text, task=task, top_k=top_k)

    # ── 持久化 ────────────────────────────────────────────────────────────────

    def _save_to_disk(self) -> None:
        """将案例元数据和向量分别持久化"""
        try:
            meta_path = self._case_dir / "cases.json"
            vec_path = self._case_dir / "vectors.npy"

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump([c.to_dict() for c in self._cases], f, ensure_ascii=False)

            if self._vectors is not None:
                np.save(str(vec_path), self._vectors)
        except Exception as e:
            logger.warning(f"案例持久化失败: {e}")

    def _load_from_disk(self) -> None:
        """从磁盘加载历史案例和向量"""
        meta_path = self._case_dir / "cases.json"
        vec_path = self._case_dir / "vectors.npy"

        if not meta_path.exists():
            self._seed_default_cases()
            return

        try:
            with open(meta_path, encoding="utf-8") as f:
                raw = json.load(f)
            self._cases = [
                AgriCase(
                    case_id=d["case_id"],
                    task=d["task"],
                    sensor_data=d["sensor_data"],
                    decision=d["decision"],
                    confidence=d["confidence"],
                    recommendation=d["recommendation"],
                    outcome=d.get("outcome", ""),
                    crop_type=d.get("crop_type", ""),
                    created_at=d.get("created_at", time.time()),
                )
                for d in raw
            ]
            if vec_path.exists():
                self._vectors = np.load(str(vec_path))
            logger.info(f"从磁盘加载 {len(self._cases)} 条案例")
        except Exception as e:
            logger.warning(f"案例加载失败，重置: {e}")
            self._cases = []
            self._vectors = None
            self._seed_default_cases()

    def _seed_default_cases(self) -> None:
        """写入默认参考案例（覆盖常见场景）"""
        defaults = [
            AgriCase(
                case_id="seed_001",
                task="irrigation",
                sensor_data={"soil_moisture": 12.0, "temperature": 40.0, "humidity": 88.0},
                decision="urgent_irrigation",
                confidence=0.95,
                recommendation="紧急灌溉 — 土壤严重缺水，立即执行",
                outcome="灌溉后 6h 土壤湿度回升至 45%，植株恢复",
                crop_type="番茄",
            ),
            AgriCase(
                case_id="seed_002",
                task="disease_risk",
                sensor_data={"temperature": 24.0, "humidity": 95.0, "leaf_wetness": 0.9, "rainfall_48h": 50.0},
                decision="critical_risk",
                confidence=0.92,
                recommendation="危险 — 病害爆发条件已具备，立即防治",
                outcome="喷施代森锰锌后发病率降低 80%",
                crop_type="葡萄",
            ),
            AgriCase(
                case_id="seed_003",
                task="fertilization",
                sensor_data={"soil_n": 20.0, "soil_p": 10.0, "soil_k": 15.0, "soil_ph": 5.4},
                decision="heavy_fertilize",
                confidence=0.88,
                recommendation="重量补肥 — 严重缺肥，需加大用量",
                outcome="追施复合肥后叶色转绿，长势恢复",
                crop_type="草莓",
            ),
            AgriCase(
                case_id="seed_004",
                task="harvest_timing",
                sensor_data={"accumulated_temperature": 1150.0, "days_since_flowering": 85.0, "fruit_color_index": 0.82, "sugar_content": 18.0},
                decision="optimal",
                confidence=0.91,
                recommendation="最佳采收期 — 建议立即安排采收",
                outcome="采收后市场售价达到季节高峰",
                crop_type="桃子",
            ),
            AgriCase(
                case_id="seed_005",
                task="irrigation",
                sensor_data={"soil_moisture": 75.0, "temperature": 22.0, "humidity": 60.0, "rainfall_24h": 15.0},
                decision="no_action",
                confidence=0.90,
                recommendation="无需灌溉 — 土壤湿度充足",
                outcome="保持监测，3天后湿度降至 60% 再灌溉",
                crop_type="黄瓜",
            ),
        ]
        for c in defaults:
            self._cases.append(c)

        if self._vectors is None:
            self._vectors = np.zeros((len(defaults), 768), dtype=np.float32)
        else:
            dim = self._vectors.shape[1]
            self._vectors = np.vstack(
                [self._vectors, np.zeros((len(defaults), dim), dtype=np.float32)]
            )
        self._save_to_disk()
        logger.info(f"写入 {len(defaults)} 条默认参考案例")

    # ── 状态查询 ──────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        from collections import Counter
        task_dist = Counter(c.task for c in self._cases)
        return {
            "service": "CaseRetrievalService",
            "embed_model": EMBED_MODEL,
            "total_cases": len(self._cases),
            "task_distribution": dict(task_dist),
            "vector_shape": list(self._vectors.shape) if self._vectors is not None else None,
            "embed_available": self._embed_available,
            "case_dir": str(self._case_dir),
        }

    async def close(self) -> None:
        await self._client.aclose()


# ── 全局单例 ──────────────────────────────────────────────────────────────────
_case_retrieval_instance: Optional[CaseRetrievalService] = None


def get_case_retrieval_service() -> CaseRetrievalService:
    global _case_retrieval_instance
    if _case_retrieval_instance is None:
        _case_retrieval_instance = CaseRetrievalService()
    return _case_retrieval_instance
