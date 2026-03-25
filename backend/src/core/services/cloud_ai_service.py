"""
云端 AI 模型服务
支持 OpenAI / DeepSeek / 混元 / 通义 等主流云端模型 API
用户只需在 .env 中填入自己的 API Key，不需要本地安装任何 AI 模型
"""

import os
import logging
from typing import Optional, AsyncGenerator

logger = logging.getLogger(__name__)

# ── 支持的模型提供商 ───────────────────────────────────
PROVIDER_OPENAI    = "openai"
PROVIDER_DEEPSEEK  = "deepseek"
PROVIDER_HUNYUAN   = "hunyuan"    # 腾讯混元
PROVIDER_QWEN      = "qwen"       # 阿里通义
PROVIDER_ZHIPU     = "zhipu"      # 智谱 GLM


def get_provider() -> str:
    """从环境变量检测当前使用的模型提供商"""
    if os.getenv("OPENAI_API_KEY"):
        return PROVIDER_OPENAI
    if os.getenv("DEEPSEEK_API_KEY"):
        return PROVIDER_DEEPSEEK
    if os.getenv("HUNYUAN_API_KEY"):
        return PROVIDER_HUNYUAN
    if os.getenv("QWEN_API_KEY"):
        return PROVIDER_QWEN
    if os.getenv("ZHIPU_API_KEY"):
        return PROVIDER_ZHIPU
    return "none"


async def chat_completion(
    prompt: str,
    system_prompt: str = "你是一个专业的AI农业决策助手，帮助用户解决作物种植、病虫害防治、施肥灌溉等农业问题。",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> dict:
    """
    统一的云端模型对话接口
    自动根据配置的 API Key 选择合适的提供商
    """
    provider = get_provider()

    if provider == "none":
        return {
            "success": False,
            "error": "未配置 AI 模型 API Key。请在 .env 文件中设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY。",
            "hint": "访问 https://platform.deepseek.com 免费获取 API Key（推荐，价格低廉）"
        }

    try:
        if provider in (PROVIDER_OPENAI, PROVIDER_DEEPSEEK):
            return await _openai_compatible_chat(
                prompt, system_prompt, temperature, max_tokens, provider
            )
        elif provider == PROVIDER_HUNYUAN:
            return await _hunyuan_chat(prompt, system_prompt, temperature, max_tokens)
        elif provider == PROVIDER_QWEN:
            return await _qwen_chat(prompt, system_prompt, temperature, max_tokens)
        elif provider == PROVIDER_ZHIPU:
            return await _zhipu_chat(prompt, system_prompt, temperature, max_tokens)
    except Exception as e:
        logger.error(f"云端 AI 调用失败 ({provider}): {e}")
        return {"success": False, "error": str(e)}


async def _openai_compatible_chat(
    prompt: str, system_prompt: str, temperature: float, max_tokens: int, provider: str
) -> dict:
    """
    OpenAI 兼容接口（OpenAI / DeepSeek 均使用此格式）
    """
    try:
        from openai import AsyncOpenAI
    except ImportError:
        return {"success": False, "error": "请安装 openai 包：pip install openai"}

    if provider == PROVIDER_DEEPSEEK:
        client = AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1",
        )
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    else:
        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    content = response.choices[0].message.content
    return {
        "success": True,
        "content": content,
        "model": model,
        "provider": provider,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
    }


async def _hunyuan_chat(
    prompt: str, system_prompt: str, temperature: float, max_tokens: int
) -> dict:
    """腾讯混元 API"""
    try:
        from tencentcloud.common import credential
        from tencentcloud.hunyuan.v20230901 import hunyuan_client, models as hm
    except ImportError:
        return {"success": False, "error": "请安装腾讯云 SDK：pip install tencentcloud-sdk-python-hunyuan"}

    secret_id = os.getenv("HUNYUAN_SECRET_ID", "")
    secret_key = os.getenv("HUNYUAN_API_KEY", "")
    cred = credential.Credential(secret_id, secret_key)
    client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou")

    req = hm.ChatCompletionsRequest()
    req.Model = os.getenv("HUNYUAN_MODEL", "hunyuan-standard")
    req.Messages = [
        {"Role": "system", "Content": system_prompt},
        {"Role": "user", "Content": prompt},
    ]
    req.Temperature = temperature

    resp = client.ChatCompletions(req)
    content = resp.Choices[0].Message.Content
    return {
        "success": True,
        "content": content,
        "model": req.Model,
        "provider": PROVIDER_HUNYUAN,
    }


async def _qwen_chat(
    prompt: str, system_prompt: str, temperature: float, max_tokens: int
) -> dict:
    """阿里通义千问 API（OpenAI 兼容模式）"""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        return {"success": False, "error": "请安装 openai 包：pip install openai"}

    client = AsyncOpenAI(
        api_key=os.getenv("QWEN_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    model = os.getenv("QWEN_MODEL", "qwen-plus")

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return {
        "success": True,
        "content": response.choices[0].message.content,
        "model": model,
        "provider": PROVIDER_QWEN,
    }


async def _zhipu_chat(
    prompt: str, system_prompt: str, temperature: float, max_tokens: int
) -> dict:
    """智谱 GLM API"""
    try:
        from zhipuai import ZhipuAI
    except ImportError:
        return {"success": False, "error": "请安装智谱 SDK：pip install zhipuai"}

    client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))
    model = os.getenv("ZHIPU_MODEL", "glm-4-flash")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return {
        "success": True,
        "content": response.choices[0].message.content,
        "model": model,
        "provider": PROVIDER_ZHIPU,
    }


def get_model_info() -> dict:
    """返回当前配置的模型信息（供前端展示）"""
    provider = get_provider()
    provider_names = {
        PROVIDER_OPENAI:   "OpenAI",
        PROVIDER_DEEPSEEK: "DeepSeek",
        PROVIDER_HUNYUAN:  "腾讯混元",
        PROVIDER_QWEN:     "阿里通义千问",
        PROVIDER_ZHIPU:    "智谱 GLM",
        "none":            "未配置",
    }
    models = {
        PROVIDER_OPENAI:   os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        PROVIDER_DEEPSEEK: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        PROVIDER_HUNYUAN:  os.getenv("HUNYUAN_MODEL", "hunyuan-standard"),
        PROVIDER_QWEN:     os.getenv("QWEN_MODEL", "qwen-plus"),
        PROVIDER_ZHIPU:    os.getenv("ZHIPU_MODEL", "glm-4-flash"),
        "none":            "N/A",
    }
    return {
        "provider": provider,
        "provider_name": provider_names.get(provider, provider),
        "model": models.get(provider, "N/A"),
        "configured": provider != "none",
    }
