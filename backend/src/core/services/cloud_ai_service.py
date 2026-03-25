"""
AI 模型服务
支持本地 Ollama（qwen2.5/deepseek-r1/minicpm-v）及云端 OpenAI / DeepSeek / 混元 / 通义 等 API
优先级：Ollama（本地）> OpenAI > DeepSeek > 混元 > 通义 > 智谱
"""

import os
import logging
from typing import Optional, AsyncGenerator

logger = logging.getLogger(__name__)

# ── 支持的模型提供商 ───────────────────────────────────
PROVIDER_OLLAMA    = "ollama"     # 本地 Ollama（最高优先级）
PROVIDER_OPENAI    = "openai"
PROVIDER_DEEPSEEK  = "deepseek"
PROVIDER_HUNYUAN   = "hunyuan"    # 腾讯混元
PROVIDER_QWEN      = "qwen"       # 阿里通义
PROVIDER_ZHIPU     = "zhipu"      # 智谱 GLM

# Ollama 默认配置
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434/v1"
OLLAMA_DEFAULT_MODEL    = "qwen2.5:14b"


def get_provider() -> str:
    """
    从环境变量检测当前使用的模型提供商
    优先级：OLLAMA > OPENAI > DEEPSEEK > HUNYUAN > QWEN > ZHIPU
    """
    # Ollama 本地优先：只要 OLLAMA_ENABLED=true 或检测到 OLLAMA_MODEL 就启用
    if os.getenv("OLLAMA_ENABLED", "").lower() in ("true", "1", "yes"):
        return PROVIDER_OLLAMA
    if os.getenv("OLLAMA_MODEL"):
        return PROVIDER_OLLAMA
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
    model_override: Optional[str] = None,
) -> dict:
    """
    统一模型对话接口
    自动根据配置选择本地 Ollama 或云端 API
    model_override: 强制使用指定模型名（仅 Ollama 模式生效，如 'deepseek-r1:70b'）
    """
    provider = get_provider()

    if provider == "none":
        return {
            "success": False,
            "error": "未配置 AI 模型。本地用户请在 .env 中设置 OLLAMA_ENABLED=true，云端用户请设置 DEEPSEEK_API_KEY。",
            "hint": "本地部署：设置 OLLAMA_ENABLED=true（需先运行 ollama serve）\n云端 API：访问 https://platform.deepseek.com 获取 Key"
        }

    try:
        if provider == PROVIDER_OLLAMA:
            return await _ollama_chat(prompt, system_prompt, temperature, max_tokens, model_override)
        elif provider in (PROVIDER_OPENAI, PROVIDER_DEEPSEEK):
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
        logger.error(f"AI 调用失败 ({provider}): {e}")
        return {"success": False, "error": str(e)}
    return {"success": False, "error": "未知 provider"}


async def _ollama_chat(
    prompt: str,
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    model_override: Optional[str] = None,
) -> dict:
    """
    本地 Ollama 调用（OpenAI 兼容接口）
    支持 qwen2.5:14b / deepseek-r1:70b / minicpm-v 等本地模型
    """
    try:
        from openai import AsyncOpenAI
    except ImportError:
        return {"success": False, "error": "请安装 openai 包：pip install openai"}

    base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_DEFAULT_BASE_URL)
    model = model_override or os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)

    # Ollama 本地接口不需要真实 api_key，填任意非空字符串
    client = AsyncOpenAI(
        api_key="ollama",
        base_url=base_url,
    )

    try:
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
        usage = response.usage
        return {
            "success": True,
            "content": content,
            "model": model,
            "provider": PROVIDER_OLLAMA,
            "local": True,
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            }
        }
    except Exception as e:
        err = str(e)
        if "connection" in err.lower() or "refused" in err.lower():
            return {
                "success": False,
                "error": f"无法连接到 Ollama ({base_url})，请确认 ollama serve 已启动",
                "hint": "运行命令：ollama serve"
            }
        return {"success": False, "error": f"Ollama 调用失败: {err}"}


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
        PROVIDER_OLLAMA:   "本地 Ollama",
        PROVIDER_OPENAI:   "OpenAI",
        PROVIDER_DEEPSEEK: "DeepSeek",
        PROVIDER_HUNYUAN:  "腾讯混元",
        PROVIDER_QWEN:     "阿里通义千问",
        PROVIDER_ZHIPU:    "智谱 GLM",
        "none":            "未配置",
    }
    models = {
        PROVIDER_OLLAMA:   os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL),
        PROVIDER_OPENAI:   os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        PROVIDER_DEEPSEEK: os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        PROVIDER_HUNYUAN:  os.getenv("HUNYUAN_MODEL", "hunyuan-standard"),
        PROVIDER_QWEN:     os.getenv("QWEN_MODEL", "qwen-plus"),
        PROVIDER_ZHIPU:    os.getenv("ZHIPU_MODEL", "glm-4-flash"),
        "none":            "N/A",
    }
    info = {
        "provider": provider,
        "provider_name": provider_names.get(provider, provider),
        "model": models.get(provider, "N/A"),
        "configured": provider != "none",
        "local": provider == PROVIDER_OLLAMA,
    }
    if provider == PROVIDER_OLLAMA:
        info["base_url"] = os.getenv("OLLAMA_BASE_URL", OLLAMA_DEFAULT_BASE_URL)
    return info


async def list_ollama_models() -> dict:
    """列出本地 Ollama 已安装的所有模型"""
    try:
        import httpx
        base = os.getenv("OLLAMA_BASE_URL", OLLAMA_DEFAULT_BASE_URL).rstrip("/v1").rstrip("/")
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return {"success": True, "models": models, "base_url": base}
            return {"success": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e), "hint": "请确认 ollama serve 已启动"}
