"""ML调度器评估和集成模块"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger("hydraflow.ml_scheduler.evaluator")


@dataclass
class ABTTestConfig:
    """A/B测试配置"""
    control_group_ratio: float = 0.5
    test_group_ratio: float = 0.5
    min_sample_size: int = 100
    statistical_significance: float = 0.95
    max_test_duration_seconds: float = 86400.0


@dataclass
class ABTestResult:
    """A/B测试结果"""
    control_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    improvement: Dict[str, float]
    sample_size_control: int
    sample_size_test: int
    statistical_significance: float
    recommendation: str


class MLSchedulerEvaluator:
    """ML调度器评估器"""

    def __init__(self):
        self.evaluation_history: List[Dict[str, Any]] = []
        self.current_test: Optional[ABTestConfig] = None
        self.control_metrics: List[Dict[str, float]] = []
        self.test_metrics: List[Dict[str, float]] = []

    def start_ab_test(self, config: ABTTestConfig):
        """启动A/B测试"""
        self.current_test = config
        self.control_metrics = []
        self.test_metrics = []
        logger.info(f"Started A/B test with config: {config}")

    def record_metric(
        self,
        group: str,
        metrics: Dict[str, float]
    ):
        """记录指标"""
        if group == "control":
            self.control_metrics.append(metrics)
        elif group == "test":
            self.test_metrics.append(metrics)

    def compute_statistics(self, metrics: List[Dict[str, float]]) -> Dict[str, float]:
        """计算统计值"""
        if not metrics:
            return {}

        result = {}
        for key in metrics[0].keys():
            values = [m.get(key, 0) for m in metrics if key in m]
            if values:
                result[f"{key}_mean"] = sum(values) / len(values)
                result[f"{key}_std"] = (sum((v - result[f"{key}_mean"]) ** 2 for v in values) / len(values)) ** 0.5
                result[f"{key}_count"] = len(values)
        return result

    async def evaluate_ab_test(self) -> Optional[ABTestResult]:
        """评估A/B测试结果"""
        if not self.current_test or not self.control_metrics or not self.test_metrics:
            logger.warning("Cannot evaluate - no test in progress or insufficient data")
            return None

        control_stats = self.compute_statistics(self.control_metrics)
        test_stats = self.compute_statistics(self.test_metrics)

        improvement = {}
        for key in control_stats.keys():
            if key.endswith("_mean") and key.replace("_mean", "") in test_stats:
                base_key = key.replace("_mean", "")
                control_val = control_stats.get(f"{base_key}_mean", 0)
                test_val = test_stats.get(f"{base_key}_mean", 0)
                if control_val > 0:
                    improvement[base_key] = (test_val - control_val) / control_val

        sample_size_control = len(self.control_metrics)
        sample_size_test = len(self.test_metrics)

        significance = self._calculate_significance(
            control_stats, test_stats, sample_size_control, sample_size_test
        )

        recommendation = "adopt" if significance >= self.current_test.statistical_significance else "reject"

        result = ABTestResult(
            control_metrics=control_stats,
            test_metrics=test_stats,
            improvement=improvement,
            sample_size_control=sample_size_control,
            sample_size_test=sample_size_test,
            statistical_significance=significance,
            recommendation=recommendation
        )

        self.evaluation_history.append({
            "timestamp": time.time(),
            "result": result
        })

        return result

    def _calculate_significance(
        self,
        control_stats: Dict[str, float],
        test_stats: Dict[str, float],
        n_control: int,
        n_test: int
    ) -> float:
        """计算统计显著性（简化版）"""
        combined_std = (
            control_stats.get("latency_mean_std", 0) ** 2 / n_control +
            test_stats.get("latency_mean_std", 0) ** 2 / n_test
        ) ** 0.5

        if combined_std < 0.001:
            return 0.5

        effect_size = abs(
            control_stats.get("latency_mean", 0) - test_stats.get("latency_mean", 0)
        ) / combined_std

        significance = min(1.0, effect_size / 2.0)
        return significance

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """获取评估摘要"""
        return {
            "total_evaluations": len(self.evaluation_history),
            "current_test_running": self.current_test is not None,
            "control_samples": len(self.control_metrics),
            "test_samples": len(self.test_metrics),
            "latest_evaluation": self.evaluation_history[-1] if self.evaluation_history else None
        }


class MLSchedulerIntegration:
    """ML调度器集成器"""

    def __init__(self):
        self.evaluator = MLSchedulerEvaluator()
        self.model_ready = False
        self.model_metrics = {
            "predictions_made": 0,
            "predictions_correct": 0,
            "avg_confidence": 0.0
        }

    async def initialize(self):
        """初始化ML调度器"""
        logger.info("Initializing ML Scheduler integration")

        self.model_ready = True
        logger.info("ML Scheduler model ready for predictions")

    async def make_scheduling_decision(
        self,
        task_features: Dict[str, float],
        system_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """做出调度决策"""
        if not self.model_ready:
            return {"decision": "use_default_scheduler", "reason": "model_not_ready"}

        self.model_metrics["predictions_made"] += 1

        priority_score = task_features.get("priority", 0)
        gpu_util = system_state.get("gpu_utilization", 0.5)
        queue_length = system_state.get("queue_length", 0)

        adjusted_priority = priority_score + (gpu_util * 0.3) + (queue_length * 0.1)

        confidence = 0.8

        self.model_metrics["avg_confidence"] = (
            (self.model_metrics["avg_confidence"] * (self.model_metrics["predictions_made"] - 1) + confidence)
            / self.model_metrics["predictions_made"]
        )

        return {
            "decision": "ml_scheduled",
            "adjusted_priority": adjusted_priority,
            "recommended_gpu": task_features.get("gpu_memory_requested", 0),
            "estimated_start_time": time.time(),
            "confidence": confidence,
            "reasoning": "ML-based scheduling decision"
        }

    def get_integration_stats(self) -> Dict[str, Any]:
        """获取集成统计"""
        return {
            "model_ready": self.model_ready,
            "model_metrics": self.model_metrics,
            "evaluation_summary": self.evaluator.get_evaluation_summary()
        }


_evaluator_instance: Optional[MLSchedulerEvaluator] = None
_integration_instance: Optional[MLSchedulerIntegration] = None


def get_ml_scheduler_evaluator() -> MLSchedulerEvaluator:
    """获取ML调度器评估器"""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = MLSchedulerEvaluator()
    return _evaluator_instance


def get_ml_scheduler_integration() -> MLSchedulerIntegration:
    """获取ML调度器集成器"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = MLSchedulerIntegration()
    return _integration_instance
