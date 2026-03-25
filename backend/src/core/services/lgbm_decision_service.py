"""
LightGBM 快速决策服务 — 农业智能决策支持

功能：
  1. 灌溉决策     — 基于土壤湿度/温度/蒸散量预测是否需要灌溉
  2. 病害风险评估  — 基于环境参数评估病害爆发概率
  3. 施肥决策     — 基于土壤 NPK/pH/EC 给出施肥建议
  4. 采收时机预测  — 基于积温/天气预测最佳采收窗口

特点：
  - 毫秒级推理（<5ms）
  - 可在线增量更新（LightGBM 支持 continue_training）
  - 支持特征重要性输出，决策可解释
  - 无需 GPU，CPU 高效
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── 懒加载 LightGBM ───────────────────────────────────────────────────────────
_lgb_loaded = False
_lgb = None


def _load_lgb():
    """延迟加载 lightgbm，确保与 JAX 环境兼容"""
    global _lgb_loaded, _lgb
    if _lgb_loaded:
        return
    try:
        import lightgbm as lgb
        _lgb = lgb
        _lgb_loaded = True
        logger.info(f"LightGBM {lgb.__version__} 加载成功")
    except ImportError as e:
        logger.error(f"LightGBM 加载失败: {e}")
        raise


# ── 数据结构 ─────────────────────────────────────────────────────────────────

@dataclass
class DecisionResult:
    """决策结果"""
    task: str                          # "irrigation" / "disease_risk" / ...
    decision: str                      # 决策标签（如 "irrigate_now"）
    confidence: float                  # 置信度 0~1
    probability: Dict[str, float]      # 各类别概率
    feature_importance: Dict[str, float]
    recommendation: str                # 中文建议
    inference_time_ms: float
    is_trained: bool
    fallback_used: bool = False        # 是否使用了规则回退
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "decision": self.decision,
            "confidence": round(self.confidence, 4),
            "probability": {k: round(v, 4) for k, v in self.probability.items()},
            "feature_importance": {k: round(v, 4) for k, v in self.feature_importance.items()},
            "recommendation": self.recommendation,
            "inference_time_ms": round(self.inference_time_ms, 2),
            "is_trained": self.is_trained,
            "fallback_used": self.fallback_used,
            **self.extra,
        }


# ── 任务配置 ─────────────────────────────────────────────────────────────────

TASK_CONFIGS = {
    "irrigation": {
        "features": ["soil_moisture", "temperature", "humidity", "evapotranspiration",
                     "rainfall_24h", "forecast_temp", "plant_stage"],
        "labels":   ["no_action", "irrigate_soon", "irrigate_now", "urgent_irrigation"],
        "label_names": {
            "no_action":         "无需灌溉 — 土壤湿度充足",
            "irrigate_soon":     "计划灌溉 — 建议 24h 内灌溉",
            "irrigate_now":      "立即灌溉 — 土壤偏干，建议尽快",
            "urgent_irrigation": "紧急灌溉 — 土壤严重缺水，立即执行",
        },
    },
    "disease_risk": {
        "features": ["temperature", "humidity", "leaf_wetness", "rainfall_48h",
                     "wind_speed", "crop_type_encoded", "growth_stage"],
        "labels":   ["low_risk", "moderate_risk", "high_risk", "critical_risk"],
        "label_names": {
            "low_risk":      "低风险 — 环境条件不利于病害发生",
            "moderate_risk": "中等风险 — 建议加强巡视检查",
            "high_risk":     "高风险 — 建议预防性喷药",
            "critical_risk": "危险 — 病害爆发条件已具备，立即防治",
        },
    },
    "fertilization": {
        "features": ["soil_n", "soil_p", "soil_k", "soil_ph", "ec",
                     "crop_type_encoded", "growth_stage", "last_fertilize_days"],
        "labels":   ["no_need", "light_fertilize", "standard_fertilize", "heavy_fertilize"],
        "label_names": {
            "no_need":          "暂不施肥 — 养分充足",
            "light_fertilize":  "轻量追肥 — 建议补充微量元素",
            "standard_fertilize":"标准施肥 — 按常规配方施用",
            "heavy_fertilize":  "重量补肥 — 严重缺肥，需加大用量",
        },
    },
    "harvest_timing": {
        "features": ["accumulated_temperature", "days_since_flowering",
                     "fruit_color_index", "sugar_content", "firmness",
                     "weather_forecast_rain", "market_price_index"],
        "labels":   ["too_early", "approaching", "optimal", "overdue"],
        "label_names": {
            "too_early": "尚未成熟 — 继续等待",
            "approaching": "即将成熟 — 建议 3-5 天后采收",
            "optimal":   "最佳采收期 — 建议立即安排采收",
            "overdue":   "过熟风险 — 立即采收，防止品质下降",
        },
    },
}


# ── LightGBM 决策服务 ─────────────────────────────────────────────────────────

class LightGBMDecisionService:
    """
    基于 LightGBM 的农业快速决策服务

    每个 task（灌溉/病害/施肥/采收）维护独立的模型实例。
    未训练时自动回退到规则 based 决策。
    """

    def __init__(self, model_save_dir: Optional[str] = None):
        self._models: Dict[str, Any] = {}          # task -> LightGBM model
        self._is_trained: Dict[str, bool] = {}
        self._model_save_dir = model_save_dir or os.path.join(
            os.path.dirname(__file__), "../../../models/lgbm"
        )
        os.makedirs(self._model_save_dir, exist_ok=True)

        logger.info(f"LightGBMDecisionService 初始化 | 模型目录: {self._model_save_dir}")

    # ── 训练 ──────────────────────────────────────────────────────────────────

    def fit(
        self,
        task: str,
        X_train: List[Dict[str, float]],
        y_train: List[int],
        num_boost_round: int = 100,
        early_stopping_rounds: Optional[int] = 20,
        X_val: Optional[List[Dict[str, float]]] = None,
        y_val: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        训练指定任务的 LightGBM 模型。

        Args:
            task:          任务名（irrigation / disease_risk / fertilization / harvest_timing）
            X_train:       训练特征列表，每条为字典
            y_train:       训练标签（整数类别）
            num_boost_round: 提升轮数
            X_val/y_val:   验证集（可选，用于 early stopping）

        Returns:
            训练结果信息
        """
        _load_lgb()

        if task not in TASK_CONFIGS:
            raise ValueError(f"未知任务: {task}，支持: {list(TASK_CONFIGS.keys())}")

        cfg = TASK_CONFIGS[task]
        feature_names = cfg["features"]
        num_classes = len(cfg["labels"])

        # 构建训练矩阵
        def to_matrix(records):
            return np.array([
                [r.get(f, 0.0) for f in feature_names]
                for r in records
            ])

        X = to_matrix(X_train)
        y = np.array(y_train, dtype=np.int32)

        train_set = _lgb.Dataset(X, label=y, feature_name=feature_names)
        valid_sets = [train_set]
        valid_names = ["train"]

        if X_val and y_val:
            X_v = to_matrix(X_val)
            y_v = np.array(y_val, dtype=np.int32)
            val_set = _lgb.Dataset(X_v, label=y_v, feature_name=feature_names)
            valid_sets.append(val_set)
            valid_names.append("valid")

        params = {
            "objective":     "multiclass",
            "num_class":     num_classes,
            "metric":        "multi_logloss",
            "n_jobs":        -1,
            "verbosity":    -1,
            "seed":          42,
            "learning_rate": 0.05,
            "num_leaves":    31,
            "max_depth":     6,
            "min_data_in_leaf": 10,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq":  5,
        }

        t0 = time.time()
        callbacks = [_lgb.log_evaluation(period=50)]
        if early_stopping_rounds and X_val:
            callbacks.append(_lgb.early_stopping(early_stopping_rounds))

        model = _lgb.train(
            params,
            train_set,
            num_boost_round=num_boost_round,
            valid_sets=valid_sets,
            valid_names=valid_names,
            callbacks=callbacks,
        )

        elapsed = (time.time() - t0) * 1000
        self._models[task] = model
        self._is_trained[task] = True

        # 保存模型
        save_path = os.path.join(self._model_save_dir, f"{task}.lgbm")
        model.save_model(save_path)
        logger.info(f"模型已保存: {save_path}")

        logger.info(
            f"LightGBM [{task}] 训练完成 | 样本: {len(X_train)} | "
            f"轮数: {model.num_trees()} | 耗时: {elapsed:.0f}ms"
        )

        return {
            "task": task,
            "n_samples": len(X_train),
            "n_trees": model.num_trees(),
            "feature_names": feature_names,
            "training_time_ms": round(elapsed, 1),
            "model_saved_to": save_path,
        }

    def load_model(self, task: str) -> bool:
        """从磁盘加载已保存的模型"""
        _load_lgb()
        save_path = os.path.join(self._model_save_dir, f"{task}.lgbm")
        if not os.path.exists(save_path):
            logger.debug(f"未找到已保存模型: {save_path}")
            return False
        try:
            self._models[task] = _lgb.Booster(model_file=save_path)
            self._is_trained[task] = True
            logger.info(f"模型加载成功: {save_path}")
            return True
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False

    # ── 推理 ──────────────────────────────────────────────────────────────────

    def predict(
        self, task: str, features: Dict[str, float]
    ) -> DecisionResult:
        """
        执行单条决策推理。

        未训练时自动使用规则回退。
        """
        t0 = time.time()

        if task not in TASK_CONFIGS:
            raise ValueError(f"未知任务: {task}")

        cfg = TASK_CONFIGS[task]
        feature_names = cfg["features"]
        label_names_map = cfg["label_names"]
        label_keys = cfg["labels"]

        # 尝试加载已保存模型（如果内存里没有）
        if task not in self._models:
            self.load_model(task)

        is_trained = self._is_trained.get(task, False)

        if is_trained:
            # ── ML 推理 ────────────────────────────────────────────────────
            X = np.array([[features.get(f, 0.0) for f in feature_names]])
            probs = self._models[task].predict(X)[0]  # shape: (num_classes,)

            pred_idx = int(np.argmax(probs))
            confidence = float(probs[pred_idx])
            probability = {k: float(probs[i]) for i, k in enumerate(label_keys)}

            # 特征重要性（归一化）
            fi = self._models[task].feature_importance("gain")
            fi_norm = fi / (fi.sum() + 1e-8)
            feature_importance = dict(zip(feature_names, fi_norm.tolist()))

            decision = label_keys[pred_idx]
            recommendation = label_names_map[decision]
            fallback = False

        else:
            # ── 规则回退（无需训练，立即可用）────────────────────────────
            pred_idx, confidence, decision, recommendation = self._rule_fallback(task, features)
            probability = {k: (confidence if k == decision else (1 - confidence) / max(len(label_keys) - 1, 1))
                           for k in label_keys}
            feature_importance = {}
            fallback = True

        elapsed = (time.time() - t0) * 1000
        return DecisionResult(
            task=task,
            decision=decision,
            confidence=confidence,
            probability=probability,
            feature_importance=feature_importance,
            recommendation=recommendation,
            inference_time_ms=elapsed,
            is_trained=is_trained,
            fallback_used=fallback,
        )

    # ── 规则回退（农业领域专家规则）─────────────────────────────────────────

    def _rule_fallback(
        self, task: str, features: Dict[str, float]
    ) -> Tuple[int, float, str, str]:
        """无 ML 模型时的专家规则决策"""
        cfg = TASK_CONFIGS[task]
        label_keys = cfg["labels"]
        label_names_map = cfg["label_names"]

        if task == "irrigation":
            sm = features.get("soil_moisture", 50.0)
            if sm < 20:
                d, c = "urgent_irrigation", 0.95
            elif sm < 35:
                d, c = "irrigate_now", 0.80
            elif sm < 55:
                d, c = "irrigate_soon", 0.60
            else:
                d, c = "no_action", 0.85

        elif task == "disease_risk":
            h = features.get("humidity", 60.0)
            t = features.get("temperature", 20.0)
            lw = features.get("leaf_wetness", 0.0)
            # 高湿+适温+叶面潮湿 → 高风险
            score = (h > 80) + (15 < t < 30) + (lw > 0.5)
            if score >= 3:
                d, c = "critical_risk", 0.85
            elif score == 2:
                d, c = "high_risk", 0.70
            elif score == 1:
                d, c = "moderate_risk", 0.60
            else:
                d, c = "low_risk", 0.80

        elif task == "fertilization":
            n = features.get("soil_n", 100.0)
            p = features.get("soil_p", 50.0)
            k = features.get("soil_k", 80.0)
            deficit_count = (n < 60) + (p < 30) + (k < 50)
            if deficit_count >= 2:
                d, c = "heavy_fertilize", 0.80
            elif deficit_count == 1:
                d, c = "standard_fertilize", 0.70
            elif n < 100 or p < 40 or k < 70:
                d, c = "light_fertilize", 0.65
            else:
                d, c = "no_need", 0.80

        elif task == "harvest_timing":
            days = features.get("days_since_flowering", 0.0)
            color = features.get("fruit_color_index", 0.5)
            if days > 90 and color > 0.9:
                d, c = "overdue", 0.80
            elif days > 75 and color > 0.7:
                d, c = "optimal", 0.75
            elif days > 60:
                d, c = "approaching", 0.65
            else:
                d, c = "too_early", 0.85

        else:
            d, c = label_keys[0], 0.5

        idx = label_keys.index(d)
        return idx, c, d, label_names_map[d]

    # ── 工具方法 ─────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """返回所有任务的模型状态"""
        status = {}
        for task in TASK_CONFIGS:
            trained = self._is_trained.get(task, False)
            model_path = os.path.join(self._model_save_dir, f"{task}.lgbm")
            status[task] = {
                "is_trained": trained,
                "model_saved": os.path.exists(model_path),
                "features": TASK_CONFIGS[task]["features"],
                "labels": TASK_CONFIGS[task]["labels"],
            }
        return {
            "service": "LightGBMDecisionService",
            "tasks": status,
            "model_save_dir": self._model_save_dir,
        }

    def predict_batch(
        self, task: str, features_list: List[Dict[str, float]]
    ) -> List[DecisionResult]:
        """批量推理"""
        return [self.predict(task, f) for f in features_list]


# ── 全局单例 ─────────────────────────────────────────────────────────────────
_lgbm_service_instance: Optional[LightGBMDecisionService] = None


def get_lgbm_service() -> LightGBMDecisionService:
    """获取全局 LightGBM 决策服务单例"""
    global _lgbm_service_instance
    if _lgbm_service_instance is None:
        _lgbm_service_instance = LightGBMDecisionService()
    return _lgbm_service_instance
