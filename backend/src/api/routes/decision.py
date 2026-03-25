"""
智能决策 API 路由
- 传感器异常检测（scikit-learn IsolationForest + Z-score + 硬阈值三级联合）
- 农业快速决策（LightGBM：灌溉/病害/施肥/采收）
- qwen2.5 快速对话（结构化建议生成）
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.core.services.anomaly_detection_service import (
    AnomalyDetectionService,
    AnomalyResult,
    get_anomaly_service,
    reset_anomaly_service,
)
from src.core.services.lgbm_decision_service import (
    LightGBMDecisionService,
    DecisionResult,
    get_lgbm_service,
    TASK_CONFIGS,
)
from src.core.services.smart_pipeline import SmartPipeline, get_smart_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decision", tags=["decision"])

# ── qwen2.5 配置 ──────────────────────────────────────────────────────────────
CHAT_MODEL     = os.getenv("CHAT_MODEL",     "qwen2.5:14b")
CHAT_MODEL_URL = os.getenv("CHAT_MODEL_URL", "http://localhost:11434/v1")
CHAT_TIMEOUT   = int(os.getenv("CHAT_MODEL_TIMEOUT", "60"))
CHAT_MAX_TOK   = int(os.getenv("CHAT_MAX_TOKENS", "4096"))


# ════════════════════════════════════════════════════════════════════════════
# 📡  传感器异常检测接口
# ════════════════════════════════════════════════════════════════════════════

class SensorAnomalyRequest(BaseModel):
    """传感器异常检测请求"""
    values: Dict[str, float] = Field(
        ...,
        example={
            "temperature": 38.5,
            "humidity": 92.0,
            "soil_moisture": 15.0,
            "co2": 450.0,
        },
        description="传感器读数字典，支持：temperature/humidity/soil_moisture/soil_ph/co2/light/ec/pressure等",
    )
    use_ml: bool = Field(True, description="是否使用 ML 模型（需要先训练）")


class AnomalyTrainRequest(BaseModel):
    """异常检测训练请求"""
    historical_data: List[Dict[str, float]] = Field(
        ...,
        description="历史正常读数列表，建议至少 200 条",
    )
    algorithm: str = Field(
        "isolation_forest",
        description="算法选择：isolation_forest / lof / ocsvm",
    )
    contamination: float = Field(
        0.05,
        ge=0.01, le=0.5,
        description="预期异常比例（0.01~0.5）",
    )


class NormalRangesUpdateRequest(BaseModel):
    """更新正常范围请求"""
    ranges: Dict[str, List[float]] = Field(
        ...,
        example={"temperature": [0, 40], "humidity": [20, 95]},
        description="每个传感器的 [min, max] 正常范围",
    )


@router.post(
    "/anomaly/detect",
    summary="📡 传感器异常检测",
    description=(
        "三级联合异常检测（硬阈值 → Z-score → ML模型）。\\n\\n"
        "**无需训练即可使用**（自动回退到规则检测）。\\n"
        "训练后精度更高（`POST /decision/anomaly/train`）。\\n\\n"
        "**severity 说明：**\\n"
        "- `normal`: 正常\\n"
        "- `warning`: 偏离正常范围，建议检查\\n"
        "- `critical`: 严重异常，需立即处理"
    ),
)
async def detect_sensor_anomaly(
    request: SensorAnomalyRequest,
    svc: AnomalyDetectionService = Depends(get_anomaly_service),
) -> Dict[str, Any]:
    """传感器数据异常检测"""
    try:
        result = svc.detect(request.values, use_ml=request.use_ml)
        return result.to_dict()
    except Exception as e:
        logger.error(f"异常检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"异常检测错误: {str(e)}")


@router.post(
    "/anomaly/train",
    summary="🎓 训练异常检测模型",
    description="用历史正常数据训练 ML 异常检测模型，训练后检测精度显著提升。",
)
async def train_anomaly_model(
    request: AnomalyTrainRequest,
    svc: AnomalyDetectionService = Depends(get_anomaly_service),
) -> Dict[str, Any]:
    """训练异常检测模型"""
    if len(request.historical_data) < 20:
        raise HTTPException(status_code=400, detail="训练数据至少需要 20 条")
    try:
        # 如果需要切换算法，重新创建服务
        if svc._algorithm != request.algorithm:
            svc = reset_anomaly_service(
                algorithm=request.algorithm,
                contamination=request.contamination,
            )
        result = svc.fit(request.historical_data)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"模型训练失败: {e}")
        raise HTTPException(status_code=500, detail=f"训练错误: {str(e)}")


@router.post(
    "/anomaly/update-ranges",
    summary="⚙️ 更新传感器正常范围",
)
async def update_normal_ranges(
    request: NormalRangesUpdateRequest,
    svc: AnomalyDetectionService = Depends(get_anomaly_service),
) -> Dict[str, Any]:
    """动态更新传感器正常范围（适应不同作物/季节）"""
    ranges = {k: tuple(v) for k, v in request.ranges.items()}
    svc.set_normal_ranges(ranges)
    return {"success": True, "updated": list(ranges.keys()), "status": svc.get_status()}


@router.get(
    "/anomaly/status",
    summary="📋 异常检测服务状态",
)
async def get_anomaly_status(
    svc: AnomalyDetectionService = Depends(get_anomaly_service),
) -> Dict[str, Any]:
    return svc.get_status()


# ════════════════════════════════════════════════════════════════════════════
# 🌱  LightGBM 农业决策接口
# ════════════════════════════════════════════════════════════════════════════

class LGBMPredictRequest(BaseModel):
    """LightGBM 决策推理请求"""
    task: str = Field(
        ...,
        description="任务名：irrigation / disease_risk / fertilization / harvest_timing",
    )
    features: Dict[str, float] = Field(
        ...,
        description="特征值字典（未知特征自动填 0）",
    )


class LGBMBatchRequest(BaseModel):
    """批量推理请求"""
    task: str
    features_list: List[Dict[str, float]] = Field(..., min_length=1, max_length=1000)


class LGBMTrainRequest(BaseModel):
    """训练请求"""
    task: str = Field(..., description="任务名")
    X_train: List[Dict[str, float]] = Field(..., description="训练特征")
    y_train: List[int] = Field(..., description="训练标签（整数类别）")
    num_boost_round: int = Field(100, ge=10, le=1000)
    X_val: Optional[List[Dict[str, float]]] = None
    y_val: Optional[List[int]] = None


@router.post(
    "/lgbm/predict",
    summary="🌱 农业快速决策推理",
    description=(
        "使用 LightGBM 进行毫秒级农业决策推理。\\n\\n"
        "**任务（task）说明：**\\n"
        "- `irrigation`: 灌溉决策（特征：soil_moisture/temperature/humidity/evapotranspiration等）\\n"
        "- `disease_risk`: 病害风险评估（特征：temperature/humidity/leaf_wetness/rainfall_48h等）\\n"
        "- `fertilization`: 施肥决策（特征：soil_n/soil_p/soil_k/soil_ph/ec等）\\n"
        "- `harvest_timing`: 采收时机（特征：accumulated_temperature/days_since_flowering等）\\n\\n"
        "**未训练时**自动使用专家规则回退，立即可用。"
    ),
)
async def lgbm_predict(
    request: LGBMPredictRequest,
    svc: LightGBMDecisionService = Depends(get_lgbm_service),
) -> Dict[str, Any]:
    """LightGBM 单条决策推理"""
    try:
        result = svc.predict(request.task, request.features)
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LightGBM 推理失败: {e}")
        raise HTTPException(status_code=500, detail=f"推理错误: {str(e)}")


@router.post(
    "/lgbm/predict-batch",
    summary="⚡ 批量农业决策推理",
    description="批量推理，最多 1000 条，适合数据回放或大田多点分析。",
)
async def lgbm_predict_batch(
    request: LGBMBatchRequest,
    svc: LightGBMDecisionService = Depends(get_lgbm_service),
) -> Dict[str, Any]:
    """批量推理"""
    try:
        results = svc.predict_batch(request.task, request.features_list)
        return {
            "task": request.task,
            "count": len(results),
            "results": [r.to_dict() for r in results],
        }
    except Exception as e:
        logger.error(f"批量推理失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量推理错误: {str(e)}")


@router.post(
    "/lgbm/train",
    summary="🎓 训练 LightGBM 决策模型",
    description="用标注数据训练指定任务的模型。训练后模型自动保存到磁盘，重启后自动加载。",
)
async def lgbm_train(
    request: LGBMTrainRequest,
    svc: LightGBMDecisionService = Depends(get_lgbm_service),
) -> Dict[str, Any]:
    """训练 LightGBM 模型"""
    if len(request.X_train) < 50:
        raise HTTPException(status_code=400, detail="训练数据至少需要 50 条")
    if len(request.X_train) != len(request.y_train):
        raise HTTPException(status_code=400, detail="X_train 和 y_train 长度不一致")
    try:
        result = svc.fit(
            task=request.task,
            X_train=request.X_train,
            y_train=request.y_train,
            num_boost_round=request.num_boost_round,
            X_val=request.X_val,
            y_val=request.y_val,
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"LightGBM 训练失败: {e}")
        raise HTTPException(status_code=500, detail=f"训练错误: {str(e)}")


@router.get(
    "/lgbm/status",
    summary="📋 查看 LightGBM 服务状态",
)
async def lgbm_status(
    svc: LightGBMDecisionService = Depends(get_lgbm_service),
) -> Dict[str, Any]:
    return svc.get_status()


@router.get(
    "/lgbm/tasks",
    summary="📖 列出所有可用任务及特征说明",
)
async def lgbm_tasks() -> Dict[str, Any]:
    return {
        task: {
            "features": cfg["features"],
            "labels": cfg["labels"],
            "label_descriptions": cfg["label_names"],
        }
        for task, cfg in TASK_CONFIGS.items()
    }


# ════════════════════════════════════════════════════════════════════════════
# 💬  qwen2.5 快速对话接口
#     对比 R1：响应快 3-5x，适合实时对话/结构化输出/快速建议
# ════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    """qwen2.5 对话请求"""
    message: str = Field(..., description="用户消息")
    system_prompt: Optional[str] = Field(
        None,
        description="系统提示词（不传则使用农业AI助手默认提示）",
    )
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=64, le=8192)
    json_mode: bool = Field(
        False,
        description="是否强制输出 JSON 格式（适合结构化数据提取）",
    )


class StructuredDecisionRequest(BaseModel):
    """结构化决策建议请求（qwen2.5 生成 JSON 格式建议）"""
    context: str = Field(..., description="环境描述（传感器数据、观察到的问题等）")
    task_type: str = Field(
        "general",
        description="任务类型：irrigation/disease/fertilization/general",
    )
    sensor_data: Optional[Dict[str, float]] = Field(None, description="可选：传感器数据")
    detection_result: Optional[Dict[str, Any]] = Field(None, description="可选：YOLO检测结果")


_DEFAULT_SYSTEM = """你是一位经验丰富的农业AI助手，专注于温室和大田智能农业管理。
你的回答需要：
1. 简洁准确，直接回答问题
2. 结合实际农业场景给出可操作建议
3. 用中文回答
4. 关键数据和建议用 **加粗** 标注"""

_JSON_SYSTEM = """你是农业决策AI，只输出 JSON 格式的结构化建议。
输出格式：
{
  "diagnosis": "问题诊断",
  "severity": "low/medium/high/critical",
  "immediate_actions": ["立即执行的动作1", ...],
  "short_term_plan": ["3-7天计划"],
  "monitoring_points": ["需要重点监控的指标"],
  "estimated_recovery": "预计恢复时间"
}"""


async def _call_qwen(
    message: str,
    system: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    """调用 qwen2.5 Ollama 接口"""
    payload: Dict[str, Any] = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(
        base_url=CHAT_MODEL_URL,
        timeout=CHAT_TIMEOUT,
    ) as client:
        resp = await client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


@router.post(
    "/chat",
    summary="💬 qwen2.5 快速对话",
    description=(
        f"使用 **{CHAT_MODEL}** 进行农业领域快速对话。\\n\\n"
        "比 DeepSeek-R1 响应快 3-5x，适合：\\n"
        "- 实时问答与建议\\n"
        "- 数据解读\\n"
        "- 操作指导\\n\\n"
        "需要深度推理分析时，请使用 `/inference` 路由的 R1 接口。"
    ),
)
async def chat_with_qwen(request: ChatRequest) -> Dict[str, Any]:
    """qwen2.5 快速对话"""
    import time
    t0 = time.time()
    try:
        system = request.system_prompt or (_JSON_SYSTEM if request.json_mode else _DEFAULT_SYSTEM)
        reply = await _call_qwen(
            message=request.message,
            system=system,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            json_mode=request.json_mode,
        )
        elapsed = (time.time() - t0) * 1000
        return {
            "model": CHAT_MODEL,
            "reply": reply,
            "response_time_ms": round(elapsed, 1),
        }
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"无法连接 Ollama ({CHAT_MODEL_URL})，请确认 ollama serve 正在运行",
        )
    except Exception as e:
        logger.error(f"qwen2.5 对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"对话错误: {str(e)}")


@router.post(
    "/structured-advice",
    summary="🔗 综合决策建议（qwen2.5 生成结构化 JSON）",
    description=(
        "综合传感器数据、YOLO检测结果、异常检测结论，\\n"
        "由 qwen2.5 生成结构化的农业干预建议。\\n\\n"
        "适合将多个检测模块的输出汇总成可执行的操作方案。"
    ),
)
async def get_structured_advice(request: StructuredDecisionRequest) -> Dict[str, Any]:
    """综合决策建议"""
    import json as _json
    import time

    t0 = time.time()

    # 组织 prompt
    parts = [f"【情境描述】{request.context}"]
    if request.sensor_data:
        parts.append(f"【传感器数据】{_json.dumps(request.sensor_data, ensure_ascii=False)}")
    if request.detection_result:
        summary = request.detection_result.get("summary", "")
        det_cnt = request.detection_result.get("detection_count", 0)
        parts.append(f"【视觉检测结果】检测到 {det_cnt} 个目标。{summary}")

    task_hint = {
        "irrigation": "请重点分析灌溉需求",
        "disease": "请重点分析病害风险和防治措施",
        "fertilization": "请重点分析施肥需求",
        "general": "请给出全面的农业管理建议",
    }.get(request.task_type, "请给出全面的农业管理建议")

    parts.append(f"【分析要求】{task_hint}")
    full_message = "\n".join(parts)

    try:
        reply_str = await _call_qwen(
            message=full_message,
            system=_JSON_SYSTEM,
            temperature=0.3,   # 低温度保证结构稳定
            max_tokens=2048,
            json_mode=True,
        )

        # 尝试解析 JSON
        try:
            advice = _json.loads(reply_str)
        except _json.JSONDecodeError:
            advice = {"raw_reply": reply_str}

        elapsed = (time.time() - t0) * 1000
        return {
            "model": CHAT_MODEL,
            "task_type": request.task_type,
            "advice": advice,
            "response_time_ms": round(elapsed, 1),
        }
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"无法连接 Ollama ({CHAT_MODEL_URL})，请确认 ollama serve 正在运行",
        )
    except Exception as e:
        logger.error(f"结构化建议生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"建议生成错误: {str(e)}")


# ════════════════════════════════════════════════════════════════════════════
# 🚀  SmartPipeline — 端到端感知→决策→格式化 Pipeline
#
#  这是新架构的统一入口：
#    传感器数据
#       ↓ AnomalyDetectionService（scikit-learn，三级联合检测）
#       ↓ LightGBMDecisionService （毫秒级农业决策）
#       ↓ qwen2.5:14b             （结构化 JSON 格式化输出）
#       → PipelineResult
# ════════════════════════════════════════════════════════════════════════════


class PipelineRequest(BaseModel):
    """SmartPipeline 请求"""
    sensor_data: Dict[str, float] = Field(
        ...,
        example={
            "temperature": 35.0,
            "humidity": 85.0,
            "soil_moisture": 18.0,
            "co2": 450.0,
        },
        description="传感器读数字典",
    )
    task: str = Field(
        "irrigation",
        description="决策任务：irrigation / disease_risk / fertilization / harvest_timing",
    )
    context_hint: str = Field(
        "",
        description="可选的额外上下文，如'番茄幼苗期'或'连续3天高温'，追加到 qwen 分析中",
    )
    use_ml_anomaly: bool = Field(
        True,
        description="是否启用 ML 异常检测（需先通过 /anomaly/train 训练，否则自动降级到规则）",
    )


class BatchPipelineRequest(BaseModel):
    """批量 Pipeline 请求"""
    sensor_records: List[Dict[str, float]] = Field(
        ..., min_length=1, max_length=200,
        description="多条传感器数据（适合大田多节点并行分析）",
    )
    task: str = Field("irrigation")
    concurrency: int = Field(
        5, ge=1, le=20,
        description="并发上限，防止 qwen 被打满",
    )


@router.post(
    "/pipeline/run",
    summary="🚀 SmartPipeline 端到端决策",
    description=(
        "**新架构统一入口**：一次调用完成传感器异常检测 → LightGBM 决策 → qwen2.5 格式化输出。\\n\\n"
        "**各层说明：**\\n"
        "1. `anomaly`：scikit-learn 三级联合检测（阈值+Z-score+ML），0 训练也能用\\n"
        "2. `decision`：LightGBM 毫秒级决策，4种任务，0 训练自动回退规则\\n"
        "3. `structured_advice`：qwen2.5:14b 把以上结果格式化成 JSON 操作建议\\n\\n"
        "**典型响应时间：**\\n"
        "- 无 qwen：< 5ms\\n"
        "- 含 qwen（ollama 本地）：1~5s\\n"
        "- qwen 超时时自动跳过，不影响 anomaly/decision 结果"
    ),
)
async def run_smart_pipeline(
    request: PipelineRequest,
    pipeline: SmartPipeline = Depends(get_smart_pipeline),
) -> Dict[str, Any]:
    """端到端 Pipeline 推理"""
    try:
        result = await pipeline.run(
            sensor_data=request.sensor_data,
            task=request.task,
            context_hint=request.context_hint,
            use_ml_anomaly=request.use_ml_anomaly,
        )
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"SmartPipeline 失败: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline 错误: {str(e)}")


@router.post(
    "/pipeline/batch",
    summary="⚡ SmartPipeline 批量分析",
    description=(
        "批量执行端到端 pipeline，适合大田多点并行分析。\\n"
        "最多支持 200 条，并发量可调（默认 5）。"
    ),
)
async def run_smart_pipeline_batch(
    request: BatchPipelineRequest,
    pipeline: SmartPipeline = Depends(get_smart_pipeline),
) -> Dict[str, Any]:
    """批量 Pipeline 推理"""
    try:
        results = await pipeline.run_batch(
            sensor_records=request.sensor_records,
            task=request.task,
            concurrency=request.concurrency,
        )
        return {
            "task": request.task,
            "count": len(results),
            "results": [r.to_dict() for r in results],
        }
    except Exception as e:
        logger.error(f"批量 Pipeline 失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量推理错误: {str(e)}")

