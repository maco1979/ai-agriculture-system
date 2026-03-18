#!/usr/bin/env python3
"""
测试增强版微调功能
"""
import pytest
import asyncio
from src.core.ai_organic_core import OrganicAICore


class TestFineTune:
    """测试增强版微调功能"""
    
    def setup_method(self):
        """设置测试环境"""
        self.ai_core = OrganicAICore()
    
    @pytest.mark.asyncio
    async def test_fine_tune_basic_parameters(self):
        """测试基本参数微调"""
        # 准备测试参数
        fine_tune_params = {
            "exploration_rate": 0.2,
            "utilization_weight": 0.6,
            "iteration_interval": 120
        }
        
        # 执行微调
        result = await self.ai_core.fine_tune(fine_tune_params)
        
        # 验证结果
        assert result["success"] == True
        assert "updated_params" in result
        assert result["updated_params"]["exploration_rate"] == 0.2
        assert result["updated_params"]["utilization_weight"] == 0.6
        assert result["updated_params"]["iteration_interval"] == 120
        
    @pytest.mark.asyncio
    async def test_fine_tune_with_invalid_parameters(self):
        """测试无效参数微调"""
        # 准备无效测试参数
        invalid_params_list = [
            {"exploration_rate": 1.5},  # 探索率超出范围
            {"iteration_interval": 1000},  # 迭代间隔超出范围
            {"multimodal_weights": {"vision": 0.7, "text": 0.5}}  # 权重总和不等于1
        ]
        
        for invalid_params in invalid_params_list:
            result = await self.ai_core.fine_tune(invalid_params)
            assert result["success"] == False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_fine_tune_with_network_evolution(self):
        """测试带网络演化的微调"""
        # 准备测试参数，包含网络演化
        fine_tune_params = {
            "exploration_rate": 0.15,
            "perform_evolution": True,
            "evolution_strategy": "adaptive"
        }
        
        # 执行微调
        result = await self.ai_core.fine_tune(fine_tune_params)
        
        # 验证结果
        assert result["success"] == True
        assert "evolution_result" in result
        assert result["evolution_result"] is not None
        assert "new_hidden_dims" in result["evolution_result"]
    
    @pytest.mark.asyncio
    async def test_fine_tune_with_multimodal_weights(self):
        """测试多模态权重微调"""
        # 准备测试参数
        fine_tune_params = {
            "multimodal_weights": {
                "vision": 0.3,
                "speech": 0.2,
                "text": 0.3,
                "sensor": 0.2
            }
        }
        
        # 执行微调
        result = await self.ai_core.fine_tune(fine_tune_params)
        
        # 验证结果
        assert result["success"] == True
        assert "updated_params" in result
        assert "multimodal_weights" in result["updated_params"]
        updated_weights = result["updated_params"]["multimodal_weights"]
        assert abs(sum(updated_weights.values()) - 1.0) < 0.01
        assert updated_weights["vision"] == 0.3
        assert updated_weights["speech"] == 0.2
        assert updated_weights["text"] == 0.3
        assert updated_weights["sensor"] == 0.2
    
    @pytest.mark.asyncio
    async def test_fine_tune_with_memory_settings(self):
        """测试记忆相关参数微调"""
        # 准备测试参数
        fine_tune_params = {
            "memory_retrieval_threshold": 0.8,
            "max_long_term_memory_size": 5000
        }
        
        # 执行微调
        result = await self.ai_core.fine_tune(fine_tune_params)
        
        # 验证结果
        assert result["success"] == True
        assert "updated_params" in result
        assert "memory_retrieval_threshold" in result["updated_params"]
        assert result["updated_params"]["memory_retrieval_threshold"] == 0.8
        assert self.ai_core.max_long_term_memory_size == 5000
    
    @pytest.mark.asyncio
    async def test_fine_tune_with_hardware_learning(self):
        """测试硬件学习相关参数微调"""
        # 准备测试参数
        fine_tune_params = {
            "hardware_learning_enabled": True,
            "multimodal_fusion_enabled": False
        }
        
        # 执行微调
        result = await self.ai_core.fine_tune(fine_tune_params)
        
        # 验证结果
        assert result["success"] == True
        assert "updated_params" in result
        assert "hardware_learning_enabled" in result["updated_params"]
        assert result["updated_params"]["hardware_learning_enabled"] == True
        assert self.ai_core.hardware_learning_enabled == True
        assert self.ai_core.multimodal_fusion_enabled == False
    
    @pytest.mark.asyncio
    async def test_fine_tune_exploration_settings(self):
        """测试探索相关参数微调"""
        # 准备测试参数
        fine_tune_params = {
            "exploration_min": 0.02,
            "exploration_decay": 0.998,
            "exploration_rate": 0.3
        }
        
        # 执行微调
        result = await self.ai_core.fine_tune(fine_tune_params)
        
        # 验证结果
        assert result["success"] == True
        assert "updated_params" in result
        assert "exploration_min" in result["updated_params"]
        assert "exploration_decay" in result["updated_params"]
        assert result["updated_params"]["exploration_min"] == 0.02
        assert result["updated_params"]["exploration_decay"] == 0.998
        assert result["updated_params"]["exploration_rate"] == 0.3
    
    def test_validate_fine_tune_params(self):
        """测试参数验证方法"""
        # 测试有效参数
        valid_params = {
            "exploration_rate": 0.1,
            "utilization_weight": 0.5,
            "iteration_interval": 60,
            "multimodal_weights": {
                "vision": 0.4,
                "speech": 0.2,
                "text": 0.3,
                "sensor": 0.1
            },
            "memory_retrieval_threshold": 0.7,
            "evolution_strategy": "adaptive"
        }
        
        is_valid, error_msg = self.ai_core._validate_fine_tune_params(valid_params)
        assert is_valid == True
        assert error_msg == ""
        
        # 测试无效参数
        invalid_params = {
            "exploration_rate": -0.1,  # 探索率为负数
            "iteration_interval": 500,  # 迭代间隔超出范围
            "multimodal_weights": {"vision": 0.8, "text": 0.3},  # 权重总和不等于1
            "evolution_strategy": "invalid_strategy"  # 无效演化策略
        }
        
        is_valid, error_msg = self.ai_core._validate_fine_tune_params(invalid_params)
        assert is_valid == False
        assert error_msg != ""
    
    @pytest.mark.asyncio
    async def test_fine_tune_empty_parameters(self):
        """测试空参数微调"""
        # 准备空测试参数
        fine_tune_params = {}
        
        # 执行微调
        result = await self.ai_core.fine_tune(fine_tune_params)
        
        # 验证结果
        assert result["success"] == True
        assert "updated_params" in result
        assert len(result["updated_params"]) == 0
