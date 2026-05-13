"""ML异常检测 - P2阶段，为故障自愈框架提供前置条件"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod
import threading

logger = logging.getLogger("hydraflow.ml_anomaly_detection")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not installed. Anomaly detection features will be limited.")
    
    # 创建一个简化的numpy模拟类
    class FakeNP:
        ndarray = list
        
        @staticmethod
        def array(x):
            return x
        
        @staticmethod
        def mean(x):
            if hasattr(x, '__iter__'):
                return sum(x) / len(x) if x else 0
            return x
        
        @staticmethod
        def std(x):
            if hasattr(x, '__iter__') and len(x) > 0:
                m = sum(x) / len(x)
                return (sum((v - m) ** 2 for v in x) / len(x)) ** 0.5
            return 0
        
        @staticmethod
        def abs(x):
            return abs(x)
        
        @staticmethod
        def sqrt(x):
            return x ** 0.5 if x >= 0 else 0
        
        @staticmethod
        def where(cond, x, y):
            return [x[i] if cond[i] else y[i] for i in range(len(cond))] if hasattr(cond, '__iter__') else (x if cond else y)
    
    np = FakeNP()


class AnomalyType(Enum):
    """异常类型"""
    POINT = "point"           # 点异常
    CONTEXTUAL = "contextual" # 上下文异常
    COLLECTIVE = "collective"  # 集体异常
    UNKNOWN = "unknown"


class AnomalySeverity(Enum):
    """异常严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AnomalyAlert:
    """异常告警"""
    alert_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    metric_name: str
    metric_value: float
    expected_value: float
    deviation_score: float
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    recommended_action: str = ""


@dataclass
class MetricDataPoint:
    """指标数据点"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class BaseAnomalyDetector(ABC):
    """异常检测器基类"""

    @abstractmethod
    async def detect(self, metric_name: str, value: float, context: Dict[str, Any] = None) -> Optional[AnomalyAlert]:
        """检测异常"""
        pass

    @abstractmethod
    async def train(self, historical_data: List[MetricDataPoint]):
        """训练模型"""
        pass


class StatisticalDetector(BaseAnomalyDetector):
    """统计方法异常检测器"""

    def __init__(
        self,
        window_size: int = 100,
        z_score_threshold: float = 3.0,
        std_factor: float = 2.5
    ):
        self.window_size = window_size
        self.z_score_threshold = z_score_threshold
        self.std_factor = std_factor

        self._data_buffer: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    async def detect(self, metric_name: str, value: float, context: Dict[str, Any] = None) -> Optional[AnomalyAlert]:
        """检测异常"""
        with self._lock:
            if metric_name not in self._data_buffer:
                self._data_buffer[metric_name] = []

            self._data_buffer[metric_name].append(value)

            if len(self._data_buffer[metric_name]) > self.window_size:
                self._data_buffer[metric_name].pop(0)

            values = self._data_buffer[metric_name]

            if len(values) < 10:
                return None

            mean = np.mean(values)
            std = np.std(values)

            if std < 0.001:
                return None

            z_score = abs(value - mean) / std

            if z_score > self.z_score_threshold:
                return AnomalyAlert(
                    alert_id=f"stat_{metric_name}_{int(time.time() * 1000)}",
                    anomaly_type=AnomalyType.POINT,
                    severity=self._get_severity(z_score),
                    metric_name=metric_name,
                    metric_value=value,
                    expected_value=mean,
                    deviation_score=z_score,
                    context={"method": "z_score", "threshold": self.z_score_threshold},
                    recommended_action=f"Check {metric_name} - value {value} deviates significantly from mean {mean:.2f}"
                )

        return None

    def _get_severity(self, z_score: float) -> AnomalySeverity:
        if z_score > 5:
            return AnomalySeverity.CRITICAL
        elif z_score > 4:
            return AnomalySeverity.HIGH
        elif z_score > 3:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    async def train(self, historical_data: List[MetricDataPoint]):
        """统计检测器不需要显式训练"""
        pass


class IsolationForestDetector(BaseAnomalyDetector):
    """孤立森林异常检测器"""

    def __init__(
        self,
        n_estimators: int = 100,
        max_samples: int = 256,
        contamination: float = 0.1,
        threshold: float = -0.5
    ):
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.threshold = threshold

        self._is_fitted = False
        self._tree_depth: int = 0
        self._avg_path_length: float = 0.0

    async def detect(self, metric_name: str, value: float, context: Dict[str, Any] = None) -> Optional[AnomalyAlert]:
        """检测异常"""
        if not self._is_fitted:
            logger.warning("IsolationForest not fitted, using fallback")
            return None

        score = self._calculate_isolation_score(value)

        if score < self.threshold:
            return AnomalyAlert(
                alert_id=f"if_{metric_name}_{int(time.time() * 1000)}",
                anomaly_type=AnomalyType.UNKNOWN,
                severity=self._get_severity(score),
                metric_name=metric_name,
                metric_value=value,
                expected_value=0,
                deviation_score=abs(score),
                context={"method": "isolation_forest"},
                recommended_action=f"Isolation score {score:.3f} below threshold {self.threshold}"
            )

        return None

    def _calculate_isolation_score(self, value: float) -> float:
        """计算孤立分数（简化版）"""
        import random
        random.seed(42)

        path_lengths = []
        for _ in range(self.n_estimators):
            depth = 0
            current_value = value

            while depth < self._tree_depth * 2:
                threshold = random.uniform(-1, 1)
                if current_value < threshold:
                    current_value = current_value * 2
                else:
                    current_value = current_value * 0.5
                depth += 1

                if abs(current_value) > 100:
                    break

            path_lengths.append(depth)

        avg_path = sum(path_lengths) / len(path_lengths)
        score = -(avg_path / (self._avg_path_length + 0.001))

        return score

    def _get_severity(self, score: float) -> AnomalySeverity:
        if score < -0.9:
            return AnomalySeverity.CRITICAL
        elif score < -0.7:
            return AnomalySeverity.HIGH
        elif score < -0.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    async def train(self, historical_data: List[MetricDataPoint]):
        """训练孤立森林"""
        if len(historical_data) < 10:
            logger.warning("Insufficient data for training")
            return

        self._tree_depth = int(np.log2(len(historical_data)))
        self._avg_path_length = 2 * (np.log(len(historical_data) - 1) + 0.5772156649) - (2 * (len(historical_data) - 1) / len(historical_data))
        self._is_fitted = True

        logger.info(f"IsolationForest trained with {len(historical_data)} samples")


class MLAnomalyDetector:
    """ML异常检测器 - 集成多种检测方法"""

    def __init__(self):
        self.detectors: Dict[str, BaseAnomalyDetector] = {}
        self.anomaly_callbacks: List[Callable] = []
        self.alert_history: List[AnomalyAlert] = []
        self.active_alerts: Dict[str, AnomalyAlert] = {}

        # 注册默认检测器
        self.register_detector("statistical", StatisticalDetector())

        # 统计信息
        self.stats = {
            "total_evaluations": 0,
            "anomalies_detected": 0,
            "alerts_fired": 0,
            "detectors_count": 1,
        }

        self._lock = threading.Lock()

        logger.info("MLAnomalyDetector initialized")

    def register_detector(self, name: str, detector: BaseAnomalyDetector):
        """注册检测器"""
        self.detectors[name] = detector
        self.stats["detectors_count"] = len(self.detectors)
        logger.info(f"Registered detector: {name}")

    def register_anomaly_callback(self, callback: Callable):
        """注册异常回调（用于触发故障自愈框架）"""
        self.anomaly_callbacks.append(callback)

    async def evaluate_metric(
        self,
        metric_name: str,
        value: float,
        context: Dict[str, Any] = None
    ) -> Optional[AnomalyAlert]:
        """评估指标"""
        self.stats["total_evaluations"] += 1

        alert = None

        for name, detector in self.detectors.items():
            try:
                result = await detector.detect(metric_name, value, context)
                if result:
                    alert = result
                    break
            except Exception as e:
                logger.error(f"Detector {name} error: {e}")

        if alert:
            await self._handle_anomaly(alert)

        return alert

    async def _handle_anomaly(self, alert: AnomalyAlert):
        """处理检测到的异常"""
        self.stats["anomalies_detected"] += 1

        with self._lock:
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)

            if len(self.alert_history) > 10000:
                self.alert_history = self.alert_history[-5000:]

        # 触发回调
        for callback in self.anomaly_callbacks:
            try:
                await callback(alert)
                self.stats["alerts_fired"] += 1
            except Exception as e:
                logger.error(f"Anomaly callback error: {e}")

        logger.warning(
            f"Anomaly detected: {alert.metric_name}={alert.metric_value:.2f} "
            f"(expected: {alert.expected_value:.2f}), severity: {alert.severity.value}"
        )

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        with self._lock:
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
                logger.info(f"Resolved alert: {alert_id}")

    async def train(self, historical_data: Dict[str, List[MetricDataPoint]]):
        """训练所有检测器"""
        for name, detector in self.detectors.items():
            if hasattr(detector, 'train'):
                metric_data = historical_data.get(name, [])
                if metric_data:
                    await detector.train(metric_data)
                    logger.info(f"Trained detector: {name} with {len(metric_data)} samples")

    def get_active_alerts(self) -> List[AnomalyAlert]:
        """获取活跃告警"""
        with self._lock:
            return list(self.active_alerts.values())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        with self._lock:
            return {
                "total_evaluations": self.stats["total_evaluations"],
                "anomalies_detected": self.stats["anomalies_detected"],
                "alerts_fired": self.stats["alerts_fired"],
                "active_alerts": len(self.active_alerts),
                "registered_detectors": list(self.detectors.keys()),
                "detectors_count": self.stats["detectors_count"],
            }


# 全局单例
_anomaly_detector_instance: Optional[MLAnomalyDetector] = None


def get_anomaly_detector() -> MLAnomalyDetector:
    """获取异常检测器单例"""
    global _anomaly_detector_instance
    if _anomaly_detector_instance is None:
        _anomaly_detector_instance = MLAnomalyDetector()
    return _anomaly_detector_instance
