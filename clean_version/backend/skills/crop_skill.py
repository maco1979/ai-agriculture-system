"""
作物管理技能 - 为决策引擎智能体提供作物管理知识
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CropSkill:
    """作物管理技能"""
    
    # 作物数据库
    CROP_DATABASE = {
        "水稻": {
            "growth_stages": ["发芽期", "幼苗期", "分蘖期", "拔节期", "抽穗期", "成熟期"],
            "temperature_range": (20, 35),
            "optimal_temperature": 28,
            "water_requirement": "高",
            "soil_type": "黏土或壤土",
            "ph_range": (5.5, 7.0),
            "growth_days": 90,
            "fertilizer_needs": {
                "N": "中等",
                "P": "中等", 
                "K": "高"
            },
            "common_pests": ["稻飞虱", "稻纵卷叶螟", "二化螟"],
            "harvest_indicator": "谷粒变黄，含水量20-25%"
        },
        "小麦": {
            "growth_stages": ["出苗期", "分蘖期", "拔节期", "抽穗期", "开花期", "灌浆期", "成熟期"],
            "temperature_range": (10, 25),
            "optimal_temperature": 18,
            "water_requirement": "中等",
            "soil_type": "壤土或砂壤土",
            "ph_range": (6.0, 7.5),
            "growth_days": 120,
            "fertilizer_needs": {
                "N": "高",
                "P": "中等",
                "K": "中等"
            },
            "common_pests": ["蚜虫", "麦蜘蛛", "吸浆虫"],
            "harvest_indicator": "麦粒变硬，含水量13-15%"
        },
        "玉米": {
            "growth_stages": ["出苗期", "拔节期", "大喇叭口期", "抽雄期", "吐丝期", "成熟期"],
            "temperature_range": (18, 32),
            "optimal_temperature": 25,
            "water_requirement": "中等",
            "soil_type": "排水良好的壤土",
            "ph_range": (5.8, 7.0),
            "growth_days": 100,
            "fertilizer_needs": {
                "N": "高",
                "P": "中等",
                "K": "高"
            },
            "common_pests": ["玉米螟", "蚜虫", "草地贪夜蛾"],
            "harvest_indicator": "苞叶变黄，籽粒变硬"
        },
        "大豆": {
            "growth_stages": ["出苗期", "分枝期", "开花期", "结荚期", "鼓粒期", "成熟期"],
            "temperature_range": (20, 30),
            "optimal_temperature": 25,
            "water_requirement": "中等",
            "soil_type": "排水良好的壤土",
            "ph_range": (6.0, 7.0),
            "growth_days": 90,
            "fertilizer_needs": {
                "N": "低（固氮）",
                "P": "中等",
                "K": "中等"
            },
            "common_pests": ["豆荚螟", "蚜虫", "红蜘蛛"],
            "harvest_indicator": "叶片变黄脱落，豆荚变褐"
        },
        "棉花": {
            "growth_stages": ["出苗期", "现蕾期", "开花期", "吐絮期", "成熟期"],
            "temperature_range": (20, 35),
            "optimal_temperature": 28,
            "water_requirement": "中等偏高",
            "soil_type": "砂壤土或壤土",
            "ph_range": (5.5, 8.0),
            "growth_days": 150,
            "fertilizer_needs": {
                "N": "高",
                "P": "中等",
                "K": "高"
            },
            "common_pests": ["棉铃虫", "蚜虫", "红蜘蛛"],
            "harvest_indicator": "棉铃开裂，棉絮露出"
        }
    }
    
    def __init__(self):
        self.crop_data = self.CROP_DATABASE
    
    def get_crop_info(self, crop_name: str) -> Dict[str, Any]:
        """
        获取作物基本信息
        
        Args:
            crop_name: 作物名称
        
        Returns:
            作物信息
        """
        crop_info = self.crop_data.get(crop_name)
        if not crop_info:
            return {
                "error": f"未找到作物 '{crop_name}' 的信息",
                "available_crops": list(self.crop_data.keys())
            }
        
        return crop_info
    
    def calculate_growth_stage(self, crop_name: str, planting_date: str, 
                             current_date: Optional[str] = None) -> Dict[str, Any]:
        """
        计算作物生长阶段
        
        Args:
            crop_name: 作物名称
            planting_date: 种植日期 (YYYY-MM-DD)
            current_date: 当前日期 (YYYY-MM-DD)，默认为今天
        
        Returns:
            生长阶段信息
        """
        try:
            crop_info = self.get_crop_info(crop_name)
            if "error" in crop_info:
                return crop_info
            
            # 解析日期
            plant_date = datetime.strptime(planting_date, "%Y-%m-%d")
            if current_date:
                curr_date = datetime.strptime(current_date, "%Y-%m-%d")
            else:
                curr_date = datetime.now()
            
            # 计算生长天数
            growth_days = (curr_date - plant_date).days
            
            if growth_days < 0:
                return {
                    "error": "当前日期早于种植日期",
                    "planting_date": planting_date,
                    "current_date": curr_date.strftime("%Y-%m-%d")
                }
            
            # 计算生长阶段
            total_days = crop_info["growth_days"]
            stage_days = total_days / len(crop_info["growth_stages"])
            
            current_stage_index = min(int(growth_days // stage_days), len(crop_info["growth_stages"]) - 1)
            current_stage = crop_info["growth_stages"][current_stage_index]
            
            # 计算阶段进度
            stage_progress = (growth_days % stage_days) / stage_days * 100
            
            # 下一阶段信息
            next_stage = None
            days_to_next = None
            if current_stage_index < len(crop_info["growth_stages"]) - 1:
                next_stage = crop_info["growth_stages"][current_stage_index + 1]
                days_in_current_stage = stage_days - (growth_days % stage_days)
                days_to_next = max(0, int(days_in_current_stage))
            
            return {
                "crop": crop_name,
                "planting_date": planting_date,
                "current_date": curr_date.strftime("%Y-%m-%d"),
                "growth_days": growth_days,
                "total_growth_days": total_days,
                "growth_progress": min(100, growth_days / total_days * 100),
                "current_stage": current_stage,
                "stage_index": current_stage_index,
                "stage_progress": stage_progress,
                "next_stage": next_stage,
                "days_to_next_stage": days_to_next,
                "estimated_harvest_date": (plant_date + timedelta(days=total_days)).strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            logger.error(f"计算生长阶段失败: {e}")
            return {
                "error": f"计算生长阶段失败: {str(e)}",
                "crop": crop_name,
                "planting_date": planting_date
            }
    
    def get_management_recommendations(self, crop_name: str, growth_stage: str, 
                                     weather_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        获取管理建议
        
        Args:
            crop_name: 作物名称
            growth_stage: 生长阶段
            weather_data: 天气数据（可选）
        
        Returns:
            管理建议
        """
        crop_info = self.get_crop_info(crop_name)
        if "error" in crop_info:
            return crop_info
        
        recommendations = {
            "irrigation": self._get_irrigation_recommendation(crop_name, growth_stage, weather_data),
            "fertilization": self._get_fertilization_recommendation(crop_name, growth_stage),
            "pest_control": self._get_pest_control_recommendation(crop_name, growth_stage),
            "field_management": self._get_field_management_recommendation(crop_name, growth_stage)
        }
        
        return {
            "crop": crop_name,
            "growth_stage": growth_stage,
            "recommendations": recommendations
        }
    
    def predict_yield(self, crop_name: str, area_hectares: float, 
                     management_score: float = 0.8) -> Dict[str, Any]:
        """
        预测产量
        
        Args:
            crop_name: 作物名称
            area_hectares: 面积（公顷）
            management_score: 管理水平评分（0-1）
        
        Returns:
            产量预测
        """
        # 基准产量（公斤/公顷）
        base_yields = {
            "水稻": 7500,
            "小麦": 6000,
            "玉米": 8000,
            "大豆": 2500,
            "棉花": 1500  # 籽棉
        }
        
        base_yield = base_yields.get(crop_name, 5000)
        
        # 考虑管理水平
        adjusted_yield = base_yield * management_score
        
        # 计算总产量
        total_yield = adjusted_yield * area_hectares
        
        return {
            "crop": crop_name,
            "area_hectares": area_hectares,
            "base_yield_kg_per_ha": base_yield,
            "management_score": management_score,
            "predicted_yield_kg_per_ha": adjusted_yield,
            "total_predicted_yield_kg": total_yield,
            "confidence": "中等" if 0.6 <= management_score <= 0.9 else "低"
        }
    
    def _get_irrigation_recommendation(self, crop_name: str, growth_stage: str, 
                                     weather_data: Optional[Dict]) -> str:
        """获取灌溉建议"""
        crop_info = self.crop_data.get(crop_name, {})
        water_req = crop_info.get("water_requirement", "中等")
        
        stage_water_needs = {
            "发芽期": "保持土壤湿润",
            "幼苗期": "适量灌溉",
            "分蘖期": "充足水分",
            "拔节期": "关键需水期",
            "开花期": "避免干旱",
            "灌浆期": "适量水分",
            "成熟期": "减少灌溉"
        }
        
        base_recommendation = stage_water_needs.get(growth_stage, "根据土壤湿度灌溉")
        
        if weather_data:
            precip = weather_data.get("precipitation", 0)
            if precip > 20:
                return f"{base_recommendation}（近期有降雨，可减少灌溉）"
            elif precip < 5:
                return f"{base_recommendation}（近期少雨，需加强灌溉）"
        
        return base_recommendation
    
    def _get_fertilization_recommendation(self, crop_name: str, growth_stage: str) -> str:
        """获取施肥建议"""
        crop_info = self.crop_data.get(crop_name, {})
        fertilizer_needs = crop_info.get("fertilizer_needs", {})
        
        stage_fertilizer = {
            "幼苗期": "施足基肥，适量追肥",
            "分蘖期": "追施氮肥促进分蘖",
            "拔节期": "平衡施肥，增施磷钾",
            "开花期": "适量追肥，保花保果",
            "灌浆期": "叶面喷施，提高品质"
        }
        
        base_recommendation = stage_fertilizer.get(growth_stage, "根据土壤测试施肥")
        
        # 添加具体肥料建议
        if fertilizer_needs.get("N") == "高":
            base_recommendation += "，注意氮肥施用"
        
        return base_recommendation
    
    def _get_pest_control_recommendation(self, crop_name: str, growth_stage: str) -> str:
        """获取病虫害防治建议"""
        crop_info = self.crop_data.get(crop_name, {})
        common_pests = crop_info.get("common_pests", [])
        
        stage_pest_risk = {
            "幼苗期": "注意地下害虫",
            "分蘖期": "预防叶部病害",
            "开花期": "防治传病害虫",
            "成熟期": "注意收获前病虫害"
        }
        
        base_recommendation = stage_pest_risk.get(growth_stage, "定期检查，预防为主")
        
        if common_pests:
            pests_str = "、".join(common_pests[:3])
            base_recommendation += f"，重点关注：{pests_str}"
        
        return base_recommendation
    
    def _get_field_management_recommendation(self, crop_name: str, growth_stage: str) -> str:
        """获取田间管理建议"""
        stage_management = {
            "发芽期": "保持土壤疏松，及时补苗",
            "幼苗期": "中耕除草，促进根系生长",
            "分蘖期": "合理密植，控制无效分蘖",
            "拔节期": "培土防倒，清理田间杂草",
            "开花期": "人工辅助授粉（如需）",
            "成熟期": "适时收获，防止落粒"
        }
        
        return stage_management.get(growth_stage, "加强田间巡查，及时处理问题")


# 使用示例
if __name__ == "__main__":
    crop_skill = CropSkill()
    
    # 获取作物信息
    rice_info = crop_skill.get_crop_info("水稻")
    print("水稻信息:", json.dumps(rice_info, indent=2, ensure_ascii=False))
    
    # 计算生长阶段
    growth_info = crop_skill.calculate_growth_stage("水稻", "2024-03-01", "2024-05-15")
    print("\n生长阶段:", json.dumps(growth_info, indent=2, ensure_ascii=False))
    
    # 获取管理建议
    recommendations = crop_skill.get_management_recommendations("水稻", "分蘖期")
    print("\n管理建议:", json.dumps(recommendations, indent=2, ensure_ascii=False))
    
    # 预测产量
    yield_prediction = crop_skill.predict_yield("水稻", 10, 0.85)
    print("\n产量预测:", json.dumps(yield_prediction, indent=2, ensure_ascii=False))