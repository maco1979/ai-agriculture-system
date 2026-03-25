"""
LLM 路由层 — 方案A：推理层 + 执行层分离

路由策略：
  - 复杂分析/诊断/报告  → deepseek-r1:70b（推理模型，无工具调用）
  - 工具调用/OpenClaw   → qwen2.5:32b（执行模型，支持tools）
  - auto 模式           → 关键词自动分流
"""

import httpx
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from enum import Enum

from ..config.config import settings

logger = logging.getLogger(__name__)


class ModelRole(str, Enum):
    REASONING = "reasoning"   # 推理模型：deepseek-r1
    AGENT = "agent"           # 执行模型：qwen2.5（支持tools）


class LLMRouter:
    """
    双模型路由器
    - 自动判断请求类型，分发到合适的模型
    - reasoning_model: deepseek-r1:70b  用于深度分析（无tools）
    - agent_model:     qwen2.5:32b      用于工具调用/OpenClaw（有tools）
    """

    def __init__(self):
        self.reasoning_client = httpx.AsyncClient(
            base_url=settings.reasoning_model_url,
            timeout=settings.reasoning_model_timeout,
        )
        self.agent_client = httpx.AsyncClient(
            base_url=settings.agent_model_url,
            timeout=settings.agent_model_timeout,
        )
        logger.info(
            f"LLM路由器已初始化 | 推理层: {settings.reasoning_model} "
            f"| 执行层: {settings.agent_model} "
            f"| 路由模式: {settings.llm_routing_mode}"
        )

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
        force_role: Optional[ModelRole] = None,
    ) -> Dict[str, Any]:
        """
        统一聊天接口，自动路由到合适的模型。

        参数：
          messages    : OpenAI 格式消息列表
          tools       : 工具定义（有tools时强制走执行模型）
          stream      : 是否流式
          force_role  : 强制指定模型角色（跳过自动路由）
        """
        role = force_role or self._route(messages, tools)
        logger.info(f"路由决策: {role.value}")

        if role == ModelRole.REASONING:
            return await self._call_reasoning(messages, stream)
        else:
            return await self._call_agent(messages, tools, stream)

    async def analyze(self, prompt: str, context: str = "") -> str:
        """
        快捷接口：直接调用推理模型做深度分析，返回纯文本结果。
        适用场景：农业病害分析、生长预测、决策报告生成等。
        """
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        result = await self._call_reasoning(messages, stream=False)
        return self._extract_text(result)

    async def execute(
        self,
        prompt: str,
        tools: Optional[List[Dict]] = None,
        system: str = "",
    ) -> Dict[str, Any]:
        """
        快捷接口：调用执行模型（支持工具调用）。
        适用场景：OpenClaw Skills、摄像头控制、模型管理等。
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        return await self._call_agent(messages, tools, stream=False)

    # ------------------------------------------------------------------
    # 路由逻辑
    # ------------------------------------------------------------------

    def _route(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]],
    ) -> ModelRole:
        """根据请求内容自动决定使用哪个模型"""

        # 有工具定义 → 必须走执行模型（推理模型不支持tools）
        if tools:
            logger.debug("检测到 tools 参数，路由到执行模型")
            return ModelRole.AGENT

        # 强制模式
        if settings.llm_routing_mode == "reasoning_only":
            return ModelRole.REASONING
        if settings.llm_routing_mode == "agent_only":
            return ModelRole.AGENT

        # auto 模式：关键词匹配
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        for keyword in settings.reasoning_keywords:
            if keyword in last_user_msg:
                logger.debug(f"关键词命中 '{keyword}'，路由到推理模型")
                return ModelRole.REASONING

        # 默认走执行模型（更快、支持tools）
        return ModelRole.AGENT

    # ------------------------------------------------------------------
    # 内部调用
    # ------------------------------------------------------------------

    async def _call_reasoning(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
    ) -> Dict[str, Any]:
        """调用推理模型 deepseek-r1（不传 tools）"""
        payload = {
            "model": settings.reasoning_model,
            "messages": messages,
            "max_tokens": settings.reasoning_max_tokens,
            "stream": stream,
        }
        try:
            resp = await self.reasoning_client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"推理模型响应成功，usage={data.get('usage', {})}")
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"推理模型请求失败: {e.response.status_code} {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"推理模型异常: {e}")
            raise

    async def _call_agent(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """调用执行模型 qwen2.5（可传 tools）"""
        payload: Dict[str, Any] = {
            "model": settings.agent_model,
            "messages": messages,
            "max_tokens": settings.agent_max_tokens,
            "stream": stream,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            resp = await self.agent_client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"执行模型响应成功，usage={data.get('usage', {})}")
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"执行模型请求失败: {e.response.status_code} {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"执行模型异常: {e}")
            raise

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(response: Dict[str, Any]) -> str:
        """从 OpenAI 格式响应中提取纯文本内容"""
        try:
            choices = response.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                # deepseek-r1 的 reasoning_content（思维链）会单独返回
                reasoning = msg.get("reasoning_content", "")
                content = msg.get("content", "")
                if reasoning and content:
                    return f"【推理过程】\n{reasoning}\n\n【结论】\n{content}"
                return content or reasoning
        except Exception:
            pass
        return ""

    def get_routing_info(self) -> Dict[str, Any]:
        """返回当前路由配置信息（用于调试/监控）"""
        return {
            "routing_mode": settings.llm_routing_mode,
            "reasoning_model": settings.reasoning_model,
            "reasoning_model_url": settings.reasoning_model_url,
            "agent_model": settings.agent_model,
            "agent_model_url": settings.agent_model_url,
            "reasoning_keywords": settings.reasoning_keywords,
        }

    async def close(self):
        """关闭 HTTP 连接"""
        await self.reasoning_client.aclose()
        await self.agent_client.aclose()


# 全局路由器实例（懒加载）
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """获取全局 LLM 路由器（FastAPI 依赖注入用）"""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
