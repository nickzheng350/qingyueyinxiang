"""统一智能引擎 - 多模块多引擎整合，唯一入口，智能调度"""
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union, Callable, TypeVar
from enum import Enum
from abc import ABC, abstractmethod
import uuid

from src.model_dispatcher.type_system import (
    ModelFunctionType,
    get_consistency_validator,
    TouchPoint,
)
from src.multimodal.audio_prompt_engine import AudioPromptEngine
from src.multimodal.enhanced_audio_engine import EnhancedAudioEngine
from src.multimodal.av_multimodal_fusion import AVMultimodalFusionEngine
from src.multimodal.workflow_integration import UnifiedProjectManager
from src.cache.priority_queue import MultiLevelCache
from src.core.concurrency import UnifiedExecutor

logger = logging.getLogger("hydraflow.core.unified_engine")

T = TypeVar('T')


class EngineMode(str, Enum):
    """引擎模式"""
    EFFICIENCY = "efficiency"      # 效率优先
    QUALITY = "quality"            # 质量优先
    BALANCED = "balanced"          # 平衡
    ECO = "eco"                    # 节能模式


class TaskPriority(int, Enum):
    """任务优先级"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ResourceProfile:
    """资源配置文件"""
    cpu_cores: int = 4
    gpu_memory_gb: float = 8.0
    ram_gb: float = 16.0
    storage_gb: float = 100.0
    max_concurrent_tasks: int = 5
    max_cache_gb: float = 4.0


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_completion_time: float = 0.0
    cache_hit_rate: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    cost_savings: float = 0.0


@dataclass
class PromptComponent:
    """提示词组件"""
    component_type: str
    content: str
    weight: float = 1.0
    required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiModalPrompt:
    """多元化提示词结构"""
    prompt_id: str
    primary: str
    components: List[PromptComponent] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    style_hints: Dict[str, Any] = field(default_factory=dict)
    quality_requirements: Dict[str, Any] = field(default_factory=dict)
    
    def add_component(self, component: PromptComponent):
        """添加提示词组件"""
        self.components.append(component)
    
    def get_weighted_content(self) -> str:
        """获取加权内容"""
        weighted = [self.primary]
        for comp in self.components:
            if comp.weight > 0:
                weighted.append(comp.content)
        return " ".join(weighted)


@dataclass
class Task:
    """任务"""
    task_id: str
    task_type: ModelFunctionType
    prompt: MultiModalPrompt
    priority: TaskPriority = TaskPriority.MEDIUM
    mode: EngineMode = EngineMode.BALANCED
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineResult:
    """引擎结果"""
    success: bool
    task_id: Optional[str] = None
    output: Optional[Any] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class BaseSubEngine(ABC):
    """基础子引擎"""
    
    @abstractmethod
    def get_supported_types(self) -> List[ModelFunctionType]:
        """获取支持的类型"""
        pass
    
    @abstractmethod
    def execute(self, task: Task) -> EngineResult:
        """执行任务"""
        pass
    
    @abstractmethod
    def estimate_cost(self, task: Task) -> float:
        """估算成本"""
        pass


class AudioSubEngine(BaseSubEngine):
    """音频子引擎"""
    
    def __init__(self):
        self.enhanced_audio = EnhancedAudioEngine()
        self.audio_prompt = AudioPromptEngine()
    
    def get_supported_types(self) -> List[ModelFunctionType]:
        return [
            ModelFunctionType.TEXT_TO_AUDIO,
            ModelFunctionType.SCRIPT_TO_AUDIO,
            ModelFunctionType.CHARACTER_VOICEOVER,
            ModelFunctionType.DUBBING,
            ModelFunctionType.FOLEY,
            ModelFunctionType.BACKGROUND_MUSIC,
            ModelFunctionType.SOUND_DESIGN,
            ModelFunctionType.AUDIO_STYLE_TRANSFER,
        ]
    
    def execute(self, task: Task) -> EngineResult:
        try:
            logger.info(f"AudioEngine executing {task.task_id}")
            
            result = EngineResult(
                success=True,
                task_id=task.task_id,
                output={"mode": task.mode.value}
            )
            
            return result
        except Exception as e:
            return EngineResult(
                success=False,
                task_id=task.task_id,
                errors=[str(e)]
            )
    
    def estimate_cost(self, task: Task) -> float:
        base_cost = 1.0
        if task.mode == EngineMode.QUALITY:
            return base_cost * 2.0
        elif task.mode == EngineMode.ECO:
            return base_cost * 0.5
        return base_cost


class VideoSubEngine(BaseSubEngine):
    """视频子引擎"""
    
    def __init__(self):
        self.fusion_engine = AVMultimodalFusionEngine()
    
    def get_supported_types(self) -> List[ModelFunctionType]:
        return [
            ModelFunctionType.TEXT_TO_VIDEO,
            ModelFunctionType.IMAGE_TO_VIDEO,
            ModelFunctionType.AUDIO_TO_VIDEO,
            ModelFunctionType.SCENE_GENERATION,
            ModelFunctionType.VIDEO_STYLE_TRANSFER,
            ModelFunctionType.VIDEO_FORMAT_CONVERT,
        ]
    
    def execute(self, task: Task) -> EngineResult:
        try:
            logger.info(f"VideoEngine executing {task.task_id}")
            return EngineResult(
                success=True,
                task_id=task.task_id,
                output={"processed": True}
            )
        except Exception as e:
            return EngineResult(
                success=False,
                task_id=task.task_id,
                errors=[str(e)]
            )
    
    def estimate_cost(self, task: Task) -> float:
        base_cost = 2.0
        if task.mode == EngineMode.QUALITY:
            return base_cost * 2.5
        elif task.mode == EngineMode.ECO:
            return base_cost * 0.6
        return base_cost


class VisualSubEngine(BaseSubEngine):
    """视觉子引擎"""
    
    def get_supported_types(self) -> List[ModelFunctionType]:
        return [
            ModelFunctionType.TEXT_TO_IMAGE,
            ModelFunctionType.IMAGE_EDIT,
            ModelFunctionType.IMAGE_UPSCALE,
            ModelFunctionType.IMAGE_STYLE_TRANSFER,
            ModelFunctionType.IMAGE_FORMAT_CONVERT,
        ]
    
    def execute(self, task: Task) -> EngineResult:
        try:
            logger.info(f"VisualEngine executing {task.task_id}")
            return EngineResult(
                success=True,
                task_id=task.task_id,
                output={"visual_result": "generated"}
            )
        except Exception as e:
            return EngineResult(
                success=False,
                task_id=task.task_id,
                errors=[str(e)]
            )
    
    def estimate_cost(self, task: Task) -> float:
        base_cost = 1.5
        if task.mode == EngineMode.QUALITY:
            return base_cost * 2.0
        elif task.mode == EngineMode.ECO:
            return base_cost * 0.7
        return base_cost


class TextSubEngine(BaseSubEngine):
    """文本子引擎"""
    
    def get_supported_types(self) -> List[ModelFunctionType]:
        return [
            ModelFunctionType.TEXT_GENERATION,
            ModelFunctionType.CODE_GENERATION,
            ModelFunctionType.AUDIO_TO_TEXT,
            ModelFunctionType.VIDEO_TO_TEXT,
            ModelFunctionType.IMAGE_TO_TEXT,
        ]
    
    def execute(self, task: Task) -> EngineResult:
        try:
            logger.info(f"TextEngine executing {task.task_id}")
            return EngineResult(
                success=True,
                task_id=task.task_id,
                output={"text_result": task.prompt.primary}
            )
        except Exception as e:
            return EngineResult(
                success=False,
                task_id=task.task_id,
                errors=[str(e)]
            )
    
    def estimate_cost(self, task: Task) -> float:
        base_cost = 0.5
        if task.mode == EngineMode.QUALITY:
            return base_cost * 1.5
        elif task.mode == EngineMode.ECO:
            return base_cost * 0.3
        return base_cost


class FusionSubEngine(BaseSubEngine):
    """融合子引擎"""
    
    def __init__(self):
        self.fusion_engine = AVMultimodalFusionEngine()
    
    def get_supported_types(self) -> List[ModelFunctionType]:
        return [
            ModelFunctionType.AV_FUSION,
        ]
    
    def execute(self, task: Task) -> EngineResult:
        try:
            logger.info(f"FusionEngine executing {task.task_id}")
            return EngineResult(
                success=True,
                task_id=task.task_id,
                output={"fused": True}
            )
        except Exception as e:
            return EngineResult(
                success=False,
                task_id=task.task_id,
                errors=[str(e)]
            )
    
    def estimate_cost(self, task: Task) -> float:
        base_cost = 3.0
        if task.mode == EngineMode.QUALITY:
            return base_cost * 3.0
        elif task.mode == EngineMode.ECO:
            return base_cost * 0.8
        return base_cost


class SmartScheduler:
    """智能调度器"""
    
    def __init__(self):
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.lock = threading.RLock()
    
    def add_task(self, task: Task):
        """添加任务"""
        with self.lock:
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: t.priority.value)
            task.status = TaskStatus.QUEUED
            logger.info(f"Task {task.task_id} queued at priority {task.priority}")
    
    def get_next_task(self, max_concurrent: int) -> Optional[Task]:
        """获取下一个任务"""
        with self.lock:
            if len(self.active_tasks) >= max_concurrent:
                return None
            
            for task in self.task_queue:
                if task.status == TaskStatus.QUEUED:
                    if all(dep not in self.active_tasks for dep in task.dependencies):
                        self.task_queue.remove(task)
                        self.active_tasks[task.task_id] = task
                        task.status = TaskStatus.RUNNING
                        return task
            return None
    
    def complete_task(self, task_id: str, result: EngineResult):
        """完成任务"""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks.pop(task_id)
                if result.success:
                    task.status = TaskStatus.COMPLETED
                    task.result = result.output
                else:
                    task.status = TaskStatus.FAILED
                    task.error = "; ".join(result.errors)
                task.completed_at = time.time()
                logger.info(f"Task {task_id} {task.status}")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        with self.lock:
            return {
                "queued": len(self.task_queue),
                "active": len(self.active_tasks),
            }


class ResourceOptimizer:
    """资源优化器"""
    
    def __init__(self, profile: ResourceProfile):
        self.profile = profile
        self.current_load: Dict[str, float] = {
            "cpu": 0.0,
            "gpu": 0.0,
            "ram": 0.0,
        }
        self.lock = threading.RLock()
    
    def can_accept_task(self, estimated_cost: float) -> bool:
        """检查是否可以接受任务"""
        with self.lock:
            max_cpu = self.profile.cpu_cores
            max_gpu = self.profile.gpu_memory_gb
            max_ram = self.profile.ram_gb
            
            cpu_available = (max_cpu * (1 - self.current_load["cpu"])) > estimated_cost * 0.1
            ram_available = (max_ram * (1 - self.current_load["ram"])) > estimated_cost * 0.5
            
            return cpu_available and ram_available
    
    def allocate_resources(self, task: Task, estimated_cost: float):
        """分配资源"""
        with self.lock:
            cost_factor = estimated_cost / 10.0
            self.current_load["cpu"] = min(1.0, self.current_load["cpu"] + cost_factor * 0.3)
            self.current_load["ram"] = min(1.0, self.current_load["ram"] + cost_factor * 0.5)
            self.current_load["gpu"] = min(1.0, self.current_load["gpu"] + cost_factor * 0.2)
    
    def release_resources(self, task: Task, estimated_cost: float):
        """释放资源"""
        with self.lock:
            cost_factor = estimated_cost / 10.0
            self.current_load["cpu"] = max(0.0, self.current_load["cpu"] - cost_factor * 0.3)
            self.current_load["ram"] = max(0.0, self.current_load["ram"] - cost_factor * 0.5)
            self.current_load["gpu"] = max(0.0, self.current_load["gpu"] - cost_factor * 0.2)
    
    def get_current_utilization(self) -> Dict[str, float]:
        """获取当前利用率"""
        with self.lock:
            return self.current_load.copy()


class UnifiedIntelligentEngine:
    """统一智能引擎 - 唯一入口"""
    
    _instance: Optional["UnifiedIntelligentEngine"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "UnifiedIntelligentEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.validator = get_consistency_validator()
        self.cache = MultiLevelCache(l1_max_size=1000, l2_max_size=10000)
        self.executor = UnifiedExecutor()
        
        self.resource_profile = ResourceProfile()
        self.resource_optimizer = ResourceOptimizer(self.resource_profile)
        self.scheduler = SmartScheduler()
        self.metrics = PerformanceMetrics()
        
        self.sub_engines: Dict[str, BaseSubEngine] = {
            "audio": AudioSubEngine(),
            "video": VideoSubEngine(),
            "visual": VisualSubEngine(),
            "text": TextSubEngine(),
            "fusion": FusionSubEngine(),
        }
        
        self.type_to_engine: Dict[ModelFunctionType, str] = self._build_type_mapping()
        
        self.running = False
        self.work_thread: Optional[threading.Thread] = None
        
        logger.info("UnifiedIntelligentEngine initialized")
    
    def _build_type_mapping(self) -> Dict[ModelFunctionType, str]:
        """构建类型到引擎的映射"""
        mapping = {}
        for engine_name, engine in self.sub_engines.items():
            for func_type in engine.get_supported_types():
                mapping[func_type] = engine_name
        return mapping
    
    def get_engine_for_type(self, task_type: ModelFunctionType) -> Optional[BaseSubEngine]:
        """获取对应类型的引擎"""
        engine_name = self.type_to_engine.get(task_type)
        return self.sub_engines.get(engine_name)
    
    def create_prompt(
        self,
        primary: str,
        **kwargs
    ) -> MultiModalPrompt:
        """创建多元化提示词"""
        return MultiModalPrompt(
            prompt_id=str(uuid.uuid4()),
            primary=primary,
            **kwargs
        )
    
    def submit_task(
        self,
        task_type: ModelFunctionType,
        prompt: Union[str, MultiModalPrompt],
        priority: TaskPriority = TaskPriority.MEDIUM,
        mode: EngineMode = EngineMode.BALANCED,
        dependencies: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """提交任务"""
        if isinstance(prompt, str):
            prompt = self.create_prompt(primary=prompt)
        
        task = Task(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            prompt=prompt,
            priority=priority,
            mode=mode,
            dependencies=dependencies or [],
            metadata=kwargs
        )
        
        validation_data = {
            "type": task_type.value,
            "priority": priority.value,
            "mode": mode.value,
        }
        
        self.validator.validate(
            task_type,
            validation_data,
            TouchPoint.PRE_PROCESSING
        )
        
        self.scheduler.add_task(task)
        self.metrics.total_tasks += 1
        
        if not self.running:
            self.start()
        
        return task.task_id
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        for task in self.scheduler.task_queue:
            if task.task_id == task_id:
                return task.status
        if task_id in self.scheduler.active_tasks:
            return self.scheduler.active_tasks[task_id].status
        return None
    
    def get_task_result(self, task_id: str) -> Optional[EngineResult]:
        """获取任务结果"""
        cached = self.cache.get(task_id)
        if cached:
            return cached
        
        for task in self.scheduler.task_queue:
            if task.task_id == task_id and task.result:
                result = EngineResult(
                    success=True,
                    task_id=task_id,
                    output=task.result
                )
                self.cache.put(task_id, result)
                return result
        return None
    
    def _process_task(self, task: Task):
        """处理任务"""
        engine = self.get_engine_for_type(task.task_type)
        if not engine:
            result = EngineResult(
                success=False,
                task_id=task.task_id,
                errors=[f"No engine for type {task.task_type}"]
            )
            self.scheduler.complete_task(task.task_id, result)
            return
        
        estimated_cost = engine.estimate_cost(task)
        
        if not self.resource_optimizer.can_accept_task(estimated_cost):
            result = EngineResult(
                success=False,
                task_id=task.task_id,
                errors=["Resources unavailable"]
            )
            self.scheduler.complete_task(task.task_id, result)
            return
        
        self.resource_optimizer.allocate_resources(task, estimated_cost)
        
        try:
            task.started_at = time.time()
            result = engine.execute(task)
            
            if result.success:
                self.metrics.completed_tasks += 1
            else:
                self.metrics.failed_tasks += 1
            
            self.cache.put(task.task_id, result)
            self.scheduler.complete_task(task.task_id, result)
        finally:
            self.resource_optimizer.release_resources(task, estimated_cost)
    
    def _work_loop(self):
        """工作循环"""
        while self.running:
            task = self.scheduler.get_next_task(self.resource_profile.max_concurrent_tasks)
            
            if task:
                self._process_task(task)
            else:
                time.sleep(0.1)
    
    def start(self):
        """启动引擎"""
        if self.running:
            return
        
        self.running = True
        self.work_thread = threading.Thread(target=self._work_loop, daemon=True)
        self.work_thread.start()
        logger.info("UnifiedIntelligentEngine started")
    
    def stop(self):
        """停止引擎"""
        self.running = False
        if self.work_thread:
            self.work_thread.join(timeout=5.0)
        logger.info("UnifiedIntelligentEngine stopped")
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """获取性能指标"""
        self.metrics.resource_utilization = self.resource_optimizer.get_current_utilization()
        self.metrics.cache_hit_rate = (
            (self.cache._hits["l1"] + self.cache._hits["l2"]) / max(1, self.cache._hits["total"])
            if self.cache._hits["total"] > 0 else 0
        )
        return self.metrics
    
    def set_engine_mode(self, mode: EngineMode):
        """设置引擎模式"""
        self.resource_profile.max_concurrent_tasks = {
            EngineMode.EFFICIENCY: 8,
            EngineMode.QUALITY: 2,
            EngineMode.BALANCED: 5,
            EngineMode.ECO: 3,
        }.get(mode, 5)
        logger.info(f"Engine mode set to {mode}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "running": self.running,
            "scheduler": self.scheduler.get_queue_stats(),
            "metrics": self.get_performance_metrics(),
            "resource_utilization": self.resource_optimizer.get_current_utilization(),
        }


def get_unified_engine() -> UnifiedIntelligentEngine:
    """获取统一智能引擎单例"""
    return UnifiedIntelligentEngine()
