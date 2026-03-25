"""
异常检测服务 — 基于 scikit-learn
用于农业传感器数据的实时异常检测

支持三种检测算法：
  1. IsolationForest  — 通用异常检测（无需标注数据，推荐）
  2. LocalOutlierFactor — 密度型异常检测（适合局部异常）
  3. OneClassSVM       — 监督式异常边界学习

使用场景：
  - 土壤湿度/温度传感器异常
  - 光照传感器故障
  - CO₂/pH 值突变
  - 灌溉流量异常
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── 懒加载 sklearn（避免与 JAX 冲突）────────────────────────────────────────
_sklearn_loaded = False
_IsolationForest = None
_LocalOutlierFactor = None
_OneClassSVM = None
_StandardScaler = None


def _load_sklearn():
    """延迟加载 sklearn，确保与 JAX 环境兼容"""
    global _sklearn_loaded, _IsolationForest, _LocalOutlierFactor
    global _OneClassSVM, _StandardScaler

    if _sklearn_loaded:
        return

    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.neighbors import LocalOutlierFactor
        from sklearn.svm import OneClassSVM
        from sklearn.preprocessing import StandardScaler

        _IsolationForest = IsolationForest
        _LocalOutlierFactor = LocalOutlierFactor
        _OneClassSVM = OneClassSVM
        _StandardScaler = StandardScaler
        _sklearn_loaded = True
        logger.info("scikit-learn 加载成功")
    except ImportError as e:
        logger.error(f"scikit-learn 加载失败: {e}")
        raise


# ── 数据结构 ─────────────────────────────────────────────────────────────────

@dataclass
class SensorReading:
    """单次传感器读数"""
    timestamp: float
    values: Dict[str, float]   # {"temperature": 25.3, "humidity": 65.0, ...}


@dataclass
class AnomalyResult:
    """异常检测结果"""
    is_anomaly: bool
    score: float                # 异常分数（越低/越负 = 越异常）
    anomaly_features: List[str] # 触发异常的具体特征名
    severity: str               # "normal" / "warning" / "critical"
    message: str
    detection_time_ms: float
    model_name: str
    raw_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_anomaly": self.is_anomaly,
            "score": round(self.score, 4),
            "anomaly_features": self.anomaly_features,
            "severity": self.severity,
            "message": self.message,
            "detection_time_ms": round(self.detection_time_ms, 2),
            "model_name": self.model_name,
            "raw_scores": {k: round(v, 4) for k, v in self.raw_scores.items()},
        }


# ── 正常范围配置（农业场景默认值）────────────────────────────────────────────
NORMAL_RANGES: Dict[str, Tuple[float, float]] = {
    "temperature":    (-5.0,  45.0),   # ℃
    "humidity":       (10.0,  95.0),   # %RH
    "soil_moisture":  (10.0,  90.0),   # %
    "soil_ph":        (4.0,    9.0),   # pH
    "co2":            (300.0, 2000.0), # ppm
    "light":          (0.0,  100000.0),# lux
    "ec":             (0.0,    5.0),   # mS/cm
    "pressure":       (900.0, 1100.0), # hPa
    "wind_speed":     (0.0,   30.0),   # m/s
    "rainfall":       (0.0,  200.0),   # mm/h
}


# ── 主服务类 ─────────────────────────────────────────────────────────────────

class AnomalyDetectionService:
    """
    农业传感器异常检测服务

    三级检测策略：
    1. 硬阈值检测（规则based，无需训练，立即可用）
    2. 统计检测（Z-score，滑动窗口，低延迟）
    3. ML模型检测（IsolationForest，需要历史数据训练）
    """

    def __init__(
        self,
        algorithm: str = "isolation_forest",
        contamination: float = 0.05,   # 预期异常比例
        z_score_threshold: float = 3.0,
        window_size: int = 100,         # 滑动窗口大小
        normal_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    ):
        self._algorithm = algorithm
        self._contamination = contamination
        self._z_score_threshold = z_score_threshold
        self._window_size = window_size
        self._normal_ranges = normal_ranges or NORMAL_RANGES.copy()

        self._model = None
        self._scaler = None
        self._is_trained = False
        self._feature_names: List[str] = []

        # 滑动窗口（用于统计方法）
        self._history: List[List[float]] = []

        logger.info(
            f"AnomalyDetectionService 初始化 | 算法: {algorithm} | "
            f"contamination: {contamination} | 窗口: {window_size}"
        )

    # ── 规则检测（立即可用，无需训练）─────────────────────────────────────────

    def check_hard_thresholds(
        self, values: Dict[str, float]
    ) -> Tuple[bool, List[str], str]:
        """
        硬阈值检测，基于预设的正常范围。

        Returns:
            (is_anomaly, anomaly_features, severity)
        """
        anomaly_features = []
        critical_features = []

        for name, value in values.items():
            if name not in self._normal_ranges:
                continue
            lo, hi = self._normal_ranges[name]
            if value < lo or value > hi:
                anomaly_features.append(name)
                # 超出范围 20% 以上视为 critical
                range_span = hi - lo
                margin = range_span * 0.2
                if value < lo - margin or value > hi + margin:
                    critical_features.append(name)

        if critical_features:
            return True, anomaly_features, "critical"
        elif anomaly_features:
            return True, anomaly_features, "warning"
        return False, [], "normal"

    # ── 统计检测（Z-score 滑动窗口）───────────────────────────────────────────

    def check_z_score(
        self, values: Dict[str, float]
    ) -> Tuple[bool, float, List[str]]:
        """
        基于滑动窗口的 Z-score 统计异常检测。
        至少需要 10 个历史点才能计算，否则返回 not-anomaly。
        """
        if not self._feature_names:
            self._feature_names = sorted(values.keys())

        vec = [values.get(f, 0.0) for f in self._feature_names]
        self._history.append(vec)
        if len(self._history) > self._window_size:
            self._history.pop(0)

        if len(self._history) < 10:
            return False, 0.0, []  # 数据不足

        hist_arr = np.array(self._history)
        mean = hist_arr.mean(axis=0)
        std = hist_arr.std(axis=0) + 1e-8

        z_scores = np.abs((np.array(vec) - mean) / std)
        anomaly_mask = z_scores > self._z_score_threshold
        anomaly_features = [
            self._feature_names[i]
            for i in range(len(self._feature_names))
            if anomaly_mask[i]
        ]

        max_z = float(z_scores.max())
        is_anomaly = bool(anomaly_mask.any())
        return is_anomaly, max_z, anomaly_features

    # ── ML 模型训练 ───────────────────────────────────────────────────────────

    def fit(self, historical_data: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        用历史数据训练异常检测模型。

        Args:
            historical_data: 历史正常读数列表，如 [{"temperature": 25.0, ...}, ...]

        Returns:
            训练结果信息
        """
        _load_sklearn()

        if not historical_data:
            raise ValueError("训练数据不能为空")

        # 统一特征名（排序以保证一致性）
        all_keys = set()
        for d in historical_data:
            all_keys.update(d.keys())
        self._feature_names = sorted(all_keys)

        # 构建训练矩阵
        X = np.array([
            [d.get(f, 0.0) for f in self._feature_names]
            for d in historical_data
        ])

        # 标准化
        self._scaler = _StandardScaler()
        X_scaled = self._scaler.fit_transform(X)

        # 训练模型
        t0 = time.time()
        if self._algorithm == "isolation_forest":
            self._model = _IsolationForest(
                contamination=self._contamination,
                random_state=42,
                n_estimators=100,
            )
            self._model.fit(X_scaled)
        elif self._algorithm == "lof":
            self._model = _LocalOutlierFactor(
                contamination=self._contamination,
                novelty=True,  # 必须 True 才支持 predict
            )
            self._model.fit(X_scaled)
        elif self._algorithm == "ocsvm":
            self._model = _OneClassSVM(nu=self._contamination)
            self._model.fit(X_scaled)
        else:
            raise ValueError(f"不支持的算法: {self._algorithm}")

        elapsed = (time.time() - t0) * 1000
        self._is_trained = True

        logger.info(
            f"异常检测模型训练完成 | 算法: {self._algorithm} | "
            f"样本数: {len(historical_data)} | 耗时: {elapsed:.0f}ms"
        )

        return {
            "algorithm": self._algorithm,
            "n_samples": len(historical_data),
            "n_features": len(self._feature_names),
            "feature_names": self._feature_names,
            "training_time_ms": round(elapsed, 1),
        }

    # ── 在线检测（三级联合）──────────────────────────────────────────────────

    def detect(
        self, values: Dict[str, float], use_ml: bool = True
    ) -> AnomalyResult:
        """
        三级联合异常检测：硬阈值 → Z-score → ML模型

        Args:
            values:  传感器读数字典
            use_ml:  是否使用 ML 模型（需要先调用 fit）

        Returns:
            AnomalyResult
        """
        t0 = time.time()
        raw_scores: Dict[str, float] = {}

        # ── Level 1：硬阈值 ────────────────────────────────────────────────
        hard_anomaly, hard_features, hard_severity = self.check_hard_thresholds(values)

        # ── Level 2：Z-score 统计 ──────────────────────────────────────────
        z_anomaly, max_z, z_features = self.check_z_score(values)
        raw_scores["max_z_score"] = max_z

        # ── Level 3：ML 模型 ───────────────────────────────────────────────
        ml_anomaly = False
        ml_score = 0.0
        ml_features: List[str] = []

        if use_ml and self._is_trained and self._scaler and self._model:
            try:
                vec = np.array([[values.get(f, 0.0) for f in self._feature_names]])
                vec_scaled = self._scaler.transform(vec)
                prediction = int(self._model.predict(vec_scaled)[0])  # -1=anomaly, 1=normal
                ml_score = float(self._model.score_samples(vec_scaled)[0])
                raw_scores["ml_score"] = ml_score
                ml_anomaly = prediction == -1
                if ml_anomaly:
                    # 用特征重要性（近似）找出最可疑特征
                    ml_features = self._feature_names  # 简化版，返回所有特征
            except Exception as e:
                logger.warning(f"ML 检测失败（回退到规则检测）: {e}")

        # ── 综合判断 ────────────────────────────────────────────────────────
        all_anomaly_features = list(set(hard_features + z_features + ml_features))
        is_anomaly = hard_anomaly or z_anomaly or ml_anomaly

        # 严重程度优先级：critical > warning > normal
        if hard_severity == "critical":
            severity = "critical"
        elif hard_anomaly or (z_anomaly and max_z > self._z_score_threshold * 1.5):
            severity = "warning"
        elif is_anomaly:
            severity = "warning"
        else:
            severity = "normal"

        # 综合分数（越低越异常，-1~1 区间）
        composite_score = ml_score if ml_anomaly else (-max_z / 10.0 if z_anomaly else 1.0)
        raw_scores["composite"] = composite_score

        # 生成描述消息
        if is_anomaly:
            features_str = "、".join(all_anomaly_features[:5]) if all_anomaly_features else "未知"
            message = (
                f"[{severity.upper()}] 检测到异常 | "
                f"异常特征: {features_str} | "
                f"Z-score 最大值: {max_z:.2f}"
            )
        else:
            message = f"传感器数据正常 | Z-score 最大值: {max_z:.2f}"

        elapsed = (time.time() - t0) * 1000
        return AnomalyResult(
            is_anomaly=is_anomaly,
            score=composite_score,
            anomaly_features=all_anomaly_features,
            severity=severity,
            message=message,
            detection_time_ms=elapsed,
            model_name=(
                f"{self._algorithm}+zscore+threshold"
                if self._is_trained else "zscore+threshold"
            ),
            raw_scores=raw_scores,
        )

    # ── 工具方法 ─────────────────────────────────────────────────────────────

    def set_normal_ranges(self, ranges: Dict[str, Tuple[float, float]]) -> None:
        """更新传感器正常范围（动态适应不同农业环境）"""
        self._normal_ranges.update(ranges)
        logger.info(f"正常范围已更新: {list(ranges.keys())}")

    def get_status(self) -> Dict[str, Any]:
        """返回服务状态"""
        return {
            "algorithm": self._algorithm,
            "is_trained": self._is_trained,
            "feature_names": self._feature_names,
            "history_size": len(self._history),
            "window_size": self._window_size,
            "contamination": self._contamination,
            "z_score_threshold": self._z_score_threshold,
            "supported_sensors": list(self._normal_ranges.keys()),
        }


# ── 全局单例 ─────────────────────────────────────────────────────────────────
_anomaly_service_instance: Optional[AnomalyDetectionService] = None


def get_anomaly_service() -> AnomalyDetectionService:
    """获取全局异常检测服务单例"""
    global _anomaly_service_instance
    if _anomaly_service_instance is None:
        _anomaly_service_instance = AnomalyDetectionService()
    return _anomaly_service_instance


def reset_anomaly_service(**kwargs) -> AnomalyDetectionService:
    """重置异常检测服务（用于切换算法或参数）"""
    global _anomaly_service_instance
    _anomaly_service_instance = AnomalyDetectionService(**kwargs)
    return _anomaly_service_instance
