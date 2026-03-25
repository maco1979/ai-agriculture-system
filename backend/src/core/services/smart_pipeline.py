"""
SmartPipeline — 农业智能决策 Pipeline 编排层

数据流：
    传感器读数
        ↓
    [Level-1] AnomalyDetectionService   — 过滤传感器故障/突变
        ↓ (正常/警告数据继续流转)
    [Level-2] LightGBMDecisionService   — 毫秒级决策（灌溉/病害/施肥/采收）
        ↓
    [Level-3] qwen2.5                   — 把决策结果格式化成结构化 JSON 建议
        ↓
    PipelineResult（统一响应结构）

设计原则：
  - 各层独立，任意层失败自动降级（不中断链路）
  - 同步推理 + 异步 qwen2.5 调用
  - 完整 tracing（每次调用有唯一 trace_id）
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# 数据结构
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineResult:
    """Pipeline 统一输出结构"""
    trace_id: str

    # ── 异常检测层结果 ─────────────────────────────────────────────────────
    anomaly_detected: bool
    anomaly_severity: str            # "normal" / "warning" / "critical"
    anomaly_features: List[str]
    anomaly_message: str

    # ── LightGBM 决策层结果 ────────────────────────────────────────────────
    lgbm_task: str                   # 执行的任务名
    lgbm_decision: str               # 决策标签
    lgbm_confidence: float
    lgbm_recommendation: str
    lgbm_fallback_used: bool

    # ── qwen2.5 格式化层结果 ───────────────────────────────────────────────
    structured_advice: Dict[str, Any]     # qwen 生成的 JSON 建议（可能为空）
    qwen_skipped: bool = False            # 是否跳过了 qwen（异常 critical 时触发或超时）
    qwen_skip_reason: str = ""

    # ── RAG 相似病例检索结果 ───────────────────────────────────────────────
    similar_cases: List[Dict[str, Any]] = field(default_factory=list)
    rag_source: str = ""                  # "nomic-embed-text" / "keyword_fallback" / "disabled"

    # ── 时延追踪 ───────────────────────────────────────────────────────────
    timing: Dict[str, float] = field(default_factory=dict)  # 各层耗时 ms
    total_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "anomaly": {
                "detected":  self.anomaly_detected,
                "severity":  self.anomaly_severity,
                "features":  self.anomaly_features,
                "message":   self.anomaly_message,
            },
            "decision": {
                "task":            self.lgbm_task,
                "label":           self.lgbm_decision,
                "confidence":      round(self.lgbm_confidence, 4),
                "recommendation":  self.lgbm_recommendation,
                "fallback_used":   self.lgbm_fallback_used,
            },
            "structured_advice": self.structured_advice,
            "qwen_skipped":      self.qwen_skipped,
            "qwen_skip_reason":  self.qwen_skip_reason,
            "similar_cases":     self.similar_cases,
            "rag_source":        self.rag_source,
            "timing_ms":         {k: round(v, 2) for k, v in self.timing.items()},
            "total_time_ms":     round(self.total_time_ms, 2),
        }


# ══════════════════════════════════════════════════════════════════════════════
# Pipeline 主类
# ══════════════════════════════════════════════════════════════════════════════

class SmartPipeline:
    """
    农业智能决策 Pipeline

    用法（FastAPI 依赖注入）：
        pipeline = SmartPipeline()
        result = await pipeline.run(sensor_data, task="irrigation")

    用法（独立调用）：
        pipeline = get_smart_pipeline()
        result = await pipeline.run({"temperature": 35, "soil_moisture": 18}, "irrigation")
    """

    def __init__(
        self,
        chat_model: str = "qwen2.5:14b",
        chat_model_url: str = "http://localhost:11434/v1",
        chat_timeout: int = 30,
        skip_qwen_on_critical: bool = False,   # critical 级别是否跳过 qwen（省延迟）
        qwen_enabled: bool = True,
        rag_enabled: bool = True,              # 是否启用 nomic-embed-text 案例检索
        rag_top_k: int = 3,                    # 检索最相似的案例数
    ):
        self._chat_model      = chat_model
        self._chat_model_url  = chat_model_url
        self._chat_timeout    = chat_timeout
        self._skip_qwen_on_critical = skip_qwen_on_critical
        self._qwen_enabled    = qwen_enabled
        self._rag_enabled     = rag_enabled
        self._rag_top_k       = rag_top_k

        # 懒加载服务实例（避免循环导入）
        self._anomaly_svc    = None
        self._lgbm_svc       = None
        self._case_svc       = None   # nomic-embed-text RAG 服务

        logger.info(
            f"SmartPipeline 初始化 | qwen_enabled={qwen_enabled} | "
            f"rag_enabled={rag_enabled} | skip_on_critical={skip_qwen_on_critical}"
        )

    # ── 懒加载 ────────────────────────────────────────────────────────────────

    def _get_anomaly_svc(self):
        if self._anomaly_svc is None:
            from src.core.services.anomaly_detection_service import get_anomaly_service
            self._anomaly_svc = get_anomaly_service()
        return self._anomaly_svc

    def _get_lgbm_svc(self):
        if self._lgbm_svc is None:
            from src.core.services.lgbm_decision_service import get_lgbm_service
            self._lgbm_svc = get_lgbm_service()
        return self._lgbm_svc

    def _get_case_svc(self):
        if self._case_svc is None:
            from src.core.services.case_retrieval_service import get_case_retrieval_service
            self._case_svc = get_case_retrieval_service()
        return self._case_svc

    # ══════════════════════════════════════════════════════════════════════════
    # 主入口
    # ══════════════════════════════════════════════════════════════════════════

    async def run(
        self,
        sensor_data: Dict[str, float],
        task: str = "irrigation",
        context_hint: str = "",          # 可选：额外上下文（如"番茄幼苗期"）
        use_ml_anomaly: bool = True,
    ) -> PipelineResult:
        """
        执行完整决策 pipeline。

        Args:
            sensor_data:   传感器字典，如 {"temperature": 35, "soil_moisture": 18}
            task:          LightGBM 任务（irrigation/disease_risk/fertilization/harvest_timing）
            context_hint:  追加到 qwen prompt 的额外上下文
            use_ml_anomaly: 是否启用 ML 异常检测（需先训练，否则自动降级到规则）

        Returns:
            PipelineResult
        """
        trace_id = str(uuid.uuid4())[:8]
        t_start = time.time()
        timing: Dict[str, float] = {}

        # ── Level 1: 异常检测 ─────────────────────────────────────────────
        t0 = time.time()
        anomaly_result = self._run_anomaly_detection(sensor_data, use_ml_anomaly)
        timing["anomaly_ms"] = (time.time() - t0) * 1000

        # critical 级别：数据可信度存疑，但仍继续决策（只是标记）
        anomaly_detected  = anomaly_result.is_anomaly
        anomaly_severity  = anomaly_result.severity
        anomaly_features  = anomaly_result.anomaly_features
        anomaly_message   = anomaly_result.message

        # ── Level 2: LightGBM 决策 ────────────────────────────────────────
        t0 = time.time()
        lgbm_result = self._run_lgbm_decision(sensor_data, task)
        timing["lgbm_ms"] = (time.time() - t0) * 1000

        # ── Level 2.5: RAG 相似病例检索（nomic-embed-text）────────────────
        similar_cases: List[Dict[str, Any]] = []
        rag_source = "disabled"
        if self._rag_enabled:
            t0 = time.time()
            rag_result = await self._run_rag(sensor_data, task, context_hint)
            timing["rag_ms"] = (time.time() - t0) * 1000
            similar_cases = rag_result.get("cases", [])
            rag_source = rag_result.get("source", "nomic-embed-text")

        # ── Level 3: qwen2.5 格式化输出 ──────────────────────────────────
        qwen_skipped = False
        qwen_skip_reason = ""
        structured_advice: Dict[str, Any] = {}

        should_call_qwen = (
            self._qwen_enabled
            and not (self._skip_qwen_on_critical and anomaly_severity == "critical")
        )

        if should_call_qwen:
            t0 = time.time()
            structured_advice, qwen_skipped, qwen_skip_reason = await self._run_qwen_format(
                sensor_data=sensor_data,
                task=task,
                anomaly_result=anomaly_result,
                lgbm_result=lgbm_result,
                context_hint=context_hint,
                similar_cases=similar_cases,
            )
            timing["qwen_ms"] = (time.time() - t0) * 1000
        else:
            qwen_skipped = True
            qwen_skip_reason = "critical 级别异常，跳过格式化以节省延迟"

        total_time = (time.time() - t_start) * 1000

        result = PipelineResult(
            trace_id=trace_id,
            anomaly_detected=anomaly_detected,
            anomaly_severity=anomaly_severity,
            anomaly_features=anomaly_features,
            anomaly_message=anomaly_message,
            lgbm_task=task,
            lgbm_decision=lgbm_result.decision,
            lgbm_confidence=lgbm_result.confidence,
            lgbm_recommendation=lgbm_result.recommendation,
            lgbm_fallback_used=lgbm_result.fallback_used,
            structured_advice=structured_advice,
            qwen_skipped=qwen_skipped,
            qwen_skip_reason=qwen_skip_reason,
            similar_cases=similar_cases,
            rag_source=rag_source,
            timing=timing,
            total_time_ms=total_time,
        )

        logger.info(
            f"[{trace_id}] Pipeline 完成 | task={task} | "
            f"anomaly={anomaly_severity} | decision={lgbm_result.decision} | "
            f"total={total_time:.1f}ms"
        )

        return result

    # ══════════════════════════════════════════════════════════════════════════
    # 各层执行方法（同步/异步解耦）
    # ══════════════════════════════════════════════════════════════════════════

    def _run_anomaly_detection(self, sensor_data: Dict[str, float], use_ml: bool):
        """执行异常检测（同步）"""
        try:
            svc = self._get_anomaly_svc()
            return svc.detect(sensor_data, use_ml=use_ml)
        except Exception as e:
            logger.warning(f"异常检测层失败，降级到空结果: {e}")
            # 返回空结果（不阻断 pipeline）
            from src.core.services.anomaly_detection_service import AnomalyResult
            return AnomalyResult(
                is_anomaly=False,
                score=1.0,
                anomaly_features=[],
                severity="normal",
                message=f"检测跳过（错误: {str(e)[:50]}）",
                detection_time_ms=0.0,
                model_name="fallback",
            )

    def _run_lgbm_decision(self, sensor_data: Dict[str, float], task: str):
        """执行 LightGBM 决策（同步）"""
        try:
            svc = self._get_lgbm_svc()
            return svc.predict(task, sensor_data)
        except Exception as e:
            logger.warning(f"LightGBM 决策层失败: {e}")
            from src.core.services.lgbm_decision_service import DecisionResult
            return DecisionResult(
                task=task,
                decision="unknown",
                confidence=0.0,
                probability={},
                feature_importance={},
                recommendation=f"决策层异常（{str(e)[:50]}），请人工复查",
                inference_time_ms=0.0,
                is_trained=False,
                fallback_used=True,
            )

    async def _run_rag(
        self,
        sensor_data: Dict[str, float],
        task: str,
        context_hint: str = "",
    ) -> Dict[str, Any]:
        """调用 CaseRetrievalService 做相似历史案例检索（nomic-embed-text）"""
        try:
            svc = self._get_case_svc()
            result = await svc.search_by_sensors(
                sensor_data=sensor_data,
                task=task,
                context_hint=context_hint,
                top_k=self._rag_top_k,
            )
            return result.to_dict()
        except Exception as e:
            logger.warning(f"RAG 检索层失败，降级: {e}")
            return {"cases": [], "source": "error", "error": str(e)[:80]}

    async def _run_qwen_format(
        self,
        sensor_data: Dict[str, float],
        task: str,
        anomaly_result,
        lgbm_result,
        context_hint: str,
        similar_cases: Optional[List[Dict[str, Any]]] = None,
    ):
        """调用 qwen2.5 做结构化输出（异步）"""
        import json as _json
        import httpx

        _JSON_SYSTEM = """你是农业决策AI，只输出 JSON 格式的结构化建议，不输出任何其他文字。
输出格式：
{
  "diagnosis": "问题诊断",
  "severity": "low/medium/high/critical",
  "immediate_actions": ["立即执行的动作1", "动作2"],
  "short_term_plan": ["3-7天计划项"],
  "monitoring_points": ["需要重点监控的指标"],
  "estimated_recovery": "预计恢复时间或说明"
}"""

        # 组织 prompt：把异常检测和 LightGBM 结果都放进去
        parts = [
            f"【传感器数据】{_json.dumps(sensor_data, ensure_ascii=False)}",
            f"【异常检测】严重程度: {anomaly_result.severity} | {anomaly_result.message}",
            f"【决策分析】任务: {task} | 结论: {lgbm_result.decision} "
            f"(置信度 {lgbm_result.confidence:.0%}) | {lgbm_result.recommendation}",
        ]
        if context_hint:
            parts.append(f"【补充信息】{context_hint}")

        # 追加相似历史案例（RAG 层）
        if similar_cases:
            case_texts = []
            for i, c in enumerate(similar_cases[:3], 1):
                txt = (
                    f"案例{i}: 决策={c.get('decision','?')} | "
                    f"建议={c.get('recommendation','?')}"
                )
                if c.get("outcome"):
                    txt += f" | 实际效果={c['outcome']}"
                case_texts.append(txt)
            parts.append("【相似历史案例参考】\n" + "\n".join(case_texts))

        task_hint = {
            "irrigation":     "请重点给出灌溉操作建议",
            "disease_risk":   "请重点给出病害防治建议",
            "fertilization":  "请重点给出施肥方案建议",
            "harvest_timing": "请重点给出采收安排建议",
        }.get(task, "请给出综合农业管理建议")
        parts.append(f"【分析要求】{task_hint}")

        message = "\n".join(parts)

        try:
            async with httpx.AsyncClient(
                base_url=self._chat_model_url,
                timeout=self._chat_timeout,
            ) as client:
                resp = await client.post(
                    "/chat/completions",
                    json={
                        "model": self._chat_model,
                        "messages": [
                            {"role": "system", "content": _JSON_SYSTEM},
                            {"role": "user",   "content": message},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1024,
                        "response_format": {"type": "json_object"},
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                raw = resp.json()["choices"][0]["message"]["content"]

            try:
                advice = _json.loads(raw)
            except _json.JSONDecodeError:
                advice = {"raw_reply": raw, "parse_error": True}

            return advice, False, ""

        except httpx.ConnectError:
            return {}, True, "Ollama 未运行（连接失败）"
        except httpx.TimeoutException:
            return {}, True, f"qwen2.5 响应超时（>{self._chat_timeout}s）"
        except Exception as e:
            logger.warning(f"qwen2.5 格式化层失败: {e}")
            return {}, True, f"格式化层错误: {str(e)[:80]}"

    # ══════════════════════════════════════════════════════════════════════════
    # 批量分析（多区域 / 多传感器节点）
    # ══════════════════════════════════════════════════════════════════════════

    async def run_batch(
        self,
        sensor_records: List[Dict[str, float]],
        task: str = "irrigation",
        concurrency: int = 5,
    ) -> List[PipelineResult]:
        """
        批量执行 pipeline（适合大田多点分析）。

        Args:
            sensor_records: 传感器数据列表
            task:           任务名
            concurrency:    并发上限（防止 qwen 被打满）
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def _bounded_run(data):
            async with semaphore:
                return await self.run(data, task=task)

        return await asyncio.gather(*[_bounded_run(d) for d in sensor_records])


# ══════════════════════════════════════════════════════════════════════════════
# 全局单例
# ══════════════════════════════════════════════════════════════════════════════

_pipeline_instance: Optional[SmartPipeline] = None


def get_smart_pipeline() -> SmartPipeline:
    """获取全局 SmartPipeline 单例"""
    global _pipeline_instance
    if _pipeline_instance is None:
        import os
        _pipeline_instance = SmartPipeline(
            chat_model=os.getenv("CHAT_MODEL", "qwen2.5:14b"),
            chat_model_url=os.getenv("CHAT_MODEL_URL", "http://localhost:11434/v1"),
            chat_timeout=int(os.getenv("CHAT_MODEL_TIMEOUT", "30")),
            skip_qwen_on_critical=os.getenv("SKIP_QWEN_ON_CRITICAL", "false").lower() == "true",
            rag_enabled=os.getenv("RAG_ENABLED", "true").lower() == "true",
            rag_top_k=int(os.getenv("RAG_TOP_K", "3")),
        )
    return _pipeline_instance
