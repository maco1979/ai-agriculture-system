"""
聊天路由 - 统一聊天接口，支持流式输出
对应前端 /chat 页面的对话功能
"""
from __future__ import annotations

import json
import time
import asyncio
from typing import Optional, List, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


# ─── 请求/响应模型 ───
class ChatMessage(BaseModel):
    role: str          # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    model: str = "deepseek-chat"
    messages: List[ChatMessage]
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int = 2048
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    id: str
    model: str
    content: str
    finish_reason: str = "stop"
    usage: dict = {}


# ─── 流式 SSE 生成器 ───
async def _stream_response(
    messages: List[ChatMessage],
    model: str,
    temperature: float,
    max_tokens: int,
) -> AsyncGenerator[str, None]:
    """尝试调用真实云端 AI，失败时降级到模拟流式输出"""
    
    try:
        # 尝试调用云端 AI 服务
        from core.services.cloud_ai_service import CloudAIService
        service = CloudAIService()
        
        last_content = ""
        async for chunk in service.stream_chat(
            messages=[m.dict() for m in messages],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            delta = chunk[len(last_content):]
            last_content = chunk
            if delta:
                data = json.dumps({"delta": delta, "finish_reason": None}, ensure_ascii=False)
                yield f"data: {data}\n\n"
                await asyncio.sleep(0)
        
        yield f"data: {json.dumps({'delta': '', 'finish_reason': 'stop'})}\n\n"
        yield "data: [DONE]\n\n"

    except Exception:
        # 降级：模拟农业AI回复
        reply = _mock_reply(messages[-1].content if messages else "", model)
        for char in reply:
            data = json.dumps({"delta": char, "finish_reason": None}, ensure_ascii=False)
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.01)
        
        yield f"data: {json.dumps({'delta': '', 'finish_reason': 'stop'})}\n\n"
        yield "data: [DONE]\n\n"


def _mock_reply(user_input: str, model: str) -> str:
    """后备模拟回复（云端服务不可用时）"""
    lower = user_input.lower()
    
    if any(k in lower for k in ["施肥", "肥料", "fertiliz"]):
        return (
            "## 精准施肥建议\n\n"
            "根据通用农业标准，建议施肥方案如下：\n\n"
            "**基础配比（每亩）：**\n"
            "- 氮肥（N）：15-20 kg\n"
            "- 磷肥（P₂O₅）：8-12 kg\n"
            "- 钾肥（K₂O）：10-15 kg\n\n"
            "> 注意：实际用量请结合土壤检测报告调整。"
        )
    elif any(k in lower for k in ["病虫", "病害", "虫害", "disease", "pest"]):
        return (
            "## 病虫害防治建议\n\n"
            "常见病虫害识别与防治：\n\n"
            "1. **稻瘟病** - 叶片出现褐色病斑，建议喷施三环唑\n"
            "2. **白叶枯病** - 叶缘枯黄，需控制水量+喷施叶枯唑\n"
            "3. **螟虫** - 茎秆中空，建议使用杀螟硫磷\n\n"
            "建议结合实地图像进行 AI 视觉诊断以获取更精准结果。"
        )
    elif any(k in lower for k in ["灌溉", "浇水", "water", "irrigat"]):
        return (
            "## 灌溉管理建议\n\n"
            "**基本原则：**\n"
            "- 旱地作物：土壤含水量低于 60% 时补水\n"
            "- 水稻：保持 2-3cm 浅水层\n"
            "- 蔬菜：少量多次，避免积水\n\n"
            "推荐接入土壤湿度传感器实现精准自动灌溉。"
        )
    else:
        return (
            f"您好！我是农业 AI 助手（{model}）。\n\n"
            "我可以帮助您解决：\n"
            "- 🌱 作物病虫害诊断\n"
            "- 💧 精准灌溉方案\n"
            "- 🌾 施肥优化建议\n"
            "- 📊 农业数据分析\n\n"
            "请告诉我您遇到的具体问题，我来为您提供专业建议！"
        )


# ─── 路由定义 ───

@router.post("/completions")
async def chat_completions(req: ChatRequest):
    """
    统一聊天接口
    - stream=true 时返回 SSE 流式响应
    - stream=false 时返回完整 JSON
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages 不能为空")

    if req.stream:
        return StreamingResponse(
            _stream_response(req.messages, req.model, req.temperature, req.max_tokens),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # 非流式：收集完整回复
    try:
        from core.services.cloud_ai_service import CloudAIService
        service = CloudAIService()
        content = await service.chat(
            messages=[m.dict() for m in req.messages],
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
    except Exception:
        content = _mock_reply(req.messages[-1].content if req.messages else "", req.model)

    return ChatResponse(
        id=f"chatcmpl-{int(time.time())}",
        model=req.model,
        content=content,
        finish_reason="stop",
    )


@router.get("/models")
async def list_chat_models():
    """返回可用的聊天模型列表"""
    return {
        "models": [
            {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "DeepSeek", "tag": "推荐"},
            {"id": "deepseek-reasoner", "name": "DeepSeek R1", "provider": "DeepSeek", "tag": "推理"},
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "OpenAI"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "OpenAI", "tag": "快速"},
            {"id": "claude-3-5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "Anthropic"},
            {"id": "hunyuan-lite", "name": "混元 Lite", "provider": "腾讯"},
            {"id": "qwen-plus", "name": "通义千问 Plus", "provider": "阿里"},
            {"id": "glm-4", "name": "GLM-4", "provider": "智谱"},
            {"id": "agriculture-local", "name": "农业专用模型", "provider": "本地", "tag": "本地"},
        ]
    }
