"""
智能体技能包 - 为AI农业决策系统提供各种技能
版本: 2.0.0 — 新增 NLPSkill 和 RecommendationSkill
"""

from .weather_skill import WeatherSkill
from .crop_skill import CropSkill
from .pest_skill import PestSkill
from .blockchain_skill import BlockchainSkill
from .device_skill import DeviceSkill
from .nlp_skill import NLPSkill
from .recommendation_skill import RecommendationSkill

__all__ = [
    'WeatherSkill',
    'CropSkill',
    'PestSkill',
    'BlockchainSkill',
    'DeviceSkill',
    'NLPSkill',
    'RecommendationSkill',
]

__version__ = '2.0.0'

# 技能注册表（名称 -> 类映射）
SKILL_REGISTRY = {
    'weather_skill':        WeatherSkill,
    'crop_skill':           CropSkill,
    'pest_skill':           PestSkill,
    'blockchain_skill':     BlockchainSkill,
    'device_skill':         DeviceSkill,
    'nlp_skill':            NLPSkill,
    'recommendation_skill': RecommendationSkill,
}


def get_skill(skill_name: str, **kwargs):
    """
    按名称创建技能实例
    
    Args:
        skill_name: 技能名称（见 SKILL_REGISTRY）
        **kwargs: 传递给技能构造函数的参数
    
    Returns:
        技能实例
    
    Raises:
        KeyError: 技能名称不存在
    """
    if skill_name not in SKILL_REGISTRY:
        raise KeyError(f"未知技能: '{skill_name}'。可用技能: {list(SKILL_REGISTRY.keys())}")
    return SKILL_REGISTRY[skill_name](**kwargs)