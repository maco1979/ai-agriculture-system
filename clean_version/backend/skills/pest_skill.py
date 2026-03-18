"""
病虫害识别技能 - 为决策引擎智能体提供病虫害识别和防治建议
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

class PestSkill:
    """病虫害识别技能"""
    
    # 病虫害数据库
    PEST_DATABASE = {
        "水稻": {
            "稻飞虱": {
                "symptoms": ["叶片变黄", "植株矮小", "蜜露分泌物", "煤污病"],
                "damage_season": ["夏季", "秋季"],
                "temperature_range": (25, 35),
                "humidity_range": (70, 90),
                "prevention": ["选用抗虫品种", "合理密植", "科学施肥"],
                "treatment": ["吡虫啉", "噻虫嗪", "烯啶虫胺"],
                "biological_control": ["蜘蛛", "瓢虫", "寄生蜂"],
                "threshold": "每丛10头以上需防治"
            },
            "稻纵卷叶螟": {
                "symptoms": ["叶片卷曲", "白色条斑", "叶片枯白"],
                "damage_season": ["夏季"],
                "temperature_range": (22, 30),
                "humidity_range": (80, 95),
                "prevention": ["清除杂草", "冬季翻耕", "灯光诱杀"],
                "treatment": ["氯虫苯甲酰胺", "甲维盐", "茚虫威"],
                "biological_control": ["赤眼蜂", "绒茧蜂"],
                "threshold": "百丛幼虫50头以上"
            },
            "纹枯病": {
                "symptoms": ["叶鞘病斑", "云纹状病斑", "植株倒伏"],
                "damage_season": ["雨季", "高温高湿"],
                "temperature_range": (25, 32),
                "humidity_range": (85, 100),
                "prevention": ["合理密植", "科学灌溉", "平衡施肥"],
                "treatment": ["井冈霉素", "己唑醇", "苯醚甲环唑"],
                "biological_control": ["拮抗菌"],
                "threshold": "病丛率15%以上"
            }
        },
        "小麦": {
            "蚜虫": {
                "symptoms": ["叶片卷曲", "蜜露分泌物", "煤污病", "植株矮小"],
                "damage_season": ["春季", "秋季"],
                "temperature_range": (15, 25),
                "humidity_range": (50, 80),
                "prevention": ["适时播种", "清除杂草", "黄板诱杀"],
                "treatment": ["吡虫啉", "啶虫脒", "氟啶虫胺腈"],
                "biological_control": ["瓢虫", "草蛉", "食蚜蝇"],
                "threshold": "百株蚜量500头以上"
            },
            "白粉病": {
                "symptoms": ["白色粉状物", "叶片变黄", "植株早衰"],
                "damage_season": ["春季", "湿度大时"],
                "temperature_range": (15, 22),
                "humidity_range": (70, 90),
                "prevention": ["选用抗病品种", "合理密植", "通风透光"],
                "treatment": ["三唑酮", "戊唑醇", "嘧菌酯"],
                "biological_control": ["芽孢杆菌"],
                "threshold": "病叶率10%以上"
            },
            "赤霉病": {
                "symptoms": ["穗部粉红色霉层", "籽粒秕瘦", "穗腐"],
                "damage_season": ["扬花期", "多雨季节"],
                "temperature_range": (20, 28),
                "humidity_range": (85, 100),
                "prevention": ["选用抗病品种", "适时播种", "开沟排水"],
                "treatment": ["多菌灵", "戊唑醇", "氰烯菌酯"],
                "biological_control": ["木霉菌"],
                "threshold": "花期遇雨需预防"
            }
        },
        "玉米": {
            "玉米螟": {
                "symptoms": ["茎秆蛀孔", "雄穗折断", "籽粒受损"],
                "damage_season": ["夏季"],
                "temperature_range": (20, 30),
                "humidity_range": (60, 80),
                "prevention": ["处理秸秆", "轮作倒茬", "性诱剂诱杀"],
                "treatment": ["氯虫苯甲酰胺", "甲维盐", "高效氯氟氰菊酯"],
                "biological_control": ["赤眼蜂", "白僵菌"],
                "threshold": "百株卵块3块以上"
            },
            "大斑病": {
                "symptoms": ["大型梭形病斑", "叶片枯死", "减产严重"],
                "damage_season": ["雨季", "高温高湿"],
                "temperature_range": (20, 28),
                "humidity_range": (85, 100),
                "prevention": ["选用抗病品种", "合理密植", "轮作"],
                "treatment": ["苯醚甲环唑", "嘧菌酯", "吡唑醚菌酯"],
                "biological_control": ["拮抗菌"],
                "threshold": "病叶率10%以上"
            }
        }
    }
    
    def __init__(self):
        self.pest_data = self.PEST_DATABASE
    
    def identify_pest(self, crop_name: str, symptoms: List[str], 
                     image_data: Optional[str] = None) -> Dict[str, Any]:
        """
        识别病虫害
        
        Args:
            crop_name: 作物名称
            symptoms: 症状描述列表
            image_data: 图像数据（base64，可选）
        
        Returns:
            识别结果
        """
        crop_pests = self.pest_data.get(crop_name, {})
        if not crop_pests:
            return {
                "error": f"未找到作物 '{crop_name}' 的病虫害数据",
                "available_crops": list(self.pest_data.keys())
            }
        
        # 基于症状匹配
        matched_pests = []
        for pest_name, pest_info in crop_pests.items():
            pest_symptoms = pest_info.get("symptoms", [])
            
            # 计算匹配度
            matched_symptoms = [s for s in symptoms if any(symptom in s for symptom in pest_symptoms)]
            match_score = len(matched_symptoms) / len(pest_symptoms) if pest_symptoms else 0
            
            if match_score > 0.3:  # 30%匹配度阈值
                matched_pests.append({
                    "pest_name": pest_name,
                    "match_score": match_score,
                    "matched_symptoms": matched_symptoms,
                    "info": pest_info
                })
        
        # 按匹配度排序
        matched_pests.sort(key=lambda x: x["match_score"], reverse=True)
        
        # 如果有图像数据，可以进一步分析（这里简化处理）
        image_analysis = None
        if image_data:
            image_analysis = self._analyze_image(image_data)
        
        return {
            "crop": crop_name,
            "symptoms": symptoms,
            "matched_pests": matched_pests[:3],  # 返回前3个匹配结果
            "image_analysis": image_analysis,
            "confidence": "高" if matched_pests and matched_pests[0]["match_score"] > 0.7 else "中"
        }
    
    def get_prevention_plan(self, crop_name: str, pest_name: str, 
                           season: str, area_hectares: float) -> Dict[str, Any]:
        """
        获取防治方案
        
        Args:
            crop_name: 作物名称
            pest_name: 病虫害名称
            season: 季节
            area_hectares: 面积（公顷）
        
        Returns:
            防治方案
        """
        pest_info = self.pest_data.get(crop_name, {}).get(pest_name)
        if not pest_info:
            return {
                "error": f"未找到病虫害 '{pest_name}' 的信息",
                "crop": crop_name
            }
        
        # 检查是否在危害季节
        damage_seasons = pest_info.get("damage_season", [])
        season_risk = "高" if season in damage_seasons else "中"
        
        # 计算用药量（示例计算）
        treatment_chemicals = pest_info.get("treatment", [])
        chemical_plan = []
        for chemical in treatment_chemicals[:2]:  # 取前两种药剂
            dosage = self._calculate_dosage(chemical, area_hectares)
            chemical_plan.append({
                "chemical": chemical,
                "dosage_kg_per_ha": dosage,
                "total_kg": dosage * area_hectares,
                "application_method": "喷雾",
                "safety_interval_days": 7  # 安全间隔期
            })
        
        # 综合防治方案
        integrated_plan = {
            "preventive_measures": pest_info.get("prevention", []),
            "chemical_control": chemical_plan,
            "biological_control": pest_info.get("biological_control", []),
            "cultural_practices": [
                "及时清除病残体",
                "合理轮作",
                "加强田间管理"
            ]
        }
        
        return {
            "crop": crop_name,
            "pest": pest_name,
            "season": season,
            "season_risk": season_risk,
            "area_hectares": area_hectares,
            "integrated_plan": integrated_plan,
            "threshold": pest_info.get("threshold", ""),
            "monitoring_frequency": "每周检查一次" if season_risk == "高" else "每两周检查一次"
        }
    
    def predict_pest_risk(self, crop_name: str, weather_data: Dict, 
                         growth_stage: str) -> Dict[str, Any]:
        """
        预测病虫害风险
        
        Args:
            crop_name: 作物名称
            weather_data: 天气数据
            growth_stage: 生长阶段
        
        Returns:
            风险预测
        """
        crop_pests = self.pest_data.get(crop_name, {})
        if not crop_pests:
            return {
                "error": f"未找到作物 '{crop_name}' 的病虫害数据"
            }
        
        temperature = weather_data.get("temperature", 25)
        humidity = weather_data.get("humidity", 70)
        precipitation = weather_data.get("precipitation", 0)
        
        risk_pests = []
        for pest_name, pest_info in crop_pests.items():
            temp_range = pest_info.get("temperature_range", (15, 35))
            humidity_range = pest_info.get("humidity_range", (60, 90))
            
            # 计算环境适宜度
            temp_suitability = self._calculate_suitability(temperature, temp_range)
            humidity_suitability = self._calculate_suitability(humidity, humidity_range)
            
            # 考虑降雨影响
            rain_factor = 1.2 if precipitation > 10 else 1.0
            
            overall_risk = (temp_suitability + humidity_suitability) / 2 * rain_factor
            
            if overall_risk > 0.6:  # 风险阈值
                risk_level = "高" if overall_risk > 0.8 else "中"
                risk_pests.append({
                    "pest_name": pest_name,
                    "risk_level": risk_level,
                    "risk_score": overall_risk,
                    "suitable_conditions": {
                        "temperature": f"{temperature}°C (适宜范围: {temp_range[0]}-{temp_range[1]}°C)",
                        "humidity": f"{humidity}% (适宜范围: {humidity_range[0]}-{humidity_range[1]}%)"
                    },
                    "preventive_actions": pest_info.get("prevention", [])[:3]
                })
        
        # 按风险排序
        risk_pests.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return {
            "crop": crop_name,
            "growth_stage": growth_stage,
            "weather_conditions": {
                "temperature": temperature,
                "humidity": humidity,
                "precipitation": precipitation
            },
            "high_risk_pests": [p for p in risk_pests if p["risk_level"] == "高"],
            "medium_risk_pests": [p for p in risk_pests if p["risk_level"] == "中"],
            "recommendations": self._get_risk_recommendations(risk_pests)
        }
    
    def _analyze_image(self, image_data: str) -> Dict[str, Any]:
        """
        分析图像数据（简化版）
        
        实际应用中应该使用深度学习模型进行图像识别
        这里返回模拟结果
        """
        # 这里应该是实际的图像分析代码
        # 例如使用OpenCV或深度学习模型
        
        return {
            "analysis_type": "症状识别",
            "detected_features": ["病斑", "变色", "畸形"],
            "confidence": 0.75,
            "note": "建议结合症状描述进行确认"
        }
    
    def _calculate_dosage(self, chemical: str, area_hectares: float) -> float:
        """计算用药量（公斤/公顷）"""
        # 简化计算，实际应根据药剂说明
        base_dosages = {
            "吡虫啉": 0.15,
            "噻虫嗪": 0.1,
            "氯虫苯甲酰胺": 0.05,
            "甲维盐": 0.02,
            "三唑酮": 0.2,
            "多菌灵": 0.3,
            "井冈霉素": 0.5
        }
        
        return base_dosages.get(chemical, 0.1)
    
    def _calculate_suitability(self, value: float, optimal_range: tuple) -> float:
        """计算环境适宜度（0-1）"""
        min_val, max_val = optimal_range
        if min_val <= value <= max_val:
            # 在适宜范围内，计算接近最佳值的程度
            optimal = (min_val + max_val) / 2
            deviation = abs(value - optimal) / (max_val - min_val) * 2
            return max(0, 1 - deviation)
        else:
            # 在范围外，计算偏离程度
            if value < min_val:
                deviation = (min_val - value) / min_val
            else:
                deviation = (value - max_val) / max_val
            return max(0, 1 - deviation * 2)
    
    def _get_risk_recommendations(self, risk_pests: List[Dict]) -> List[str]:
        """获取风险应对建议"""
        recommendations = []
        
        if any(p["risk_level"] == "高" for p in risk_pests):
            recommendations.extend([
                "立即加强田间检查",
                "准备防治药剂",
                "考虑预防性施药"
            ])
        
        if any(p["risk_level"] == "中" for p in risk_pests):
            recommendations.extend([
                "增加监测频率",
                "清理田间环境",
                "做好防治准备"
            ])
        
        if not risk_pests:
            recommendations.append("当前病虫害风险较低，保持常规监测")
        
        return recommendations


# 使用示例
if __name__ == "__main__":
    pest_skill = PestSkill()
    
    # 识别病虫害
    symptoms = ["叶片变黄", "植株矮小", "蜜露分泌物"]
    identification = pest_skill.identify_pest("水稻", symptoms)
    print("病虫害识别:", json.dumps(identification, indent=2, ensure_ascii=False))
    
    # 获取防治方案
    prevention_plan = pest_skill.get_prevention_plan("水稻", "稻飞虱", "夏季", 5)
    print("\n防治方案:", json.dumps(prevention_plan, indent=2, ensure_ascii=False))
    
    # 预测病虫害风险
    weather_data = {"temperature": 28, "humidity": 85, "precipitation": 5}
    risk_prediction = pest_skill.predict_pest_risk("水稻", weather_data, "分蘖期")
    print("\n风险预测:", json.dumps(risk_prediction, indent=2, ensure_ascii=False))