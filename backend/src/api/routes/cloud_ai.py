"""
AI 对话路由（本地 Ollama + 云端 API）
支持本地 Ollama（qwen2.5/deepseek-r1/minicpm-v）及各大云端模型，无需认证，开箱即用
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from src.core.services.cloud_ai_service import (
    chat_completion, get_model_info, list_ollama_models
)

router = APIRouter(prefix="/ai", tags=["AI对话"])


class ChatRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    model: Optional[str] = None   # 可选：指定 Ollama 模型，如 deepseek-r1:70b


class AgricultureRequest(BaseModel):
    """农业决策请求"""
    crop: Optional[str] = None          # 作物名称
    symptom: Optional[str] = None       # 症状描述
    question: str                       # 问题


@router.get("/model-info")
async def model_info():
    """获取当前配置的 AI 模型信息"""
    return get_model_info()


@router.get("/local-models")
async def local_models():
    """
    列出本地 Ollama 已安装的模型
    需要 ollama serve 正在运行
    """
    return await list_ollama_models()


@router.post("/test-local")
async def test_local_model(model: Optional[str] = None):
    """
    一键测试本地 Ollama 连通性
    - model: 指定要测试的模型名，默认使用 OLLAMA_MODEL
    - 返回测试结果和响应时间
    """
    import time
    import os
    from src.core.services.cloud_ai_service import OLLAMA_DEFAULT_MODEL

    target_model = model or os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)
    start = time.time()

    # 先检查 Ollama 服务本身
    models_result = await list_ollama_models()
    if not models_result.get("success"):
        return {
            "success": False,
            "error": "Ollama 服务未启动",
            "hint": "请运行: ollama serve",
            "detail": models_result.get("error", ""),
        }

    installed = models_result.get("models", [])
    # 检查目标模型是否已安装
    model_available = any(
        target_model == m or target_model.split(":")[0] == m.split(":")[0]
        for m in installed
    )
    if not model_available:
        return {
            "success": False,
            "error": f"模型 '{target_model}' 未安装",
            "installed_models": installed,
            "hint": f"请运行: ollama pull {target_model}",
        }

    # 发一条简单测试消息
    result = await chat_completion(
        prompt="用一句话介绍你自己（包括模型名称）。",
        system_prompt="你是一个农业 AI 助手，请简短回答。",
        temperature=0.3,
        max_tokens=100,
        model_override=target_model,
    )
    elapsed = round(time.time() - start, 2)

    return {
        "success": result.get("success", False),
        "model_tested": target_model,
        "installed_models": installed,
        "elapsed_seconds": elapsed,
        "response": result.get("content", ""),
        "error": result.get("error", None),
    }


@router.post("/chat")
async def ai_chat(req: ChatRequest):
    """
    通用 AI 对话接口
    自动使用配置的模型（本地 Ollama 或云端 API）
    支持 model 字段指定具体 Ollama 模型，如 deepseek-r1:70b
    """
    result = await chat_completion(
        prompt=req.prompt,
        system_prompt=req.system_prompt or "你是一个专业的AI农业决策助手。",
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        model_override=req.model,
    )
    return result


@router.post("/agriculture/decision")
async def agriculture_decision(req: AgricultureRequest):
    """
    农业决策接口
    根据作物、症状等信息给出专业建议
    """
    parts = [f"用户问题：{req.question}"]
    if req.crop:
        parts.append(f"作物类型：{req.crop}")
    if req.symptom:
        parts.append(f"症状描述：{req.symptom}")

    prompt = "\n".join(parts)

    result = await chat_completion(
        prompt=prompt,
        system_prompt=(
            "你是一个专业的AI农业决策助手，具备作物栽培、病虫害防治、"
            "施肥灌溉、农业气象等专业知识。请给出具体、实用、可执行的建议。"
            "回答格式：先给出诊断/分析，再给出具体操作建议，最后注明注意事项。"
        ),
        temperature=0.6,
        max_tokens=2000,
    )
    return result


@router.post("/agriculture/plant-disease")
async def diagnose_disease(req: AgricultureRequest):
    """病虫害诊断"""
    prompt = f"作物：{req.crop or '未知'}\n症状：{req.symptom or req.question}"

    result = await chat_completion(
        prompt=prompt,
        system_prompt=(
            "你是农业病虫害专家。根据描述的症状，给出：\n"
            "1. 可能的病害/虫害名称\n"
            "2. 确认诊断的方法\n"
            "3. 防治方案（优先推荐生物防治和低毒农药）\n"
            "4. 预防措施"
        ),
        temperature=0.5,
        max_tokens=1500,
    )
    return result


@router.post("/agriculture/fertilization")
async def fertilization_advice(req: AgricultureRequest):
    """施肥方案建议"""
    result = await chat_completion(
        prompt=req.question,
        system_prompt=(
            "你是农业施肥专家。根据用户描述，给出科学施肥方案，包括：\n"
            "1. 推荐肥料种类和配比\n"
            "2. 施肥时间和方法\n"
            "3. 用量建议\n"
            "4. 注意事项（避免过量、烧苗等）"
        ),
        temperature=0.5,
        max_tokens=1500,
    )
    return result
