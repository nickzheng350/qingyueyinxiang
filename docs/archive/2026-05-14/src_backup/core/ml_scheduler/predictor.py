"""调度预测器 - 使用ML模型预测最优调度决策"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    
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
        def argmax(x):
            if hasattr(x, '__iter__') and len(x) > 0:
                return max(range(len(x)), key=lambda i: x[i])
            return 0
        
        @staticmethod
        def argmin(x):
            if hasattr(x, '__iter__') and len(x) > 0:
                return min(range(len(x)), key=lambda i: x[i])
            return 0
        
        @staticmethod
        def max(x):
            return max(x) if hasattr(x, '__iter__') else x
        
        @staticmethod
        def min(x):
            return min(x) if hasattr(x, '__iter__') else x
        
        @staticmethod
        def sum(x):
            return sum(x) if hasattr(x, '__iter__') else x
        
        @staticmethod
        def dot(x, y):
            if hasattr(x, '__iter__') and hasattr(y, '__iter__'):
                return sum(a * b for a, b in zip(x, y))
            return x * y
        
        @staticmethod
        def concatenate(arrays):
            result = []
            for arr in arrays:
                if hasattr(arr, '__iter__'):
                    result.extend(arr)
                else:
                    result.append(arr)
            return result
    
    np = FakeNP()

from .trainer import TaskExecutionRecord, MLFeatureExtractor, ModelManager, get_model_manager

logger = logging.getLogger("hydraflow.ml_scheduler.predictor")


class PredictionType(Enum):
    """预测类型"""
    PRIORITY = "priority"           # 任务优先级
    RESOURCE_USAGE = "resource_usage"  # 资源使用量
    EXECUTION_TIME = "execution_time"  # 执行时间
    QUEUE_POSITION = "queue_position"  # 队列位置
    OPTIMAL_SLOT = "optimal_slot"    # 最优执行时间槽


@dataclass
class TaskFeatures:
    """任务特征"""
    task_id: str
    priority: int
    gpu_memory_requested: float
    cpu_cores_requested: float
    ram_requested: float
    estimated_duration: float
    wait_time: float
    queue_length_at_submit: int
    system_load_at_submit: Dict[str, float]
    task_type: str = ""
    hour_of_day: int = 0
    day_of_week: int = 0
    is_rush_hour: bool = False

    def to_record(self) -> TaskExecutionRecord:
        """转换为执行记录格式"""
        return TaskExecutionRecord(
            task_id=self.task_id,
            task_type=self.task_type,
            priority=self.priority,
            gpu_memory_requested=self.gpu_memory_requested,
            cpu_cores_requested=self.cpu_cores_requested,
            ram_requested=self.ram_requested,
            estimated_duration=self.estimated_duration,
            actual_duration=0,  # 未执行时为0
            wait_time=self.wait_time,
            queue_length_at_submit=self.queue_length_at_submit,
            system_load_at_submit=self.system_load_at_submit,
            actual_start_time=time.time(),
            actual_end_time=0,
            success=False,
        )


@dataclass
class PredictionResult:
    """预测结果"""
    prediction_type: PredictionType
    value: float
    confidence: float  # 0-1
    model_version: str
    features_used: List[str] = field(default_factory=list)


@dataclass
class SchedulingRecommendation:
    """调度建议"""
    task_id: str
    recommended_priority: float
    recommended_resources: Dict[str, float]
    estimated_start_time: float
    estimated_completion_time: float
    queue_position: int
    confidence: float
    reasons: List[str] = field(default_factory=list)


class SchedulingPredictor:
    """调度预测器 - 使用ML模型进行调度决策"""

    def __init__(self):
        self.feature_extractor = MLFeatureExtractor()
        self.model_manager = get_model_manager()
        self.model_loaded = False
        self._fallback_weights = None

    async def initialize(self):
        """初始化预测器"""
        success = await self.model_manager.load_latest_model()
        if success:
            self.model_loaded = True
            logger.info("SchedulingPredictor initialized with ML model")
        else:
            logger.warning("SchedulingPredictor initialized without ML model, using fallback")
            self._init_fallback_weights()

    def _init_fallback_weights(self):
        """初始化备用权重（当ML模型不可用时）"""
        # 基于经验的默认权重
        self._fallback_weights = np.array([
            3.0,   # 优先级
            1.5,   # GPU内存
            0.5,   # CPU核心
            0.3,   # RAM
            1.0,   # 预估时长
            1.2,   # 等待时间
            0.8,   # 队列长度
            -2.0,  # CPU负载（负）
            -2.5,  # GPU负载（负）
            -1.0,  # RAM负载（负）
            0.2,   # 小时
            0.1,   # 星期
            0.5,   # 高峰时段
        ])

    async def predict_priority(self, features: TaskFeatures) -> PredictionResult:
        """预测任务优先级分数"""
        record = features.to_record()
        X = self.feature_extractor.extract(record).reshape(1, -1)

        if self.model_loaded and self.model_manager.get_active_model():
            model = self.model_manager.get_active_model()
            loop = asyncio.get_event_loop()
            score = await loop.run_in_executor(None, lambda: model.predict(X)[0])
            confidence = 0.8  # ML模型有一定置信度
        else:
            # 使用备用计算
            score = self._fallback_predict(X)
            confidence = 0.4  # 备用模型置信度较低

        return PredictionResult(
            prediction_type=PredictionType.PRIORITY,
            value=float(score),
            confidence=confidence,
            model_version=self.model_manager.active_model_version or "fallback",
            features_used=self.feature_extractor.feature_names,
        )

    def _fallback_predict(self, X: np.ndarray) -> float:
        """备用预测（无ML模型时）"""
        if self._fallback_weights is None:
            self._init_fallback_weights()
        return float(np.dot(X, self._fallback_weights))

    async def predict_execution_time(
        self,
        features: TaskFeatures,
        current_system_load: Dict[str, float]
    ) -> PredictionResult:
        """预测任务执行时间"""
        # 基础执行时间
        base_time = features.estimated_duration

        # 根据系统负载调整
        avg_load = (
            current_system_load.get("cpu", 0) +
            current_system_load.get("gpu", 0) +
            current_system_load.get("ram", 0)
        ) / 3

        # 负载越高，预计时间越长
        load_factor = 1.0 + avg_load * 0.5

        # 考虑资源竞争
        resource_factor = 1.0
        if features.gpu_memory_requested > 16:
            resource_factor *= 1.2  # 大模型需要更多调整时间

        predicted_time = base_time * load_factor * resource_factor

        return PredictionResult(
            prediction_type=PredictionType.EXECUTION_TIME,
            value=predicted_time,
            confidence=0.7,
            model_version="heuristic",
        )

    async def predict_resource_usage(
        self,
        features: TaskFeatures
    ) -> PredictionResult:
        """预测资源使用量"""
        # 基于任务类型和参数估算
        base_gpu = features.gpu_memory_requested
        base_cpu = features.cpu_cores_requested
        base_ram = features.ram_requested

        # 根据任务类型调整系数
        type_factors = {
            "text_to_video": {"gpu": 1.5, "cpu": 1.2, "ram": 1.3},
            "image_generation": {"gpu": 1.3, "cpu": 1.0, "ram": 1.1},
            "audio_processing": {"gpu": 0.5, "cpu": 1.0, "ram": 0.8},
            "text_generation": {"gpu": 0.8, "cpu": 1.0, "ram": 0.9},
        }

        factor = type_factors.get(features.task_type, {"gpu": 1.0, "cpu": 1.0, "ram": 1.0})

        predicted_usage = {
            "gpu_memory": base_gpu * factor["gpu"],
            "cpu_cores": base_cpu * factor["cpu"],
            "ram": base_ram * factor["ram"],
        }

        return PredictionResult(
            prediction_type=PredictionType.RESOURCE_USAGE,
            value=np.mean(list(predicted_usage.values())),
            confidence=0.6,
            model_version="heuristic",
        )

    async def recommend_scheduling(
        self,
        features: TaskFeatures,
        current_system_load: Dict[str, float],
        queue_status: Dict[str, Any]
    ) -> SchedulingRecommendation:
        """生成调度建议"""
        # 获取优先级预测
        priority_result = await self.predict_priority(features)

        # 获取执行时间预测
        exec_time_result = await self.predict_execution_time(features, current_system_load)

        # 估算最优开始时间
        queue_length = queue_status.get("pending_tasks", 0)
        avg_wait_per_task = 30.0  # 假设每个任务平均等待30秒

        estimated_start = time.time() + (queue_length * avg_wait_per_task)
        estimated_completion = estimated_start + exec_time_result.value

        # 计算推荐队列位置
        if priority_result.value > 7.0:
            recommended_position = 1  # 高优先级靠前
        elif priority_result.value > 4.0:
            recommended_position = min(3, queue_length + 1)
        else:
            recommended_position = queue_length + 1

        # 生成建议原因
        reasons = []
        if features.gpu_memory_requested > 20:
            reasons.append("大GPU内存需求，建议在低负载时执行")
        if features.is_rush_hour:
            reasons.append("高峰时段，考虑延后或提升优先级")
        if priority_result.value > 6.0:
            reasons.append(f"ML预测优先级高({priority_result.value:.2f})")
        if queue_length > 20:
            reasons.append(f"当前队列较长({queue_length}个任务)，建议等待")

        return SchedulingRecommendation(
            task_id=features.task_id,
            recommended_priority=priority_result.value,
            recommended_resources={
                "gpu_memory": features.gpu_memory_requested,
                "cpu_cores": features.cpu_cores_requested,
                "ram": features.ram_requested,
            },
            estimated_start_time=estimated_start,
            estimated_completion_time=estimated_completion,
            queue_position=recommended_position,
            confidence=priority_result.confidence,
            reasons=reasons,
        )

    async def batch_predict(
        self,
        tasks_features: List[TaskFeatures]
    ) -> List[PredictionResult]:
        """批量预测"""
        results = []
        for features in tasks_features:
            result = await self.predict_priority(features)
            results.append(result)
        return results

    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if self.model_loaded and self.model_manager.get_active_model():
            model = self.model_manager.get_active_model()
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            else:
                return {name: 1.0 / len(self.feature_extractor.feature_names)
                       for name in self.feature_extractor.feature_names}
        else:
            if self._fallback_weights is None:
                self._init_fallback_weights()
            importances = np.abs(self._fallback_weights)

        importances = importances / (np.sum(importances) + 1e-6)

        return {
            name: float(imp)
            for name, imp in zip(self.feature_extractor.feature_names, importances)
        }


# 全局预测器实例
_predictor_instance: Optional[SchedulingPredictor] = None


def get_scheduling_predictor() -> SchedulingPredictor:
    """获取调度预测器单例"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = SchedulingPredictor()
    return _predictor_instance


async def initialize_predictor():
    """初始化预测器（需在启动时调用）"""
    predictor = get_scheduling_predictor()
    await predictor.initialize()
    return predictor
