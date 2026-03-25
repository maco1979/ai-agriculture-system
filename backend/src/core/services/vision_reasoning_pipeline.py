"""
视觉推理管线 — 拍照 → 视觉模型理解 → DeepSeek-R1 深度分析

管线流程：
  Step1: 摄像头拍照（base64图像）
  Step2: 视觉模型（LLaVA / MiniCPM-V / moondream2）理解图像内容
  Step3: DeepSeek-R1:70b 对视觉结果进行深度推理分析

支持的视觉模型（Ollama本地）：
  - llava:13b        通用视觉问答
  - minicpm-v        中文理解强，推荐农业场景
  - moondream2       轻量2B，速度快
  - llava-llama3     性能较强
"""

import base64
import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ── 配置 ────────────────────────────────────────────────────────────────────
VISION_MODEL      = os.getenv("VISION_MODEL",      "minicpm-v")
VISION_MODEL_URL  = os.getenv("VISION_MODEL_URL",  "http://localhost:11434/v1")
VISION_TIMEOUT    = int(os.getenv("VISION_MODEL_TIMEOUT", "60"))

REASONING_MODEL      = os.getenv("REASONING_MODEL",      "deepseek-r1:70b")
REASONING_MODEL_URL  = os.getenv("REASONING_MODEL_URL",  "http://localhost:11434/v1")
REASONING_TIMEOUT    = int(os.getenv("REASONING_MODEL_TIMEOUT", "120"))
REASONING_MAX_TOKENS = int(os.getenv("REASONING_MAX_TOKENS", "8192"))


class VisionScene(str, Enum):
    """视觉分析场景"""
    CROP_DISEASE    = "crop_disease"      # 作物病害检测
    GROWTH_STATUS   = "growth_status"     # 生长状态评估
    PEST_DETECTION  = "pest_detection"    # 病虫害检测
    ENVIRONMENT     = "environment"       # 环境状态分析
    GENERAL         = "general"           # 通用场景


# ── 视觉模型系统提示词 ───────────────────────────────────────────────────────
_VISION_PROMPTS: Dict[VisionScene, str] = {
    VisionScene.CROP_DISEASE: (
        "你是农业病害视觉识别专家。请仔细观察图像中作物的状态，"
        "详细描述：叶片颜色/纹理/形态异常、茎秆状况、病斑特征（颜色/形状/分布）、"
        "受害程度（轻/中/重）。输出结构化观察报告，不要做最终诊断结论。"
    ),
    VisionScene.GROWTH_STATUS: (
        "你是作物生长评估专家。请分析图像中作物的整体生长状态，"
        "描述：植株高度/密度/颜色均匀性、叶片展开情况、生长阶段判断、"
        "是否存在徒长/矮化/缺素等问题。给出量化评估（1-10分）。"
    ),
    VisionScene.PEST_DETECTION: (
        "你是农业害虫识别专家。请分析图像中是否存在害虫或虫害痕迹，"
        "描述：虫体特征（大小/颜色/形态）、危害部位和方式、"
        "虫口密度估算、受害面积比例。"
    ),
    VisionScene.ENVIRONMENT: (
        "你是农业环境分析专家。请分析图像中的环境状态，"
        "描述：光照强度/均匀性、植株间距与通风状况、"
        "土壤/基质可见状态、设施设备运行状况、整体环境评级。"
    ),
    VisionScene.GENERAL: (
        "你是农业AI视觉分析助手。请详细描述图像中的所有可见内容，"
        "重点关注：植物状态、环境条件、异常现象，给出客观全面的观察报告。"
    ),
}

# ── R1 深度分析系统提示词 ───────────────────────────────────────────────────
_R1_PROMPTS: Dict[VisionScene, str] = {
    VisionScene.CROP_DISEASE: (
        "你是拥有20年经验的农业病理学专家。"
        "以下是视觉AI对作物图像的观察报告，请基于此进行多步骤深度推理：\n"
        "1. 综合症状判断可能病害类型（真菌/细菌/病毒/生理性）\n"
        "2. 鉴别诊断（排除相似病害，给出置信度）\n"
        "3. 病害发展阶段评估（初期/中期/末期）\n"
        "4. 发病原因分析（环境/栽培管理/品种抗性）\n"
        "5. 分阶段防治方案（应急72h → 中期2周 → 长期预防）\n"
        "6. 预计损失风险与恢复周期\n"
        "请保持严谨推理链，每步结论须有依据。"
    ),
    VisionScene.GROWTH_STATUS: (
        "你是资深农业栽培专家。"
        "以下是视觉AI对作物生长状态的观察报告，请进行深度分析：\n"
        "1. 生长阶段精确判断与正常值对比\n"
        "2. 存在问题的根因分析（光照/营养/水分/温度）\n"
        "3. 生长潜力评估与产量预测\n"
        "4. 针对性栽培管理调整建议（含具体参数）\n"
        "5. 后续关键管理节点提醒"
    ),
    VisionScene.PEST_DETECTION: (
        "你是农业植保专家。"
        "以下是视觉AI对害虫/虫害的观察报告，请进行深度分析：\n"
        "1. 害虫种类鉴定与生活习性分析\n"
        "2. 危害程度量化评估与经济损失预测\n"
        "3. 传播扩散风险评估\n"
        "4. 生物/物理/化学防治方案（优先级排序）\n"
        "5. 防治时机与用药安全间隔期建议"
    ),
    VisionScene.ENVIRONMENT: (
        "你是农业设施环境优化专家。"
        "以下是视觉AI对农业环境的观察报告，请进行深度分析：\n"
        "1. 环境各指标与作物需求的匹配度评估\n"
        "2. 主要限制因素识别与量化影响\n"
        "3. 改善优先级排序（ROI最高的改进项）\n"
        "4. 具体优化方案（含设备调整参数）\n"
        "5. 预期改善效果评估"
    ),
    VisionScene.GENERAL: (
        "你是AI农业系统综合分析专家。"
        "以下是视觉AI的图像观察报告，请进行综合深度分析，"
        "识别关键问题、评估风险等级、给出优先处理建议。"
    ),
}


class VisionReasoningPipeline:
    """
    视觉推理管线
    
    拍照 → 视觉模型（LLaVA/MiniCPM-V）理解 → DeepSeek-R1 深度分析
    """

    def __init__(self):
        self._vision_client: Optional[httpx.AsyncClient] = None
        self._reasoning_client: Optional[httpx.AsyncClient] = None
        logger.info(
            f"视觉推理管线初始化 | 视觉模型: {VISION_MODEL} | 推理模型: {REASONING_MODEL}"
        )

    @property
    def vision_client(self) -> httpx.AsyncClient:
        if self._vision_client is None or self._vision_client.is_closed:
            self._vision_client = httpx.AsyncClient(
                base_url=VISION_MODEL_URL,
                timeout=VISION_TIMEOUT,
            )
        return self._vision_client

    @property
    def reasoning_client(self) -> httpx.AsyncClient:
        if self._reasoning_client is None or self._reasoning_client.is_closed:
            self._reasoning_client = httpx.AsyncClient(
                base_url=REASONING_MODEL_URL,
                timeout=REASONING_TIMEOUT,
            )
        return self._reasoning_client

    # ── 核心管线入口 ─────────────────────────────────────────────────────────

    async def analyze(
        self,
        image_base64: str,
        scene: VisionScene = VisionScene.CROP_DISEASE,
        extra_context: Optional[str] = None,
        vision_model: Optional[str] = None,
        skip_reasoning: bool = False,
    ) -> Dict[str, Any]:
        """
        完整视觉推理管线
        
        参数：
          image_base64   : base64编码的图像（JPEG/PNG）
          scene          : 分析场景（影响系统提示词）
          extra_context  : 额外上下文（如作物种类、环境数据文字描述）
          vision_model   : 覆盖默认视觉模型
          skip_reasoning : True=只做视觉理解，跳过R1深度分析（调试用）
        
        返回：
          {
            "vision_observation": "视觉模型观察报告",
            "reasoning_process":  "R1 思维链（CoT）",
            "conclusion":         "最终分析结论",
            "full_report":        "完整报告（含两个阶段）",
            "vision_model_used":  "minicpm-v",
            "reasoning_model_used": "deepseek-r1:70b",
            "usage": { "vision": {...}, "reasoning": {...} },
          }
        """
        result: Dict[str, Any] = {
            "scene": scene.value,
            "vision_model_used": vision_model or VISION_MODEL,
            "reasoning_model_used": REASONING_MODEL,
            "vision_observation": "",
            "reasoning_process": "",
            "conclusion": "",
            "full_report": "",
            "usage": {},
        }

        # ── Step 1: 视觉模型理解图像 ─────────────────────────────────────────
        logger.info(f"[管线 Step1] 视觉理解开始 | 场景: {scene.value}")
        vision_resp = await self._call_vision(
            image_base64=image_base64,
            scene=scene,
            extra_context=extra_context,
            model_override=vision_model,
        )
        vision_text = self._extract_text(vision_resp)
        result["vision_observation"] = vision_text
        result["usage"]["vision"] = vision_resp.get("usage", {})
        logger.info(f"[管线 Step1] 视觉理解完成 | 观察字符数: {len(vision_text)}")

        if skip_reasoning:
            result["full_report"] = f"【视觉观察】\n{vision_text}"
            return result

        # ── Step 2: DeepSeek-R1 深度分析 ─────────────────────────────────────
        logger.info(f"[管线 Step2] R1深度分析开始")
        r1_resp = await self._call_reasoning(
            vision_observation=vision_text,
            scene=scene,
            extra_context=extra_context,
        )
        reasoning_text = r1_resp.get("reasoning_content", "")
        conclusion_text = r1_resp.get("content", "")

        result["reasoning_process"] = reasoning_text
        result["conclusion"] = conclusion_text
        result["usage"]["reasoning"] = r1_resp.get("_usage", {})

        # 组装完整报告
        result["full_report"] = self._build_full_report(
            scene=scene,
            vision_text=vision_text,
            reasoning_text=reasoning_text,
            conclusion_text=conclusion_text,
        )
        logger.info(f"[管线 Step2] R1分析完成 | 结论字符数: {len(conclusion_text)}")
        return result

    # ── Step1: 调用视觉模型 ──────────────────────────────────────────────────

    async def _call_vision(
        self,
        image_base64: str,
        scene: VisionScene,
        extra_context: Optional[str],
        model_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """调用 Ollama 视觉模型（OpenAI 兼容接口）"""
        model = model_override or VISION_MODEL

        # 构造带图像的消息（OpenAI vision格式）
        user_content: List[Any] = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                },
            },
            {
                "type": "text",
                "text": (
                    _VISION_PROMPTS[scene]
                    + (f"\n\n【背景信息】{extra_context}" if extra_context else "")
                    + "\n\n请输出详细的图像观察报告："
                ),
            },
        ]

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": user_content}],
            "max_tokens": 2048,
            "stream": False,
        }

        try:
            resp = await self.vision_client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"视觉模型响应 usage={data.get('usage', {})}")
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"视觉模型HTTP错误: {e.response.status_code} | {e.response.text[:300]}")
            raise RuntimeError(f"视觉模型调用失败({e.response.status_code}): {e.response.text[:200]}")
        except httpx.TimeoutException:
            logger.error("视觉模型请求超时")
            raise RuntimeError("视觉模型响应超时，请检查模型是否已加载")

    # ── Step2: 调用 R1 深度推理 ──────────────────────────────────────────────

    async def _call_reasoning(
        self,
        vision_observation: str,
        scene: VisionScene,
        extra_context: Optional[str],
    ) -> Dict[str, Any]:
        """将视觉观察结果传给 DeepSeek-R1 做深度分析"""
        system_prompt = _R1_PROMPTS[scene]

        user_msg = (
            f"【视觉AI观察报告】\n{vision_observation}"
            + (f"\n\n【补充背景】\n{extra_context}" if extra_context else "")
            + "\n\n请基于以上观察报告进行深度推理分析。"
        )

        payload = {
            "model": REASONING_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_msg},
            ],
            "max_tokens": REASONING_MAX_TOKENS,
            "stream": False,
        }

        try:
            resp = await self.reasoning_client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            # 提取 message 内容，附带 usage
            msg = data.get("choices", [{}])[0].get("message", {})
            msg["_usage"] = data.get("usage", {})
            return msg
        except httpx.HTTPStatusError as e:
            logger.error(f"R1推理HTTP错误: {e.response.status_code} | {e.response.text[:300]}")
            raise RuntimeError(f"DeepSeek-R1调用失败({e.response.status_code}): {e.response.text[:200]}")
        except httpx.TimeoutException:
            logger.error("R1推理请求超时（推理时间过长，可正常现象）")
            raise RuntimeError("DeepSeek-R1响应超时，70B模型推理较慢，建议增大 REASONING_MODEL_TIMEOUT")

    # ── 工具方法 ─────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_text(resp: Dict[str, Any]) -> str:
        """从 OpenAI 格式响应中提取文本"""
        try:
            return resp["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError):
            return ""

    @staticmethod
    def _build_full_report(
        scene: VisionScene,
        vision_text: str,
        reasoning_text: str,
        conclusion_text: str,
    ) -> str:
        scene_labels = {
            VisionScene.CROP_DISEASE:   "作物病害深度诊断报告",
            VisionScene.GROWTH_STATUS:  "作物生长状态分析报告",
            VisionScene.PEST_DETECTION: "病虫害检测报告",
            VisionScene.ENVIRONMENT:    "农业环境分析报告",
            VisionScene.GENERAL:        "综合视觉分析报告",
        }
        title = scene_labels.get(scene, "视觉推理报告")
        sep = "─" * 60

        parts = [f"# {title}\n", f"{sep}\n## 一、视觉AI观察（Step 1）\n{vision_text}\n"]
        if reasoning_text:
            parts.append(f"{sep}\n## 二、DeepSeek-R1 推理过程（Step 2 CoT）\n{reasoning_text}\n")
        parts.append(f"{sep}\n## 三、最终分析结论\n{conclusion_text}\n")
        return "\n".join(parts)

    async def close(self):
        """关闭连接"""
        for c in [self._vision_client, self._reasoning_client]:
            if c and not c.is_closed:
                await c.aclose()


# ── 全局单例 ─────────────────────────────────────────────────────────────────
_pipeline: Optional[VisionReasoningPipeline] = None


def get_vision_pipeline() -> VisionReasoningPipeline:
    """FastAPI 依赖注入入口"""
    global _pipeline
    if _pipeline is None:
        _pipeline = VisionReasoningPipeline()
    return _pipeline
