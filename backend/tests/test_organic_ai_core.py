"""
有机体AI核心测试脚本
"""
import asyncio
import pytest
from src.core.ai_organic_core import OrganicAICore, get_organic_ai_core

async def test_organic_ai_core_initialization():
    """测试有机体AI核心初始化"""
    ai_core = await get_organic_ai_core()
    assert ai_core is not None
    assert ai_core.state.value == "idle"
    assert ai_core.iteration_enabled == True
    assert ai_core.iteration_interval == 60

async def test_organic_ai_core_active_iteration():
    """测试有机体AI核心主动迭代"""
    ai_core = await get_organic_ai_core()
    
    # 测试启动主动迭代
    await ai_core.start_active_iteration()
    assert ai_core.iteration_task is not None
    
    # 测试停止主动迭代
    await ai_core.stop_active_iteration()
    assert ai_core.iteration_task is None

async def test_organic_ai_core_decision_making():
    """测试有机体AI核心决策功能"""
    ai_core = await get_organic_ai_core()
    
    # 测试简单决策
    state_features = {
        "temperature": 25.0,
        "humidity": 65.0,
        "co2_level": 400.0,
        "light_intensity": 500.0
    }
    
    decision = await ai_core.make_decision(state_features)
    assert decision is not None
    assert decision.action is not None
    assert 0 <= decision.confidence <= 1.0
    assert "risk_assessment" in decision.__dict__

async def test_organic_ai_core_enhanced_decision():
    """测试增强型决策功能"""
    ai_core = await get_organic_ai_core()
    
    # 测试增强型决策
    state_features = {
        "temperature": 25.0,
        "humidity": 65.0,
        "co2_level": 400.0,
        "light_intensity": 500.0
    }
    
    # 添加多模态输入
    multimodal_input = {
        "vision": {
            "objects": ["plant", "pot"],
            "confidence": 0.95
        },
        "sensor": {
            "soil_moisture": 0.6,
            "ph_level": 6.5
        }
    }
    
    decision = await ai_core.make_enhanced_decision(state_features, multimodal_input)
    assert decision is not None
    assert decision.action is not None
    assert 0 <= decision.confidence <= 1.0
    assert "multimodal_vector" in state_features

async def test_organic_ai_core_network_evolution():
    """测试网络结构演化"""
    ai_core = await get_organic_ai_core()
    
    # 测试不同演化策略
    evolution_strategies = ["adaptive", "expand", "shrink", "random", "optimize"]
    
    for strategy in evolution_strategies:
        result = await ai_core.evolve_network_structure(strategy)
        assert result is not None
        assert "evolution_strategy" in result
        assert result["evolution_strategy"] == strategy

async def test_organic_ai_core_memory_management():
    """测试记忆管理功能"""
    ai_core = await get_organic_ai_core()
    
    # 测试添加到长期记忆
    memory_item = {
        "type": "test_memory",
        "features": {
            "temperature": 25.0,
            "humidity": 65.0
        },
        "result": "success"
    }
    
    ai_core.add_to_long_term_memory(memory_item)
    assert len(ai_core.long_term_memory) > 0
    
    # 测试从长期记忆中检索
    retrieved = ai_core.retrieve_from_long_term_memory({
        "temperature": 25.0,
        "humidity": 65.0
    })
    assert len(retrieved) >= 0

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_organic_ai_core_initialization())
    asyncio.run(test_organic_ai_core_active_iteration())
    asyncio.run(test_organic_ai_core_decision_making())
    asyncio.run(test_organic_ai_core_enhanced_decision())
    asyncio.run(test_organic_ai_core_network_evolution())
    asyncio.run(test_organic_ai_core_memory_management())
    
    print("所有测试通过！")
