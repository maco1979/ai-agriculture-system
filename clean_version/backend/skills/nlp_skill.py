"""
自然语言处理技能 - 为用户交互智能体提供NLP能力
支持中文农业场景的意图识别、实体提取、情感分析和回复生成
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class NLPSkill:
    """自然语言处理技能"""

    # 意图识别规则库（关键词匹配 + 正则）
    INTENT_PATTERNS = {
        "query_weather": {
            "keywords": ["天气", "气温", "温度", "降雨", "湿度", "风速", "晴", "雨", "雪"],
            "patterns": [r"(明天|今天|后天).*(天气|温度)", r".*会不会下雨"],
            "description": "查询天气信息"
        },
        "query_crop_status": {
            "keywords": ["作物", "庄稼", "生长", "长势", "叶片", "根系", "发育", "苗情"],
            "patterns": [r"(水稻|小麦|玉米|大豆).*(怎么样|如何|状态)", r".*什么时候.*(成熟|收获)"],
            "description": "查询作物生长状态"
        },
        "irrigation_control": {
            "keywords": ["灌溉", "浇水", "供水", "滴灌", "喷灌", "缺水", "干旱"],
            "patterns": [r"(打开|关闭|开启|停止).*(水阀|灌溉|浇水)", r".*需要.*灌溉"],
            "description": "灌溉控制操作"
        },
        "fertilization_advice": {
            "keywords": ["施肥", "肥料", "氮磷钾", "有机肥", "追肥", "基肥", "营养"],
            "patterns": [r".*什么时候.*(施肥|追肥)", r".*需要.*什么肥"],
            "description": "施肥建议咨询"
        },
        "pest_detection": {
            "keywords": ["病虫害", "害虫", "病害", "虫子", "枯萎", "发黄", "腐烂", "斑点", "蚜虫", "飞虱"],
            "patterns": [r".*叶片.*(变黄|发黄|枯萎)", r".*出现.*(害虫|病斑|异常)"],
            "description": "病虫害检测与防治"
        },
        "harvest_planning": {
            "keywords": ["收割", "收获", "采收", "成熟", "收成", "产量"],
            "patterns": [r".*什么时候.*(收割|收获|采收)", r".*预计.*产量"],
            "description": "收获计划咨询"
        },
        "device_control": {
            "keywords": ["设备", "传感器", "摄像头", "阀门", "电机", "控制器", "在线", "离线"],
            "patterns": [r"(打开|关闭|重启).*(设备|摄像头|传感器)", r".*设备.*状态"],
            "description": "设备控制操作"
        },
        "data_query": {
            "keywords": ["数据", "记录", "历史", "报表", "统计", "查询", "导出"],
            "patterns": [r".*查看.*(数据|记录|报表)", r".*最近.*(天|周|月).*(数据|记录)"],
            "description": "数据查询与导出"
        },
        "system_status": {
            "keywords": ["系统", "状态", "运行", "健康", "监控", "告警", "异常"],
            "patterns": [r".*系统.*(怎么样|如何|状态)", r".*有没有.*(告警|异常|错误)"],
            "description": "系统状态查询"
        },
        "blockchain_trace": {
            "keywords": ["溯源", "追溯", "区块链", "记录上链", "产品信息", "来源"],
            "patterns": [r".*产品.*(溯源|追溯|来源)", r".*查看.*区块链"],
            "description": "区块链溯源查询"
        },
        "greeting": {
            "keywords": ["你好", "您好", "hi", "hello", "早上好", "晚上好", "在吗"],
            "patterns": [],
            "description": "问候语"
        },
        "help": {
            "keywords": ["帮助", "怎么用", "功能", "说明", "使用方法", "能做什么"],
            "patterns": [r".*怎么.*(用|操作|使用)", r".*有什么.*(功能|用途)"],
            "description": "获取帮助"
        }
    }

    # 农业实体识别词典
    ENTITY_DICT = {
        "crops": ["水稻", "小麦", "玉米", "大豆", "棉花", "油菜", "蔬菜", "果树", "花生", "高粱"],
        "zones": ["大棚A区", "大棚B区", "大棚C区", "温室", "露地", "A区", "B区", "C区",
                  "zone_a", "zone_b", "zone_c"],
        "devices": ["传感器", "摄像头", "水阀", "灌溉泵", "补光灯", "风机", "遮阳网"],
        "pests": ["稻飞虱", "蚜虫", "稻纵卷叶螟", "二化螟", "白粉病", "稻瘟病", "条纹叶枯病"],
        "time_expressions": ["今天", "明天", "后天", "昨天", "本周", "上周", "本月",
                             r"\d+天前", r"\d+小时前", r"最近\d+天"],
        "numbers": [r"\d+\.?\d*\s*(公斤|kg|吨|亩|公顷|升|L|度|%|℃)"]
    }

    # 情感词典
    POSITIVE_WORDS = ["好", "棒", "优秀", "不错", "满意", "喜欢", "正常", "健康", "顺利", "成功"]
    NEGATIVE_WORDS = ["差", "糟糕", "失败", "异常", "故障", "问题", "错误", "担心", "害怕", "严重"]

    # 回复模板
    RESPONSE_TEMPLATES = {
        "greeting": "您好！我是AI农业决策助手，可以帮您查询天气、分析作物状态、控制设备等。请问有什么需要帮助的吗？",
        "help": (
            "我能为您提供以下服务：\n"
            "🌤️ 天气查询 - 获取当前及未来天气预报\n"
            "🌾 作物管理 - 查询作物生长状态和管理建议\n"
            "💧 灌溉控制 - 智能灌溉决策和设备控制\n"
            "🧪 施肥建议 - 基于土壤和作物需求的施肥方案\n"
            "🐛 病虫害防治 - 识别和防治农业病虫害\n"
            "📊 数据分析 - 查询历史数据和生成报表\n"
            "🔗 溯源追踪 - 农产品区块链溯源查询\n"
            "您可以用自然语言告诉我您的需求！"
        ),
        "unknown": "抱歉，我没有完全理解您的问题。您可以尝试问我关于天气、作物、灌溉、病虫害等方面的问题，或者输入'帮助'查看我能做什么。",
        "query_weather": "好的，我来为您获取天气信息...",
        "irrigation_control": "收到灌溉指令，正在处理...",
        "pest_detection": "我来帮您分析病虫害情况...",
        "device_control": "正在执行设备控制指令...",
        "data_query": "正在查询相关数据...",
        "system_status": "正在获取系统状态...",
    }

    def __init__(self, language: str = "zh-CN", sentiment_analysis_enabled: bool = True):
        self.language = language
        self.sentiment_analysis_enabled = sentiment_analysis_enabled
        self._intent_cache: Dict[str, Any] = {}
        logger.info(f"NLPSkill 初始化完成，语言: {language}")

    # ──────────────────────────────────────────────
    #  核心公开方法
    # ──────────────────────────────────────────────

    def understand_intent(self, text: str) -> Dict[str, Any]:
        """
        识别用户意图

        Args:
            text: 用户输入文本

        Returns:
            意图识别结果，包含主意图、置信度和候选意图
        """
        text_clean = text.strip().lower()

        # 缓存检查
        if text_clean in self._intent_cache:
            return self._intent_cache[text_clean]

        scores: Dict[str, float] = {}

        for intent_name, config in self.INTENT_PATTERNS.items():
            score = 0.0
            # 关键词匹配
            for kw in config["keywords"]:
                if kw in text:
                    score += 1.0
            # 正则匹配（权重更高）
            for pattern in config["patterns"]:
                if re.search(pattern, text):
                    score += 2.0
            scores[intent_name] = score

        if not scores or max(scores.values()) == 0:
            result = {
                "intent": "unknown",
                "confidence": 0.0,
                "candidates": [],
                "description": "未能识别意图",
                "raw_text": text
            }
        else:
            sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            top_intent, top_score = sorted_intents[0]
            total = sum(s for _, s in sorted_intents if s > 0) or 1
            confidence = min(top_score / total, 1.0)

            candidates = [
                {
                    "intent": name,
                    "score": round(sc, 3),
                    "description": self.INTENT_PATTERNS[name]["description"]
                }
                for name, sc in sorted_intents[1:4] if sc > 0
            ]

            result = {
                "intent": top_intent,
                "confidence": round(confidence, 3),
                "description": self.INTENT_PATTERNS[top_intent]["description"],
                "candidates": candidates,
                "raw_text": text
            }

        self._intent_cache[text_clean] = result
        return result

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        从文本中提取农业实体

        Args:
            text: 输入文本

        Returns:
            按类别分组的实体字典
        """
        entities: Dict[str, List[str]] = {}

        for category, patterns in self.ENTITY_DICT.items():
            found: List[str] = []
            for pattern in patterns:
                if pattern.startswith("\\d") or pattern.startswith(r"\d"):
                    # 正则模式
                    matches = re.findall(pattern, text)
                    found.extend(matches)
                else:
                    # 精确词匹配
                    if pattern in text:
                        found.append(pattern)

            if found:
                entities[category] = list(dict.fromkeys(found))  # 去重保序

        return entities

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        分析文本情感倾向

        Args:
            text: 输入文本

        Returns:
            情感分析结果
        """
        if not self.sentiment_analysis_enabled:
            return {"sentiment": "neutral", "confidence": 0.5, "scores": {}}

        pos_count = sum(1 for w in self.POSITIVE_WORDS if w in text)
        neg_count = sum(1 for w in self.NEGATIVE_WORDS if w in text)

        total = pos_count + neg_count or 1
        pos_score = pos_count / total
        neg_score = neg_count / total

        if pos_score > neg_score and pos_score > 0.5:
            sentiment, confidence = "positive", pos_score
        elif neg_score > pos_score and neg_score > 0.5:
            sentiment, confidence = "negative", neg_score
        else:
            sentiment, confidence = "neutral", 0.5

        return {
            "sentiment": sentiment,
            "confidence": round(confidence, 3),
            "scores": {
                "positive": round(pos_score, 3),
                "negative": round(neg_score, 3),
                "neutral": round(1 - pos_score - neg_score + 0.001, 3)
            },
            "positive_keywords": [w for w in self.POSITIVE_WORDS if w in text],
            "negative_keywords": [w for w in self.NEGATIVE_WORDS if w in text]
        }

    def generate_response(
        self,
        intent: str,
        entities: Optional[Dict[str, List[str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        根据意图和上下文生成回复文本

        Args:
            intent: 识别出的意图
            entities: 提取的实体
            context: 附加上下文（如传感器数据）

        Returns:
            生成的回复字符串
        """
        entities = entities or {}
        context = context or {}

        base = self.RESPONSE_TEMPLATES.get(intent, self.RESPONSE_TEMPLATES["unknown"])

        # 补充实体信息
        extras: List[str] = []
        if entities.get("crops"):
            extras.append(f"作物: {', '.join(entities['crops'])}")
        if entities.get("zones"):
            extras.append(f"区域: {', '.join(entities['zones'])}")

        # 补充上下文
        if context.get("sensor_data"):
            sd = context["sensor_data"]
            if "temperature" in sd:
                extras.append(f"当前温度: {sd['temperature']}°C")
            if "humidity" in sd:
                extras.append(f"当前湿度: {sd['humidity']}%")
            if "soil_moisture" in sd:
                extras.append(f"土壤湿度: {sd['soil_moisture']}%")

        if extras:
            base += "\n\n📍 " + " | ".join(extras)

        return base

    def parse_command(self, text: str) -> Dict[str, Any]:
        """
        综合解析用户指令（意图 + 实体 + 情感 + 回复）

        Args:
            text: 用户输入文本

        Returns:
            完整解析结果
        """
        intent_result = self.understand_intent(text)
        entity_result = self.extract_entities(text)
        sentiment_result = self.analyze_sentiment(text) if self.sentiment_analysis_enabled else {}
        response = self.generate_response(intent_result["intent"], entity_result)

        return {
            "text": text,
            "intent": intent_result,
            "entities": entity_result,
            "sentiment": sentiment_result,
            "suggested_response": response,
            "timestamp": datetime.now().isoformat(),
            "requires_action": intent_result["intent"] not in ("greeting", "help", "unknown")
        }

    def batch_parse(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量解析多条指令"""
        return [self.parse_command(t) for t in texts]
