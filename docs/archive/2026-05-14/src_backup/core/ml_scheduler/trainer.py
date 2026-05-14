"""调度模型训练器 - 从历史数据中学习最优调度策略"""

import asyncio
import logging
import time
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

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

logger = logging.getLogger("hydraflow.ml_scheduler.trainer")


@dataclass
class TaskExecutionRecord:
    """任务执行记录"""
    task_id: str
    task_type: str
    priority: int
    gpu_memory_requested: float
    cpu_cores_requested: float
    ram_requested: float
    estimated_duration: float
    actual_duration: float
    wait_time: float  # 等待时长
    queue_length_at_submit: int
    system_load_at_submit: Dict[str, float]
    actual_start_time: float
    actual_end_time: float
    success: bool
    user_id: Optional[str] = None
    project_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskExecutionRecord":
        return cls(**data)


@dataclass
class TrainingConfig:
    """训练配置"""
    model_type: str = "gradient_boosting"
    test_size: float = 0.2
    validation_size: float = 0.1
    learning_rate: float = 0.1
    max_depth: int = 6
    n_estimators: int = 100
    early_stopping_rounds: int = 10
    model_save_path: str = "models/scheduling_model"
    min_samples_leaf: int = 10


@dataclass
class TrainingResult:
    """训练结果"""
    model_path: str
    feature_importance: Dict[str, float]
    metrics: Dict[str, float]  # MAE, RMSE, accuracy等
    training_samples: int
    validation_samples: int
    training_duration: float
    timestamp: str


class MLFeatureExtractor:
    """ML特征提取器 - 从执行记录中提取特征"""

    def __init__(self):
        self.feature_names = [
            "priority",
            "gpu_memory_requested",
            "cpu_cores_requested",
            "ram_requested",
            "estimated_duration",
            "wait_time",
            "queue_length_at_submit",
            "system_load_cpu",
            "system_load_gpu",
            "system_load_ram",
            "hour_of_day",
            "day_of_week",
            "is_rush_hour",
        ]

    def extract(self, record: TaskExecutionRecord) -> np.ndarray:
        """从记录中提取特征"""
        features = [
            float(record.priority),
            record.gpu_memory_requested / 48.0,  # 归一化
            record.cpu_cores_requested / 64.0,
            record.ram_requested / 256.0,
            min(record.estimated_duration / 300.0, 1.0),  # 最大5分钟
            min(record.wait_time / 600.0, 1.0),  # 最大10分钟
            min(record.queue_length_at_submit / 100.0, 1.0),
            record.system_load_at_submit.get("cpu", 0.0),
            record.system_load_at_submit.get("gpu", 0.0),
            record.system_load_at_submit.get("ram", 0.0),
            float(datetime.fromtimestamp(record.actual_start_time).hour) / 24.0,
            float(datetime.fromtimestamp(record.actual_start_time).weekday()) / 7.0,
            1.0 if 9 <= datetime.fromtimestamp(record.actual_start_time).hour <= 18 else 0.0,
        ]
        return np.array(features, dtype=np.float32)

    def extract_batch(self, records: List[TaskExecutionRecord]) -> np.ndarray:
        """批量提取特征"""
        return np.array([self.extract(r) for r in records])


class SchedulingModelTrainer:
    """调度模型训练器"""

    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        self.feature_extractor = MLFeatureExtractor()
        self.model = None
        self.model_loaded = False

    async def train_from_history(
        self,
        historical_data: List[TaskExecutionRecord]
    ) -> TrainingResult:
        """从历史数据训练调度模型"""
        logger.info(f"Starting training with {len(historical_data)} samples")

        start_time = time.time()

        # 1. 提取特征
        X = self.feature_extractor.extract_batch(historical_data)

        # 2. 计算标签（调度质量分数：完成时间越短、等待越少、质量越高越好）
        y = self._compute_labels(historical_data)

        # 3. 划分数据集
        X_train, X_val, y_train, y_val = self._split_data(X, y)

        logger.info(f"Training: {len(X_train)}, Validation: {len(X_val)}")

        # 4. 训练模型
        self.model = await self._train_model(X_train, y_train, X_val, y_val)

        # 5. 评估模型
        metrics = self._evaluate(X_val, y_val)

        # 6. 计算特征重要性
        feature_importance = self._get_feature_importance()

        # 7. 保存模型
        model_path = await self._save_model()

        training_duration = time.time() - start_time

        result = TrainingResult(
            model_path=model_path,
            feature_importance=feature_importance,
            metrics=metrics,
            training_samples=len(X_train),
            validation_samples=len(X_val),
            training_duration=training_duration,
            timestamp=datetime.now().isoformat(),
        )

        logger.info(f"Training completed in {training_duration:.2f}s, metrics: {metrics}")

        return result

    def _compute_labels(self, records: List[TaskExecutionRecord]) -> np.ndarray:
        """计算标签：调度质量分数

        分数计算考虑：
        1. 任务是否成功完成
        2. 实际执行时间 vs 预估时间（接近1最好）
        3. 等待时间（越短越好）
        4. 系统负载状态（低负载时调度更好）
        """
        labels = []

        for record in records:
            # 基础分数：成功=1，失败=0
            base_score = 1.0 if record.success else 0.0

            # 时间效率：实际/预估，接近1表示预估准确
            time_ratio = record.actual_duration / max(record.estimated_duration, 1)
            time_score = 1.0 - min(abs(1 - time_ratio), 1.0)

            # 等待惩罚：等待时间越长，惩罚越大
            wait_score = max(0, 1.0 - record.wait_time / 600.0)  # 最多惩罚10分钟

            # 负载效率：低负载时调度更好
            avg_load = (
                record.system_load_at_submit.get("cpu", 0) +
                record.system_load_at_submit.get("gpu", 0) +
                record.system_load_at_submit.get("ram", 0)
            ) / 3
            load_score = 1.0 - avg_load

            # 综合分数
            final_score = (
                base_score * 0.4 +
                time_score * 0.3 +
                wait_score * 0.2 +
                load_score * 0.1
            )

            labels.append(final_score)

        return np.array(labels, dtype=np.float32)

    def _split_data(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """划分训练集和验证集"""
        n_samples = len(X)
        n_val = int(n_samples * self.config.validation_size)
        n_test = int(n_samples * self.config.test_size)

        indices = np.random.permutation(n_samples)

        val_indices = indices[:n_val]
        test_indices = indices[n_val:n_val + n_test]
        train_indices = indices[n_val + n_test:]

        return (
            X[train_indices],
            X[val_indices] if len(val_indices) > 0 else X[:0],
            y[train_indices],
            y[val_indices] if len(val_indices) > 0 else y[:0],
        )

    async def _train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray
    ):
        """训练模型"""
        try:
            from sklearn.ensemble import GradientBoostingRegressor
            from sklearn.multioutput import MultiOutputRegressor

            # 使用梯度提升回归器
            model = GradientBoostingRegressor(
                learning_rate=self.config.learning_rate,
                max_depth=self.config.max_depth,
                n_estimators=self.config.n_estimators,
                min_samples_leaf=self.config.min_samples_leaf,
                validation_fraction=0.1,
                n_iter_no_change=self.config.early_stopping_rounds,
                random_state=42,
            )

            # 异步训练（在线程池中执行）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: model.fit(X_train, y_train)
            )

            self.model = model
            self.model_loaded = True

            return model

        except ImportError:
            logger.warning("sklearn not available, using simple linear model")
            return await self._train_simple_model(X_train, y_train)

    async def _train_simple_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray
    ):
        """训练简单线性模型（备选）"""
        # 计算最小二乘解
        X_pinv = np.linalg.pinv(X_train.T @ X_train + 1e-6 * np.eye(X_train.shape[1]))
        weights = X_pinv @ X_train.T @ y_train

        self.model = SimpleLinearModel(weights)
        self.model_loaded = True

        return self.model

    def _evaluate(self, X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, float]:
        """评估模型"""
        if self.model is None:
            return {}

        y_pred = self.model.predict(X_val)

        # 计算各种指标
        mae = np.mean(np.abs(y_val - y_pred))
        rmse = np.sqrt(np.mean((y_val - y_pred) ** 2))
        r2 = 1 - np.sum((y_val - y_pred) ** 2) / (np.sum((y_val - np.mean(y_val)) ** 2) + 1e-6)

        # 准确率：预测值在0.1范围内
        accuracy = np.mean(np.abs(y_val - y_pred) < 0.1)

        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2),
            "accuracy_0.1": float(accuracy),
        }

    def _get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if self.model is None:
            return {}

        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
        elif hasattr(self.model, 'weights'):
            importances = np.abs(self.model.weights)
        else:
            return {name: 1.0 / len(self.feature_names) for name in self.feature_names}

        # 归一化
        importances = importances / (np.sum(importances) + 1e-6)

        return {
            name: float(imp)
            for name, imp in zip(self.feature_extractor.feature_names, importances)
        }

    async def _save_model(self) -> str:
        """保存模型"""
        import pickle

        save_dir = Path(self.config.model_save_path)
        save_dir.mkdir(parents=True, exist_ok=True)

        model_file = save_dir / "scheduling_model.pkl"
        config_file = save_dir / "config.json"
        features_file = save_dir / "feature_names.json"

        # 保存模型
        with open(model_file, 'wb') as f:
            pickle.dump(self.model, f)

        # 保存配置
        with open(config_file, 'w') as f:
            json.dump({
                "model_type": self.config.model_type,
                "feature_names": self.feature_extractor.feature_names,
            }, f, indent=2)

        # 保存特征名
        with open(features_file, 'w') as f:
            json.dump(self.feature_extractor.feature_names, f, indent=2)

        logger.info(f"Model saved to {model_file}")

        return str(model_file)

    async def load_model(self, model_path: str):
        """加载已有模型"""
        import pickle

        model_file = Path(model_path) / "scheduling_model.pkl"

        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")

        with open(model_file, 'rb') as f:
            self.model = pickle.load(f)

        self.model_loaded = True
        logger.info(f"Model loaded from {model_file}")


class SimpleLinearModel:
    """简单线性模型（无sklearn时的备选）"""

    def __init__(self, weights: np.ndarray):
        self.weights = weights

    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        return X @ self.weights


class ModelManager:
    """模型管理器 - 管理多个版本的调度模型"""

    def __init__(self, model_dir: str = "models/scheduling_model"):
        self.model_dir = Path(model_dir)
        self.models: Dict[str, Any] = {}
        self.active_model_version: Optional[str] = None

    async def load_latest_model(self) -> bool:
        """加载最新模型"""
        if not self.model_dir.exists():
            logger.warning(f"Model directory not found: {self.model_dir}")
            return False

        # 查找所有模型版本
        model_files = list(self.model_dir.glob("*/scheduling_model.pkl"))

        if not model_files:
            logger.warning("No models found")
            return False

        # 按修改时间排序
        latest = max(model_files, key=lambda p: p.stat().st_mtime)

        trainer = SchedulingModelTrainer()
        await trainer.load_model(str(latest.parent))

        self.models["latest"] = trainer.model
        self.active_model_version = "latest"

        logger.info(f"Loaded latest model from {latest.parent}")
        return True

    def get_active_model(self):
        """获取当前活跃模型"""
        if self.active_model_version and self.active_model_version in self.models:
            return self.models[self.active_model_version]
        return None


# 全局模型管理器
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """获取模型管理器单例"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
