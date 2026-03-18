"""
个性化推荐技能 - 为用户交互智能体提供智能推荐能力
基于协同过滤 + 规则引擎，结合用户历史行为和环境数据生成农业行动建议
"""

import math
import random
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class RecommendationSkill:
    """个性化推荐技能"""

    # 作物-操作 推荐规则库
    ACTION_RULES = [
        # (条件描述, 优先级权重, 推荐类型, 模板)
        {
            "id": "R001",
            "name": "低湿度自动灌溉推荐",
            "condition": lambda ctx: ctx.get("soil_moisture", 100) < 30,
            "priority": 0.95,
            "type": "irrigation",
            "title": "建议立即灌溉",
            "description": "土壤湿度偏低（{soil_moisture}%），建议开启灌溉系统，保持30-60%适宜范围。",
            "action": {"type": "irrigation", "duration_min": 15, "flow_rate": 8},
            "tags": ["自动化", "紧急"]
        },
        {
            "id": "R002",
            "name": "高温补水推荐",
            "condition": lambda ctx: ctx.get("temperature", 20) > 35 and ctx.get("soil_moisture", 100) < 50,
            "priority": 0.90,
            "type": "irrigation",
            "title": "高温警报 - 建议补水",
            "description": "当前温度 {temperature}°C 较高，结合土壤湿度 {soil_moisture}%，建议增加灌溉频率。",
            "action": {"type": "irrigation", "duration_min": 20, "flow_rate": 10},
            "tags": ["高温", "水分管理"]
        },
        {
            "id": "R003",
            "name": "施肥周期推荐",
            "condition": lambda ctx: ctx.get("days_since_fertilization", 999) > 21,
            "priority": 0.75,
            "type": "fertilization",
            "title": "施肥周期提醒",
            "description": "距上次施肥已 {days_since_fertilization} 天，建议进行追肥，补充氮磷钾营养。",
            "action": {"type": "fertilization", "fertilizer_type": "复合肥", "amount_kg_per_mu": 10},
            "tags": ["定期维护", "营养管理"]
        },
        {
            "id": "R004",
            "name": "高湿病虫害预警推荐",
            "condition": lambda ctx: ctx.get("humidity", 0) > 85 and ctx.get("temperature", 20) > 25,
            "priority": 0.88,
            "type": "pest_prevention",
            "title": "高温高湿 - 病虫害风险预警",
            "description": "当前温度 {temperature}°C，湿度 {humidity}%，高温高湿环境容易引发病虫害，建议提前防治。",
            "action": {"type": "pest_inspection", "frequency": "每日巡检"},
            "tags": ["预防", "病虫害"]
        },
        {
            "id": "R005",
            "name": "光照不足补光推荐",
            "condition": lambda ctx: ctx.get("light_intensity", 1000) < 500,
            "priority": 0.70,
            "type": "lighting",
            "title": "光照不足 - 建议补光",
            "description": "当前光照强度 {light_intensity} lux，低于作物生长需求，建议开启补光灯。",
            "action": {"type": "supplement_light", "duration_hours": 4},
            "tags": ["光照管理", "设施农业"]
        },
        {
            "id": "R006",
            "name": "收获时机推荐",
            "condition": lambda ctx: ctx.get("growth_progress", 0) >= 0.90,
            "priority": 0.85,
            "type": "harvest",
            "title": "作物接近成熟 - 准备收获",
            "description": "当前作物生长进度 {growth_progress_pct}%，已接近成熟，建议7天内安排收割。",
            "action": {"type": "harvest_plan", "suggested_days": 7},
            "tags": ["收获", "丰产"]
        },
        {
            "id": "R007",
            "name": "pH异常调节推荐",
            "condition": lambda ctx: ctx.get("ph", 6.5) < 5.5 or ctx.get("ph", 6.5) > 7.5,
            "priority": 0.82,
            "type": "soil_adjustment",
            "title": "土壤pH异常 - 建议调节",
            "description": "检测到土壤pH为 {ph}，超出适宜范围（5.5-7.5），建议施用石灰/硫磺进行调节。",
            "action": {"type": "soil_amendment", "material": "石灰" if True else "硫磺"},
            "tags": ["土壤管理", "基础管理"]
        },
        {
            "id": "R008",
            "name": "模型推理效果提升推荐",
            "condition": lambda ctx: ctx.get("model_accuracy", 1.0) < 0.85,
            "priority": 0.65,
            "type": "model_optimization",
            "title": "AI模型精度偏低 - 建议重训练",
            "description": "当前模型准确率 {model_accuracy_pct}%，建议收集更多数据并重新训练。",
            "action": {"type": "model_retrain", "data_collection_days": 7},
            "tags": ["AI优化", "系统管理"]
        }
    ]

    # 用户行为 -> 推荐偏好映射
    BEHAVIOR_PREFERENCE_MAP = {
        "irrigation_control": ["R001", "R002"],
        "fertilization_advice": ["R003"],
        "pest_detection": ["R004"],
        "device_control": ["R005"],
        "harvest_planning": ["R006"],
        "data_query": ["R008"],
        "query_crop_status": ["R001", "R003", "R004", "R006"]
    }

    def __init__(
        self,
        recommendation_engine: str = "rule_based",
        personalization_level: str = "high",
        max_recommendations: int = 5
    ):
        self.engine = recommendation_engine
        self.personalization_level = personalization_level
        self.max_recommendations = max_recommendations
        # 用户历史行为存储 {user_id: [{"intent": ..., "timestamp": ..., "feedback": ...}]}
        self._user_history: Dict[str, List[Dict]] = defaultdict(list)
        # 用户偏好分数 {user_id: {rule_id: score}}
        self._user_preferences: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        logger.info(f"RecommendationSkill 初始化，引擎: {recommendation_engine}")

    # ──────────────────────────────────────────────
    #  核心公开方法
    # ──────────────────────────────────────────────

    def recommend_actions(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        intent_history: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        生成个性化行动推荐

        Args:
            user_id: 用户ID
            context: 当前环境上下文（传感器数据、作物状态等）
            intent_history: 最近的意图历史

        Returns:
            排序后的推荐列表
        """
        context = context or {}
        intent_history = intent_history or []

        # 1. 基于规则筛选触发的推荐
        triggered: List[Dict[str, Any]] = []
        for rule in self.ACTION_RULES:
            try:
                if rule["condition"](context):
                    rec = self._build_recommendation(rule, context)
                    triggered.append(rec)
            except Exception as e:
                logger.debug(f"规则 {rule['id']} 评估出错: {e}")

        # 2. 个性化排序
        if self.personalization_level in ("medium", "high"):
            triggered = self._personalize(triggered, user_id, intent_history)

        # 3. 截断到最大数量
        return triggered[:self.max_recommendations]

    def suggest_products(
        self,
        crop_name: str,
        issue_type: str,
        area_mu: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        推荐农业投入品（农药/肥料/种子）

        Args:
            crop_name: 作物名称
            issue_type: 问题类型（pest/disease/nutrition/seed）
            area_mu: 面积（亩）

        Returns:
            推荐产品列表
        """
        product_db = {
            "pest": [
                {"name": "吡虫啉", "dose_per_mu": "10ml", "interval_days": 7, "safety_period": 14,
                 "target": ["蚜虫", "飞虱", "蓟马"], "organic": False},
                {"name": "阿维菌素", "dose_per_mu": "15ml", "interval_days": 10, "safety_period": 14,
                 "target": ["螨虫", "线虫"], "organic": False},
                {"name": "苦参碱", "dose_per_mu": "20ml", "interval_days": 5, "safety_period": 3,
                 "target": ["蚜虫", "粉虱"], "organic": True}
            ],
            "disease": [
                {"name": "百菌清", "dose_per_mu": "100g", "interval_days": 7, "safety_period": 21,
                 "target": ["炭疽病", "霜霉病"], "organic": False},
                {"name": "波尔多液", "dose_per_mu": "混合液500ml", "interval_days": 14, "safety_period": 0,
                 "target": ["霜霉病", "溃疡病"], "organic": True},
                {"name": "甲基硫菌灵", "dose_per_mu": "50g", "interval_days": 7, "safety_period": 14,
                 "target": ["灰霉病", "白粉病"], "organic": False}
            ],
            "nutrition": [
                {"name": "尿素（N46%）", "dose_per_mu": "10-15kg", "application": "撒施或灌溉施入",
                 "nutrient": "N", "organic": False},
                {"name": "磷酸二铵", "dose_per_mu": "8-12kg", "application": "基肥",
                 "nutrient": "NP", "organic": False},
                {"name": "硫酸钾", "dose_per_mu": "5-8kg", "application": "追肥",
                 "nutrient": "K", "organic": False},
                {"name": "有机腐植酸肥", "dose_per_mu": "50kg", "application": "基肥",
                 "nutrient": "NPK+有机质", "organic": True}
            ],
            "seed": [
                {"name": f"{crop_name}优质品种A", "germination_rate": "95%",
                 "yield_per_mu": "600kg", "resistance": "抗病虫", "organic": False},
                {"name": f"{crop_name}高产品种B", "germination_rate": "92%",
                 "yield_per_mu": "700kg", "resistance": "耐高温", "organic": False}
            ]
        }

        products = product_db.get(issue_type, [])
        # 计算总用量
        for p in products:
            if "dose_per_mu" in p:
                dose_str = p["dose_per_mu"]
                p["total_dose"] = f"总用量（{area_mu}亩）: {dose_str} × {area_mu}"

        return products

    def predict_user_needs(
        self,
        user_id: str,
        lookahead_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        预测用户未来几天的需求

        Args:
            user_id: 用户ID
            lookahead_days: 预测天数

        Returns:
            预测需求列表
        """
        history = self._user_history.get(user_id, [])

        if not history:
            # 新用户 - 返回通用推荐
            return self._get_default_predictions(lookahead_days)

        # 统计历史意图频率
        intent_counts: Dict[str, int] = defaultdict(int)
        for record in history[-30:]:  # 只看最近30条
            intent_counts[record.get("intent", "unknown")] += 1

        predictions = []
        for day_offset in range(1, min(lookahead_days + 1, 4)):
            target_date = (datetime.now() + timedelta(days=day_offset)).strftime("%m-%d")
            # 最高频意图 -> 预测需求
            top_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:2]
            for intent, count in top_intents:
                predictions.append({
                    "predicted_date": target_date,
                    "predicted_need": intent,
                    "confidence": min(count / 30, 0.9),
                    "description": f"基于历史行为，预测您在 {target_date} 可能需要: {intent}",
                    "proactive_data": f"建议提前准备 {intent} 相关数据"
                })

        return predictions[:lookahead_days]

    def record_feedback(
        self,
        user_id: str,
        recommendation_id: str,
        accepted: bool,
        intent: Optional[str] = None
    ) -> None:
        """
        记录用户对推荐的反馈，用于持续优化

        Args:
            user_id: 用户ID
            recommendation_id: 推荐规则ID
            accepted: 是否采纳
            intent: 当时的意图
        """
        # 更新偏好分数
        delta = 0.1 if accepted else -0.05
        self._user_preferences[user_id][recommendation_id] = max(
            0.0, min(1.0,
                     self._user_preferences[user_id].get(recommendation_id, 0.5) + delta)
        )
        # 记录历史
        self._user_history[user_id].append({
            "recommendation_id": recommendation_id,
            "accepted": accepted,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"用户 {user_id} 对推荐 {recommendation_id} 反馈: {'采纳' if accepted else '忽略'}")

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户偏好画像"""
        history = self._user_history.get(user_id, [])
        prefs = self._user_preferences.get(user_id, {})

        if not history:
            return {"user_id": user_id, "status": "new_user", "preferences": {}, "history_count": 0}

        intents = [h.get("intent") for h in history if h.get("intent")]
        intent_dist: Dict[str, int] = defaultdict(int)
        for i in intents:
            intent_dist[i] += 1

        return {
            "user_id": user_id,
            "status": "active",
            "history_count": len(history),
            "top_intents": sorted(intent_dist.items(), key=lambda x: x[1], reverse=True)[:5],
            "preferences": dict(prefs),
            "personalization_score": min(len(history) / 100, 1.0)
        }

    # ──────────────────────────────────────────────
    #  内部辅助方法
    # ──────────────────────────────────────────────

    def _build_recommendation(self, rule: Dict, context: Dict) -> Dict[str, Any]:
        """根据规则和上下文构建推荐条目"""
        desc = rule["description"]
        # 插值上下文变量
        fmt_vars = {
            "soil_moisture": round(context.get("soil_moisture", 0), 1),
            "temperature": round(context.get("temperature", 0), 1),
            "humidity": round(context.get("humidity", 0), 1),
            "light_intensity": round(context.get("light_intensity", 0), 0),
            "ph": round(context.get("ph", 6.5), 2),
            "days_since_fertilization": int(context.get("days_since_fertilization", 0)),
            "growth_progress": round(context.get("growth_progress", 0), 2),
            "growth_progress_pct": round(context.get("growth_progress", 0) * 100, 1),
            "model_accuracy": round(context.get("model_accuracy", 1.0), 2),
            "model_accuracy_pct": round(context.get("model_accuracy", 1.0) * 100, 1),
        }
        try:
            desc = desc.format(**fmt_vars)
        except KeyError:
            pass

        return {
            "id": rule["id"],
            "name": rule["name"],
            "title": rule["title"],
            "description": desc,
            "type": rule["type"],
            "priority": rule["priority"],
            "action": rule["action"],
            "tags": rule["tags"],
            "timestamp": datetime.now().isoformat()
        }

    def _personalize(
        self,
        recommendations: List[Dict],
        user_id: str,
        intent_history: List[str]
    ) -> List[Dict]:
        """根据用户偏好和意图历史调整推荐排序"""
        prefs = self._user_preferences.get(user_id, {})

        # 意图 -> 规则ID 偏好加分
        intent_boost: Dict[str, float] = defaultdict(float)
        for intent in intent_history[-5:]:
            for rule_id in self.BEHAVIOR_PREFERENCE_MAP.get(intent, []):
                intent_boost[rule_id] += 0.05

        for rec in recommendations:
            rid = rec["id"]
            user_pref_score = prefs.get(rid, 0.5)
            intent_score = intent_boost.get(rid, 0.0)
            rec["personalized_priority"] = min(
                rec["priority"] * user_pref_score * 2 + intent_score, 1.0
            )

        return sorted(recommendations, key=lambda r: r.get("personalized_priority", r["priority"]), reverse=True)

    def _get_default_predictions(self, days: int) -> List[Dict[str, Any]]:
        """新用户默认预测"""
        defaults = [
            {"predicted_need": "query_weather", "description": "建议每日查看天气预报，及时调整农事安排"},
            {"predicted_need": "irrigation_control", "description": "定期检查土壤湿度，按需灌溉"},
            {"predicted_need": "pest_detection", "description": "每周巡检作物，早发现早防治"},
        ]
        results = []
        for i in range(min(days, len(defaults))):
            target_date = (datetime.now() + timedelta(days=i + 1)).strftime("%m-%d")
            d = defaults[i].copy()
            d["predicted_date"] = target_date
            d["confidence"] = 0.6
            results.append(d)
        return results
