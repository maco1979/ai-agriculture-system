"""
LLM 推理服务 — 封装 DeepSeek-R1 深度推理能力

三大场景复用入口：
  1. 作物病害深度诊断   → diagnose_crop_disease()
  2. 农业季度规划报告   → generate_quarterly_plan()
  3. 模型训练调优建议   → analyze_model_training()

底层统一走 deepseek-r1:70b（Ollama 本地），不传 tools。
需要工具调用时请使用 LLMRouter（decision-service 中的 llm_router.py）。
"""

import httpx
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── 配置（优先读取环境变量，回退到默认值）─────────────────────────────────
REASONING_MODEL     = os.getenv("REASONING_MODEL",     "deepseek-r1:70b")
REASONING_MODEL_URL = os.getenv("REASONING_MODEL_URL", "http://localhost:11434/v1")
REASONING_TIMEOUT   = int(os.getenv("REASONING_MODEL_TIMEOUT", "120"))
REASONING_MAX_TOK   = int(os.getenv("REASONING_MAX_TOKENS",    "8192"))


# ── 系统提示词 ──────────────────────────────────────────────────────────────
_SYSTEM_DISEASE = """你是一位拥有20年经验的农业病理学专家与AI农业系统顾问。
请对用户描述的作物症状进行多步骤深度推理：
1. 症状识别与分类
2. 可能病因分析（真菌/细菌/病毒/生理性/环境性）
3. 鉴别诊断（排除相似病害）
4. 确诊结论与置信度评估
5. 分阶段防治方案（应急处理 → 中期防治 → 长期预防）
6. 预计恢复周期与风险提示

请保持严谨的逻辑推理链，每步结论必须有依据支撑。"""

_SYSTEM_QUARTERLY = """你是资深农业经营顾问与AI系统规划师。
请基于用户提供的数据，生成一份结构完整的季度农业决策报告：
1. 现状评估（产量/质量/资源利用率）
2. 关键问题识别（风险点与机会点）
3. 季度目标设定（量化指标）
4. 分月执行计划（种植/管理/采收节点）
5. 资源配置方案（人力/设备/预算）
6. 风险预案与应急措施
7. 预期效益测算

报告需具体可执行，避免泛泛而谈。"""

_SYSTEM_MODEL_TUNING = """你是AI模型工程师与MLOps专家。
请对用户提供的模型训练性能数据进行全面分析：
1. 性能指标解读（准确率/损失/收敛速度）
2. 瓶颈定位（过拟合/欠拟合/梯度消失/数据问题）
3. 根本原因分析（逐步推理）
4. 调优优先级排序（高/中/低影响）
5. 具体超参数建议（含建议值范围）
6. 数据/架构层面优化建议
7. 预期改进效果评估

请给出可直接执行的、量化的调优建议。"""


class LLMReasoningService:
    """
    DeepSeek-R1 深度推理服务
    复用于病害诊断、季度规划、模型调优三大场景
    """

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(
            f"LLM推理服务初始化 | 模型: {REASONING_MODEL} | 地址: {REASONING_MODEL_URL}"
        )

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=REASONING_MODEL_URL,
                timeout=REASONING_TIMEOUT,
            )
        return self._client

    # ── 场景1：作物病害深度诊断 ────────────────────────────────────────────

    async def diagnose_crop_disease(
        self,
        crop_type: str,
        symptoms: str,
        environment: Optional[Dict[str, Any]] = None,
        growth_day: Optional[int] = None,
        images_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        作物病害深度诊断
        
        参数：
          crop_type           : 作物种类（番茄/生菜/...）
          symptoms            : 症状描述（叶片/茎秆/根系等表现）
          environment         : 环境数据 {temperature, humidity, co2, light...}
          growth_day          : 生长天数
          images_description  : 图像观察描述（无实际图像时可文字描述）
        """
        env_desc = ""
        if environment:
            env_desc = "\n".join(
                f"  - {k}: {v}" for k, v in environment.items()
            )
            env_desc = f"\n【环境数据】\n{env_desc}"

        img_desc = f"\n【图像观察】\n{images_description}" if images_description else ""
        day_desc = f"\n【生长天数】第 {growth_day} 天" if growth_day is not None else ""

        user_msg = (
            f"【作物种类】{crop_type}{day_desc}\n"
            f"【症状描述】\n{symptoms}"
            f"{env_desc}"
            f"{img_desc}\n\n"
            "请对上述症状进行多步骤深度推理诊断。"
        )

        raw = await self._call_reasoning(_SYSTEM_DISEASE, user_msg)
        return {
            "scenario": "crop_disease_diagnosis",
            "crop_type": crop_type,
            "model_used": REASONING_MODEL,
            **self._parse_response(raw),
        }

    # ── 场景2：农业季度规划报告 ────────────────────────────────────────────

    async def generate_quarterly_plan(
        self,
        farm_name: str,
        quarter: str,
        current_metrics: Dict[str, Any],
        crop_schedule: Optional[List[Dict]] = None,
        constraints: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        农业季度规划报告生成

        参数：
          farm_name       : 农场/基地名称
          quarter         : 季度（如 "2026-Q2"）
          current_metrics : 当前指标 {yield, quality_score, energy_cost...}
          crop_schedule   : 本季度作物安排列表
          constraints     : 约束条件（预算/人力/设备限制等）
        """
        metrics_desc = "\n".join(
            f"  - {k}: {v}" for k, v in current_metrics.items()
        )

        schedule_desc = ""
        if crop_schedule:
            lines = []
            for item in crop_schedule:
                lines.append(
                    f"  - {item.get('crop','?')} | "
                    f"面积:{item.get('area','?')} | "
                    f"计划产量:{item.get('target_yield','?')}"
                )
            schedule_desc = "\n【本季作物安排】\n" + "\n".join(lines)

        constraints_desc = f"\n【约束条件】\n{constraints}" if constraints else ""

        user_msg = (
            f"【农场】{farm_name}  【季度】{quarter}\n"
            f"【当前经营指标】\n{metrics_desc}"
            f"{schedule_desc}"
            f"{constraints_desc}\n\n"
            "请生成详细的季度农业决策规划报告。"
        )

        raw = await self._call_reasoning(_SYSTEM_QUARTERLY, user_msg)
        return {
            "scenario": "quarterly_plan",
            "farm_name": farm_name,
            "quarter": quarter,
            "model_used": REASONING_MODEL,
            **self._parse_response(raw),
        }

    # ── 场景3：模型训练策略分析 ────────────────────────────────────────────

    async def analyze_model_training(
        self,
        model_name: str,
        metrics_history: List[Dict[str, Any]],
        current_state: Dict[str, Any],
        objective: str = "maximize_accuracy",
        hardware_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        模型训练策略分析与调优建议

        参数：
          model_name       : 模型名称
          metrics_history  : 历史指标列表 [{epoch, accuracy, loss, lr...}]
          current_state    : 当前训练状态（来自 TrainingStateRequest）
          objective        : 优化目标
          hardware_info    : 硬件配置 {gpu, vram, cpu...}
        """
        # 取最近10条历史，避免过长
        recent = metrics_history[-10:] if len(metrics_history) > 10 else metrics_history
        history_lines = []
        for i, m in enumerate(recent):
            line = " | ".join(f"{k}:{v}" for k, v in m.items())
            history_lines.append(f"  [{i+1}] {line}")
        history_desc = "\n".join(history_lines) if history_lines else "  （暂无历史数据）"

        state_desc = "\n".join(
            f"  - {k}: {v}" for k, v in current_state.items()
        )

        hw_desc = ""
        if hardware_info:
            hw_desc = "\n【硬件配置】\n" + "\n".join(
                f"  - {k}: {v}" for k, v in hardware_info.items()
            )

        user_msg = (
            f"【模型名称】{model_name}\n"
            f"【优化目标】{objective}\n"
            f"【当前训练状态】\n{state_desc}\n"
            f"【近期训练历史（最近{len(recent)}条）】\n{history_desc}"
            f"{hw_desc}\n\n"
            "请对上述训练数据进行深度分析，给出详细的调优策略和具体参数建议。"
        )

        raw = await self._call_reasoning(_SYSTEM_MODEL_TUNING, user_msg)
        return {
            "scenario": "model_training_analysis",
            "model_name": model_name,
            "objective": objective,
            "model_used": REASONING_MODEL,
            **self._parse_response(raw),
        }

    # ── 场景4：视觉结果深度分析（接收视觉模型输出，进行R1推理）──────────────

    async def analyze_visual_scene(
        self,
        vision_observation: str,
        scene_type: str = "crop_disease",
        extra_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        基于视觉模型观察结果进行 R1 深度推理

        适用于：拍照→视觉理解→R1分析 管线的独立调用
        （完整管线推荐直接用 VisionReasoningPipeline）

        参数：
          vision_observation : 视觉模型输出的图像观察报告（文字）
          scene_type         : 场景类型（crop_disease/growth_status/pest_detection/environment/general）
          extra_context      : 补充背景信息
        """
        _scene_prompts = {
            "crop_disease": (
                "你是农业病理学专家。以下是视觉AI的图像观察报告，"
                "请进行多步骤深度病害推理诊断，给出确诊结论与防治方案。"
            ),
            "growth_status": (
                "你是作物栽培专家。以下是视觉AI的生长状态观察报告，"
                "请进行深度分析，给出生长评估与管理建议。"
            ),
            "pest_detection": (
                "你是植保专家。以下是视觉AI的害虫观察报告，"
                "请进行害虫鉴定、危害评估与防治方案推理。"
            ),
            "environment": (
                "你是农业环境优化专家。以下是视觉AI的环境观察报告，"
                "请分析环境问题并给出优化建议。"
            ),
            "general": (
                "你是AI农业系统分析专家。以下是视觉AI的图像观察报告，"
                "请进行综合深度分析与决策建议。"
            ),
        }
        system_prompt = _scene_prompts.get(scene_type, _scene_prompts["general"])

        user_msg = (
            f"【视觉AI观察报告】\n{vision_observation}"
            + (f"\n\n【补充背景】\n{extra_context}" if extra_context else "")
            + "\n\n请基于以上观察进行深度推理分析。"
        )

        raw = await self._call_reasoning(system_prompt, user_msg)
        return {
            "scenario": f"visual_scene_{scene_type}",
            "scene_type": scene_type,
            "model_used": REASONING_MODEL,
            **self._parse_response(raw),
        }

    # ── 通用推理接口 ───────────────────────────────────────────────────────

    async def reason(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """通用深度推理接口（自定义系统提示词）"""
        raw = await self._call_reasoning(
            system_prompt, user_message, max_tokens=max_tokens
        )
        return {
            "scenario": "custom_reasoning",
            "model_used": REASONING_MODEL,
            **self._parse_response(raw),
        }

    # ── 内部方法 ───────────────────────────────────────────────────────────

    async def _call_reasoning(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """向 DeepSeek-R1 发起请求（不传 tools）"""
        payload = {
            "model": REASONING_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            "max_tokens": max_tokens or REASONING_MAX_TOK,
            "stream": False,
        }
        try:
            resp = await self.client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                f"DeepSeek-R1 响应成功 | tokens={data.get('usage', {})}"
            )
            return data
        except httpx.HTTPStatusError as e:
            logger.error(
                f"DeepSeek-R1 HTTP错误: {e.response.status_code} | {e.response.text[:200]}"
            )
            raise
        except httpx.TimeoutException:
            logger.error("DeepSeek-R1 请求超时（推理时间过长）")
            raise
        except Exception as e:
            logger.error(f"DeepSeek-R1 未知错误: {e}")
            raise

    @staticmethod
    def _parse_response(raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 OpenAI 格式响应，提取：
          - reasoning_content : DeepSeek-R1 的思维链（CoT）
          - content           : 最终结论
          - usage             : token 用量
        """
        result = {
            "reasoning_process": "",
            "conclusion": "",
            "full_response": "",
            "usage": {},
        }
        try:
            choices = raw.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                reasoning = msg.get("reasoning_content", "")
                content   = msg.get("content", "")
                result["reasoning_process"] = reasoning
                result["conclusion"]        = content
                result["full_response"]     = (
                    f"【推理过程】\n{reasoning}\n\n【结论】\n{content}"
                    if reasoning else content
                )
            result["usage"] = raw.get("usage", {})
        except Exception as e:
            logger.warning(f"响应解析异常: {e}")
        return result

    async def close(self):
        """关闭 HTTP 连接"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# ── 全局单例 ───────────────────────────────────────────────────────────────
_service: Optional[LLMReasoningService] = None


def get_reasoning_service() -> LLMReasoningService:
    """获取全局推理服务实例（FastAPI 依赖注入用）"""
    global _service
    if _service is None:
        _service = LLMReasoningService()
    return _service
