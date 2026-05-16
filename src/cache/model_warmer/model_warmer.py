"""模型预热系统 - 启动时预加载常用模型，减少首次请求延迟"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import threading

logger = logging.getLogger("hydraflow.model_warmer")


class WarmUpStrategy(Enum):
    """预热策略"""
    EAGER = "eager"           # 立即预热所有模型
    LAZY = "lazy"            # 按需预热
    PREDICTIVE = "predictive" # 基于历史预测预热
    ADAPTIVE = "adaptive"     # 自适应预热


class ModelStatus(Enum):
    """模型状态"""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    READY = "ready"
    FAILED = "failed"
    UNLOADED = "unloaded"  # 被卸载以释放资源


@dataclass
class ModelInfo:
    """模型信息"""
    model_id: str
    model_type: str
    model_path: str
    memory_required_gb: float
    load_priority: int = 0
    expected_load_time: float = 10.0
    usage_count: int = 0
    last_used_at: Optional[float] = None
    status: ModelStatus = ModelStatus.NOT_LOADED


@dataclass
class WarmUpTask:
    """预热任务"""
    model_id: str
    priority: int
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    success: bool = False


class ModelWarmer:
    """模型预热管理器"""

    def __init__(
        self,
        strategy: WarmUpStrategy = WarmUpStrategy.PREDICTIVE,
        max_concurrent_loads: int = 2,
        max_memory_gb: float = 40.0
    ):
        self.strategy = strategy
        self.max_concurrent_loads = max_concurrent_loads
        self.max_memory_gb = max_memory_gb

        self.models: Dict[str, ModelInfo] = {}
        self.warmup_queue: List[WarmUpTask] = []
        self.active_loads: Dict[str, WarmUpTask] = {}

        self.current_memory_usage_gb = 0.0
        self.warmup_stats = {
            "total_warmups": 0,
            "successful_warmups": 0,
            "failed_warmups": 0,
            "avg_warmup_time": 0.0,
        }

        self._lock = threading.RLock()
        self._warmup_in_progress = False
        self._load_func: Optional[Callable] = None
        self._unload_func: Optional[Callable] = None

        logger.info(f"ModelWarmer initialized with strategy={strategy.value}")

    def register_model(
        self,
        model_id: str,
        model_type: str,
        model_path: str,
        memory_required_gb: float,
        load_priority: int = 0
    ):
        """注册模型"""
        with self._lock:
            self.models[model_id] = ModelInfo(
                model_id=model_id,
                model_type=model_type,
                model_path=model_path,
                memory_required_gb=memory_required_gb,
                load_priority=load_priority,
            )
            logger.debug(f"Registered model: {model_id} ({memory_required_gb}GB)")

    def set_load_function(self, load_func: Callable):
        """设置模型加载函数"""
        self._load_func = load_func

    def set_unload_function(self, unload_func: Callable):
        """设置模型卸载函数"""
        self._unload_func = unload_func

    async def warmup(self, model_ids: List[str] = None):
        """执行预热"""
        if self._warmup_in_progress:
            logger.warning("Warmup already in progress")
            return

        self._warmup_in_progress = True

        try:
            if self.strategy == WarmUpStrategy.EAGER:
                await self._eager_warmup(model_ids)
            elif self.strategy == WarmUpStrategy.LAZY:
                await self._lazy_warmup(model_ids)
            elif self.strategy == WarmUpStrategy.PREDICTIVE:
                await self._predictive_warmup(model_ids)
            elif self.strategy == WarmUpStrategy.ADAPTIVE:
                await self._adaptive_warmup(model_ids)
        finally:
            self._warmup_in_progress = False

    async def _eager_warmup(self, model_ids: List[str] = None):
        """立即预热所有模型"""
        models_to_warmup = self._get_models_to_warmup(model_ids)

        # 按优先级排序
        models_to_warmup.sort(key=lambda m: m.load_priority, reverse=True)

        for model in models_to_warmup:
            await self._load_model(model.model_id)

    async def _lazy_warmup(self, model_ids: List[str] = None):
        """按需预热 - 只预热明确指定的模型"""
        if model_ids:
            for model_id in model_ids:
                await self._load_model(model_id)
        else:
            logger.info("Lazy warmup: no models specified")

    async def _predictive_warmup(self, model_ids: List[str] = None):
        """基于预测的预热 - 根据历史使用数据预测"""
        # 获取需要预热的模型
        models_to_warmup = self._get_models_to_warmup(model_ids)

        # 按使用频率和优先级排序
        def predict_score(model: ModelInfo) -> float:
            recent_usage = model.usage_count
            priority_factor = model.load_priority * 0.1
            memory_factor = (self.max_memory_gb - model.memory_required_gb) / self.max_memory_gb
            return recent_usage + priority_factor + memory_factor

        models_to_warmup.sort(key=predict_score, reverse=True)

        # 在内存限制内预热
        for model in models_to_warmup:
            if self.current_memory_usage_gb + model.memory_required_gb <= self.max_memory_gb:
                await self._load_model(model.model_id)
            else:
                logger.info(f"Memory limit reached, skipping {model.model_id}")

    async def _adaptive_warmup(self, model_ids: List[str] = None):
        """自适应预热 - 根据系统负载动态调整"""
        # 获取系统负载（简化版）
        import psutil
        system_memory_available = psutil.virtual_memory().available / (1024**3)

        # 如果系统内存充足，预热更多模型
        if system_memory_available > self.max_memory_gb * 1.5:
            await self._predictive_warmup(model_ids)
        elif system_memory_available > self.max_memory_gb:
            # 只预热高优先级模型
            high_priority_models = [
                m for m in self._get_models_to_warmup(model_ids)
                if m.load_priority >= 5
            ]
            for model in high_priority_models:
                await self._load_model(model.model_id)
        else:
            logger.warning("Low system memory, skipping warmup")

    def _get_models_to_warmup(self, model_ids: List[str] = None) -> List[ModelInfo]:
        """获取待预热模型列表"""
        if model_ids:
            return [self.models[mid] for mid in model_ids if mid in self.models]
        else:
            return [m for m in self.models.values() if m.status == ModelStatus.NOT_LOADED]

    async def _load_model(self, model_id: str):
        """加载单个模型"""
        if model_id not in self.models:
            logger.error(f"Model not registered: {model_id}")
            return False

        model = self.models[model_id]

        if model.status == ModelStatus.READY:
            logger.debug(f"Model already loaded: {model_id}")
            return True

        if model.status == ModelStatus.LOADING:
            logger.debug(f"Model already loading: {model_id}")
            return False

        # 检查内存
        if self.current_memory_usage_gb + model.memory_required_gb > self.max_memory_gb:
            # 尝试卸载低优先级模型
            await self._unload_low_priority_models(model.memory_required_gb)

            if self.current_memory_usage_gb + model.memory_required_gb > self.max_memory_gb:
                logger.warning(f"Insufficient memory for model {model_id}")
                return False

        model.status = ModelStatus.LOADING
        task = WarmUpTask(model_id=model_id, priority=model.load_priority)
        task.started_at = time.time()

        self.active_loads[model_id] = task
        self.warmup_stats["total_warmups"] += 1

        try:
            if self._load_func:
                await self._load_func(model.model_id)
            else:
                await self._default_load(model)

            model.status = ModelStatus.READY
            task.success = True
            task.completed_at = time.time()

            self.current_memory_usage_gb += model.memory_required_gb
            model.usage_count += 1
            model.last_used_at = time.time()

            self.warmup_stats["successful_warmups"] += 1

            elapsed = task.completed_at - task.started_at
            self.warmup_stats["avg_warmup_time"] = (
                (self.warmup_stats["avg_warmup_time"] * (self.warmup_stats["successful_warmups"] - 1) + elapsed)
                / self.warmup_stats["successful_warmups"]
            )

            logger.info(f"Model warmed up: {model_id} ({elapsed:.2f}s)")

        except Exception as e:
            model.status = ModelStatus.FAILED
            task.completed_at = time.time()
            self.warmup_stats["failed_warmups"] += 1
            logger.error(f"Model warmup failed: {model_id}, error: {e}")

        finally:
            if model_id in self.active_loads:
                del self.active_loads[model_id]

        return task.success

    async def _default_load(self, model: ModelInfo):
        """默认加载实现（模拟）"""
        await asyncio.sleep(min(model.expected_load_time, 5.0))

    async def _unload_low_priority_models(self, required_memory_gb: float):
        """卸载低优先级模型以释放内存"""
        candidates = [
            m for m in self.models.values()
            if m.status == ModelStatus.READY and m.load_priority < 5
        ]
        candidates.sort(key=lambda m: (m.load_priority, m.last_used_at or 0))

        freed_memory = 0.0
        for model in candidates:
            if freed_memory >= required_memory_gb:
                break
            await self._unload_model(model.model_id)
            freed_memory += model.memory_required_gb

    async def _unload_model(self, model_id: str):
        """卸载模型"""
        if model_id not in self.models:
            return

        model = self.models[model_id]

        if model.status != ModelStatus.READY:
            return

        try:
            if self._unload_func:
                await self._unload_func(model_id)
            else:
                await self._default_unload(model)

            model.status = ModelStatus.UNLOADED
            self.current_memory_usage_gb -= model.memory_required_gb

            logger.info(f"Model unloaded: {model_id}")

        except Exception as e:
            logger.error(f"Model unload failed: {model_id}, error: {e}")

    async def _default_unload(self, model: ModelInfo):
        """默认卸载实现（模拟）"""
        await asyncio.sleep(0.5)

    async def preload_before_task(self, task_type: str, task_params: Dict[str, Any]):
        """任务执行前预加载所需模型"""
        required_models = self._predict_required_models(task_type, task_params)

        for model_id in required_models:
            if model_id in self.models:
                model = self.models[model_id]
                if model.status != ModelStatus.READY:
                    asyncio.create_task(self._load_model(model_id))

    def _predict_required_models(self, task_type: str, task_params: Dict[str, Any]) -> List[str]:
        """预测任务需要的模型"""
        task_to_models = {
            "text_to_image": ["sd_model", "vae_model"],
            "image_edit": ["sd_model", "inpaint_model"],
            "text_to_video": ["video_model", "sd_model"],
            "audio_generation": ["tts_model", "audio_codec"],
        }
        return task_to_models.get(task_type, [])

    def record_usage(self, model_id: str):
        """记录模型使用"""
        if model_id in self.models:
            self.models[model_id].usage_count += 1
            self.models[model_id].last_used_at = time.time()

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "strategy": self.strategy.value,
            "registered_models": len(self.models),
            "ready_models": sum(1 for m in self.models.values() if m.status == ModelStatus.READY),
            "loading_models": sum(1 for m in self.models.values() if m.status == ModelStatus.LOADING),
            "current_memory_gb": self.current_memory_usage_gb,
            "max_memory_gb": self.max_memory_gb,
            "warmup_stats": self.warmup_stats.copy(),
            "active_loads": list(self.active_loads.keys()),
        }


_model_warmer_instance: Optional[ModelWarmer] = None


def get_model_warmer() -> ModelWarmer:
    """获取模型预热器单例"""
    global _model_warmer_instance
    if _model_warmer_instance is None:
        _model_warmer_instance = ModelWarmer()
    return _model_warmer_instance
