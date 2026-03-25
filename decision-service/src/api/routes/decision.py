"""
决策API路由
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ...core.llm_router import LLMRouter, ModelRole, get_llm_router

router = APIRouter(prefix="/decision", tags=["决策"])


class DecisionRequest(BaseModel):
    """决策请求模型"""
    input_data: Dict[str, Any]
    model_type: str = "default"
    confidence_threshold: float = 0.7


class DecisionResponse(BaseModel):
    """决策响应模型"""
    decision: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any]


class ModelInfo(BaseModel):
    """模型信息模型"""
    name: str
    version: str
    status: str
    accuracy: float


# ── 新增：深度推理相关模型 ──────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """深度分析请求（路由到 DeepSeek-R1）"""
    prompt: str
    context: Optional[str] = ""
    force_reasoning: bool = False   # True=强制用推理模型，False=自动路由


class AnalyzeResponse(BaseModel):
    """深度分析响应"""
    result: str
    model_used: str
    role: str   # "reasoning" 或 "agent"


class LLMRoutingInfo(BaseModel):
    """LLM 路由配置信息"""
    routing_mode: str
    reasoning_model: str
    reasoning_model_url: str
    agent_model: str
    agent_model_url: str
    reasoning_keywords: List[str]


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "decision-service"}


@router.get("/models")
async def get_models() -> List[ModelInfo]:
    """获取可用模型列表"""
    return [
        ModelInfo(
            name="agriculture_decision_model",
            version="1.0.0",
            status="active",
            accuracy=0.95
        ),
        ModelInfo(
            name="resource_optimization_model",
            version="1.0.0",
            status="active",
            accuracy=0.92
        ),
        ModelInfo(
            name="risk_assessment_model",
            version="1.0.0",
            status="active",
            accuracy=0.88
        )
    ]


@router.post("/predict", response_model=DecisionResponse)
async def make_decision(request: DecisionRequest) -> DecisionResponse:
    """进行决策预测"""
    try:
        # 模拟决策逻辑
        input_data = request.input_data
        
        # 根据输入数据生成决策
        if "agriculture" in request.model_type:
            decision = "种植建议: 适合种植小麦"
            confidence = 0.95
            reasoning = "基于土壤分析和气候数据，小麦种植条件最优"
        elif "resource" in request.model_type:
            decision = "资源分配: 优先分配水资源"
            confidence = 0.92
            reasoning = "水资源紧张，优先保障农业用水"
        elif "risk" in request.model_type:
            decision = "风险评估: 低风险"
            confidence = 0.88
            reasoning = "当前环境条件稳定，风险较低"
        else:
            decision = "默认决策: 继续监控"
            confidence = 0.8
            reasoning = "数据不足，建议继续收集数据"
        
        # 确保置信度不低于阈值
        if confidence < request.confidence_threshold:
            decision = "决策: 需要更多数据"
            confidence = request.confidence_threshold
            reasoning = "置信度过低，建议收集更多数据"
        
        return DecisionResponse(
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "model_used": request.model_type,
                "input_size": len(str(input_data)),
                "processing_time": "0.1s"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"决策处理错误: {str(e)}")


@router.get("/status")
async def get_service_status():
    """获取服务状态"""
    return {
        "service": "decision-service",
        "status": "running",
        "version": "1.0.0",
        "models_available": 3,
        "uptime": "24h"
    }


# ── 新增：双模型路由接口 ────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
async def deep_analyze(
    request: AnalyzeRequest,
    llm: LLMRouter = Depends(get_llm_router),
):
    """
    深度分析接口（路由到 DeepSeek-R1 推理模型）

    适用场景：
    - 农业病害深度诊断
    - 作物生长预测分析
    - 多因素农业决策报告
    - 复杂问题原因分析
    """
    try:
        force_role = ModelRole.REASONING if request.force_reasoning else None
        messages = []
        if request.context:
            messages.append({"role": "system", "content": request.context})
        messages.append({"role": "user", "content": request.prompt})

        response = await llm.chat(
            messages=messages,
            tools=None,       # 推理模型不传 tools
            force_role=force_role,
        )

        # 提取模型信息
        model_used = response.get("model", "unknown")
        role = "reasoning" if "deepseek" in model_used.lower() else "agent"
        result = llm._extract_text(response)

        return AnalyzeResponse(
            result=result,
            model_used=model_used,
            role=role,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"深度分析失败: {str(e)}")


@router.post("/execute")
async def execute_with_tools(
    prompt: str,
    system: str = "",
    llm: LLMRouter = Depends(get_llm_router),
):
    """
    工具执行接口（路由到 qwen2.5 执行模型，支持 OpenClaw tools）

    适用场景：
    - 调用摄像头/PTZ控制
    - 触发模型训练/推理
    - 系统监控告警处理
    """
    try:
        result = await llm.execute(prompt=prompt, system=system)
        return {
            "result": llm._extract_text(result),
            "model_used": result.get("model", "unknown"),
            "role": "agent",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.get("/llm-routing", response_model=LLMRoutingInfo)
async def get_llm_routing(llm: LLMRouter = Depends(get_llm_router)):
    """
    查看当前 LLM 路由配置
    - 显示推理模型和执行模型的配置
    - 显示自动路由关键词列表
    """
    return llm.get_routing_info()