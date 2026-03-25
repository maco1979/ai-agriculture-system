"""
云端 AI 对话路由
提供统一的 AI 问答接口，调用用户配置的云端模型（DeepSeek/OpenAI/混元等）
无需认证，开箱即用
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from src.core.services.cloud_ai_service import chat_completion, get_model_info

router = APIRouter(prefix="/ai", tags=["AI对话"])


class ChatRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000


class AgricultureRequest(BaseModel):
    """农业决策请求"""
    crop: Optional[str] = None          # 作物名称
    symptom: Optional[str] = None       # 症状描述
    question: str                       # 问题


@router.get("/model-info")
async def model_info():
    """获取当前配置的 AI 模型信息"""
    return get_model_info()


@router.post("/chat")
async def ai_chat(req: ChatRequest):
    """
    通用 AI 对话接口
    自动使用用户在 .env 中配置的云端模型
    """
    result = await chat_completion(
        prompt=req.prompt,
        system_prompt=req.system_prompt or "你是一个专业的AI农业决策助手。",
        temperature=req.temperature,
        max_tokens=req.max_tokens,
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
