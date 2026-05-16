"""多模态资源池化引擎 - 统一管理GPU/计算资源，降低成本，提升利用率"""

import asyncio
import logging
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, Tuple, Union
from abc import ABC, abstractmethod
from collections import defaultdict

logger = logging.getLogger("hydraflow.multimodal.resource_pool")


class ResourceType(str, Enum):
    """资源类型"""
    GPU = "gpu"
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    STORAGE = "storage"


class ResourceStatus(str, Enum):
    """资源状态"""
    IDLE = "idle"
    BUSY = "busy"
    RESERVED = "reserved"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class TaskPriority(str, Enum):
    """任务优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


@dataclass
class ResourceDescriptor:
    """资源描述符"""
    resource_id: str
    resource_type: ResourceType
    status: ResourceStatus = ResourceStatus.IDLE
    capacity: float = 0.0  # 总容量（GPU为显存GB，CPU为核心数，内存为GB）
    used: float = 0.0  # 当前使用量
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_used: float = 0.0
    usage_count: int = 0


@dataclass
class ResourceAllocation:
    """资源分配结果"""
    success: bool
    resource_id: Optional[str] = None
    allocated_capacity: float = 0.0
    timeout: float = 0.0
    error_message: Optional[str] = None


@dataclass
class PoolStatistics:
    """资源池统计"""
    total_resources: int = 0
    idle_resources: int = 0
    busy_resources: int = 0
    average_utilization: float = 0.0
    total_capacity: float = 0.0
    used_capacity: float = 0.0
    pending_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0


@dataclass
class TaskRequest:
    """任务资源请求"""
    task_id: str
    task_type: str
    priority: TaskPriority = TaskPriority.MEDIUM
    required_gpu_memory: float = 0.0  # GB
    required_cpu_cores: int = 1
    required_memory: float = 0.0  # GB
    timeout: float = 300.0  # 秒
    dependencies: List[str] = field(default_factory=list)
    callback: Optional[Callable[[ResourceAllocation], None]] = None


class BaseResourcePool(ABC):
    """资源池抽象基类"""

    @abstractmethod
    async def acquire(self, request: TaskRequest) -> ResourceAllocation:
        """获取资源"""
        pass

    @abstractmethod
    async def release(self, resource_id: str) -> None:
        """释放资源"""
        pass

    @abstractmethod
    def get_statistics(self) -> PoolStatistics:
        """获取统计信息"""
        pass

    @abstractmethod
    def get_resource_status(self, resource_id: str) -> Optional[ResourceDescriptor]:
        """获取资源状态"""
        pass


class GPUResourcePool(BaseResourcePool):
    """GPU资源池"""

    def __init__(self):
        self._resources: Dict[str, ResourceDescriptor] = {}
        self._pending_tasks: List[TaskRequest] = []
        self._lock = asyncio.Lock()
        self._completed_tasks = 0
        self._failed_tasks = 0
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_running = False
        self._load_resources()

    def _load_resources(self):
        """加载系统GPU资源"""
        try:
            import torch
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    device = torch.device(f"cuda:{i}")
                    props = torch.cuda.get_device_properties(device)
                    self._resources[f"gpu_{i}"] = ResourceDescriptor(
                        resource_id=f"gpu_{i}",
                        resource_type=ResourceType.GPU,
                        status=ResourceStatus.IDLE,
                        capacity=props.total_memory / (1024 ** 3),  # 转换为GB
                        metadata={
                            "name": props.name,
                            "compute_capability": f"{props.major}.{props.minor}",
                            "multi_processor_count": props.multi_processor_count,
                            "max_threads_per_multi_processor": props.max_threads_per_multi_processor,
                        }
                    )
                logger.info(f"Loaded {len(self._resources)} GPU(s)")
            else:
                logger.warning("No GPU available, creating simulated resources")
                # 创建模拟资源用于开发测试
                self._resources["gpu_sim_0"] = ResourceDescriptor(
                    resource_id="gpu_sim_0",
                    resource_type=ResourceType.GPU,
                    status=ResourceStatus.IDLE,
                    capacity=24.0,
                    metadata={"name": "Simulated GPU", "type": "simulation"}
                )
        except ImportError:
            logger.warning("PyTorch not available, creating simulated GPU resources")
            self._resources["gpu_sim_0"] = ResourceDescriptor(
                resource_id="gpu_sim_0",
                resource_type=ResourceType.GPU,
                status=ResourceStatus.IDLE,
                capacity=24.0,
                metadata={"name": "Simulated GPU", "type": "simulation"}
            )

    async def _find_available_resource(self, required_memory: float) -> Optional[str]:
        """查找可用资源"""
        async with self._lock:
            # 优先查找完全空闲且容量足够的资源
            for rid, resource in self._resources.items():
                if (resource.status == ResourceStatus.IDLE and 
                    resource.capacity >= required_memory):
                    return rid
            
            # 查找部分空闲但剩余容量足够的资源
            for rid, resource in self._resources.items():
                if (resource.status == ResourceStatus.BUSY and 
                    resource.capacity - resource.used >= required_memory):
                    return rid
            
            return None

    async def _allocate_resource(self, resource_id: str, request: TaskRequest) -> ResourceAllocation:
        """分配资源"""
        async with self._lock:
            resource = self._resources.get(resource_id)
            if not resource:
                return ResourceAllocation(
                    success=False,
                    error_message=f"Resource {resource_id} not found"
                )
            
            if resource.status == ResourceStatus.ERROR:
                return ResourceAllocation(
                    success=False,
                    error_message=f"Resource {resource_id} is in error state"
                )
            
            available = resource.capacity - resource.used
            if available < request.required_gpu_memory:
                return ResourceAllocation(
                    success=False,
                    error_message=f"Insufficient memory on {resource_id}"
                )
            
            resource.status = ResourceStatus.BUSY
            resource.used += request.required_gpu_memory
            resource.last_used = time.time()
            resource.usage_count += 1
            
            logger.info(f"Allocated GPU {resource_id} for task {request.task_id}")
            return ResourceAllocation(
                success=True,
                resource_id=resource_id,
                allocated_capacity=request.required_gpu_memory,
                timeout=request.timeout
            )

    async def acquire(self, request: TaskRequest) -> ResourceAllocation:
        """获取GPU资源"""
        # 快速路径：立即分配
        resource_id = await self._find_available_resource(request.required_gpu_memory)
        if resource_id:
            return await self._allocate_resource(resource_id, request)
        
        # 慢速路径：加入等待队列
        async with self._lock:
            self._pending_tasks.append(request)
        
        # 等待资源可用或超时
        try:
            async with asyncio.timeout(request.timeout):
                while True:
                    resource_id = await self._find_available_resource(request.required_gpu_memory)
                    if resource_id:
                        async with self._lock:
                            if request in self._pending_tasks:
                                self._pending_tasks.remove(request)
                        return await self._allocate_resource(resource_id, request)
                    await asyncio.sleep(0.5)
        except asyncio.TimeoutError:
            async with self._lock:
                if request in self._pending_tasks:
                    self._pending_tasks.remove(request)
            self._failed_tasks += 1
            return ResourceAllocation(
                success=False,
                error_message="Timeout waiting for GPU resource"
            )

    async def release(self, resource_id: str) -> None:
        """释放GPU资源"""
        async with self._lock:
            resource = self._resources.get(resource_id)
            if resource:
                resource.used = 0.0  # 简化处理：释放全部占用
                resource.status = ResourceStatus.IDLE
                resource.last_used = time.time()
                logger.info(f"Released GPU {resource_id}")
                
                # 尝试处理等待队列中的任务
                await self._process_pending_tasks()

    async def _process_pending_tasks(self):
        """处理等待队列"""
        async with self._lock:
            # 按优先级排序
            sorted_tasks = sorted(
                self._pending_tasks,
                key=lambda t: [TaskPriority.CRITICAL, TaskPriority.HIGH, 
                               TaskPriority.MEDIUM, TaskPriority.LOW, 
                               TaskPriority.BACKGROUND].index(t.priority)
            )
            
            for task in sorted_tasks[:3]:  # 最多尝试3个任务
                resource_id = await self._find_available_resource(task.required_gpu_memory)
                if resource_id:
                    allocation = await self._allocate_resource(resource_id, task)
                    if allocation.success and task.callback:
                        asyncio.create_task(task.callback(allocation))
                    self._pending_tasks.remove(task)
                    self._completed_tasks += 1

    def get_statistics(self) -> PoolStatistics:
        """获取统计信息"""
        total = len(self._resources)
        idle = sum(1 for r in self._resources.values() if r.status == ResourceStatus.IDLE)
        busy = sum(1 for r in self._resources.values() if r.status == ResourceStatus.BUSY)
        total_capacity = sum(r.capacity for r in self._resources.values())
        used_capacity = sum(r.used for r in self._resources.values())
        
        return PoolStatistics(
            total_resources=total,
            idle_resources=idle,
            busy_resources=busy,
            average_utilization=(used_capacity / total_capacity) * 100 if total_capacity > 0 else 0,
            total_capacity=total_capacity,
            used_capacity=used_capacity,
            pending_tasks=len(self._pending_tasks),
            completed_tasks=self._completed_tasks,
            failed_tasks=self._failed_tasks
        )

    def get_resource_status(self, resource_id: str) -> Optional[ResourceDescriptor]:
        """获取资源状态"""
        return self._resources.get(resource_id)

    def _monitor_loop(self):
        """资源监控循环"""
        while self._monitor_running:
            try:
                stats = self.get_statistics()
                if stats.average_utilization > 90:
                    logger.warning(f"High GPU utilization: {stats.average_utilization:.1f}%")
                elif stats.idle_resources == stats.total_resources and stats.pending_tasks > 0:
                    logger.warning(f"All GPUs idle but {stats.pending_tasks} tasks pending")
                time.sleep(10)
            except Exception as e:
                logger.error(f"GPU monitor error: {e}")

    def start_monitor(self):
        """启动监控"""
        if not self._monitor_running:
            self._monitor_running = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

    def stop_monitor(self):
        """停止监控"""
        self._monitor_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)


class MultiModalResourceManager:
    """多模态资源管理器 - 统一调度GPU/CPU/内存资源"""

    _instance: Optional["MultiModalResourceManager"] = None

    def __new__(cls) -> "MultiModalResourceManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._gpu_pool = GPUResourcePool()
        self._task_registry: Dict[str, TaskRequest] = {}
        self._allocation_map: Dict[str, str] = {}  # task_id -> resource_id
        self._lock = asyncio.Lock()
        
        # 启动监控
        self._gpu_pool.start_monitor()
        logger.info("MultiModalResourceManager initialized")

    async def acquire_gpu(self, task_id: str, task_type: str, 
                          required_memory: float = 4.0,
                          priority: TaskPriority = TaskPriority.MEDIUM,
                          timeout: float = 300.0) -> ResourceAllocation:
        """获取GPU资源"""
        request = TaskRequest(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            required_gpu_memory=required_memory,
            timeout=timeout
        )
        
        async with self._lock:
            self._task_registry[task_id] = request
        
        allocation = await self._gpu_pool.acquire(request)
        
        if allocation.success:
            async with self._lock:
                self._allocation_map[task_id] = allocation.resource_id
        
        return allocation

    async def release_gpu(self, task_id: str) -> None:
        """释放GPU资源"""
        async with self._lock:
            resource_id = self._allocation_map.get(task_id)
            if resource_id:
                await self._gpu_pool.release(resource_id)
                del self._allocation_map[task_id]
                if task_id in self._task_registry:
                    del self._task_registry[task_id]

    def get_statistics(self) -> Dict[str, Any]:
        """获取综合统计"""
        gpu_stats = self._gpu_pool.get_statistics()
        return {
            "gpu": {
                "total": gpu_stats.total_resources,
                "idle": gpu_stats.idle_resources,
                "busy": gpu_stats.busy_resources,
                "utilization": gpu_stats.average_utilization,
                "total_capacity_gb": gpu_stats.total_capacity,
                "used_capacity_gb": gpu_stats.used_capacity,
            },
            "tasks": {
                "pending": gpu_stats.pending_tasks,
                "completed": gpu_stats.completed_tasks,
                "failed": gpu_stats.failed_tasks,
            }
        }

    def get_resource_status(self) -> List[Dict[str, Any]]:
        """获取所有资源状态"""
        status_list = []
        for rid, resource in self._gpu_pool._resources.items():
            status_list.append({
                "resource_id": rid,
                "type": resource.resource_type.value,
                "status": resource.status.value,
                "capacity_gb": resource.capacity,
                "used_gb": resource.used,
                "metadata": resource.metadata,
                "last_used": resource.last_used,
                "usage_count": resource.usage_count,
            })
        return status_list

    def suggest_batch_size(self, task_type: str) -> int:
        """根据资源状态建议批处理大小"""
        stats = self.get_statistics()
        gpu_util = stats["gpu"]["utilization"]
        
        if gpu_util < 30:
            return 8  # 低负载时增大批量
        elif gpu_util < 60:
            return 4  # 中等负载
        elif gpu_util < 80:
            return 2  # 较高负载
        else:
            return 1  # 高负载时单任务

    async def allocate_for_multimodal_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """为多模态任务分配资源"""
        task_id = task_spec["task_id"]
        task_type = task_spec["task_type"]
        requirements = task_spec.get("requirements", {})
        
        # 解析资源需求
        gpu_memory = requirements.get("gpu_memory", 4.0)
        priority = TaskPriority(requirements.get("priority", "medium"))
        
        # 获取资源
        allocation = await self.acquire_gpu(
            task_id=task_id,
            task_type=task_type,
            required_memory=gpu_memory,
            priority=priority
        )
        
        if allocation.success:
            return {
                "success": True,
                "resource_id": allocation.resource_id,
                "allocated_memory_gb": allocation.allocated_capacity,
                "message": "Resource allocated successfully"
            }
        else:
            return {
                "success": False,
                "error": allocation.error_message
            }

    async def release_from_multimodal_task(self, task_id: str) -> Dict[str, Any]:
        """释放多模态任务资源"""
        try:
            await self.release_gpu(task_id)
            return {"success": True, "message": "Resource released successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}


@dataclass
class PooledModelInstance:
    """池化模型实例"""
    model_id: str
    resource_id: str
    instance: Any
    last_used: float = 0.0
    usage_count: int = 0
    warm: bool = False  # 是否已预热


class ModelPoolManager:
    """模型池管理器 - 复用模型实例"""

    def __init__(self):
        self._model_pools: Dict[str, List[PooledModelInstance]] = {}
        self._lock = asyncio.Lock()
        self._resource_manager = get_multimodal_resource_manager()
        self._max_pool_size = 3  # 每个模型最大实例数

    async def get_model(self, model_id: str, task_id: str) -> Optional[PooledModelInstance]:
        """获取模型实例"""
        async with self._lock:
            pool = self._model_pools.get(model_id, [])
            
            # 优先返回预热好的空闲实例
            for instance in pool:
                if instance.warm and self._is_instance_idle(instance):
                    instance.last_used = time.time()
                    instance.usage_count += 1
                    return instance
            
            # 如果池未满，创建新实例
            if len(pool) < self._max_pool_size:
                return await self._create_model_instance(model_id, task_id)
            
            # 池已满，等待或返回None
            return None

    def _is_instance_idle(self, instance: PooledModelInstance) -> bool:
        """检查实例是否空闲"""
        # 简化判断：基于时间阈值
        return time.time() - instance.last_used > 1.0

    async def _create_model_instance(self, model_id: str, task_id: str) -> Optional[PooledModelInstance]:
        """创建模型实例"""
        # 先获取GPU资源
        allocation = await self._resource_manager.acquire_gpu(
            task_id=f"model_init_{model_id}",
            task_type="model_loading",
            required_memory=8.0,
            priority=TaskPriority.HIGH
        )
        
        if not allocation.success:
            logger.error(f"Failed to allocate GPU for model {model_id}")
            return None
        
        try:
            # 模拟模型加载（实际应调用真实的模型加载逻辑）
            logger.info(f"Loading model {model_id} on {allocation.resource_id}")
            await asyncio.sleep(2)  # 模拟加载时间
            
            instance = PooledModelInstance(
                model_id=model_id,
                resource_id=allocation.resource_id,
                instance=f"model_instance_{model_id}_{time.time()}",
                last_used=time.time(),
                warm=True
            )
            
            async with self._lock:
                if model_id not in self._model_pools:
                    self._model_pools[model_id] = []
                self._model_pools[model_id].append(instance)
            
            logger.info(f"Model {model_id} loaded successfully")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            await self._resource_manager.release_gpu(f"model_init_{model_id}")
            return None

    async def release_model(self, instance: PooledModelInstance) -> None:
        """释放模型实例（放回池中）"""
        instance.last_used = time.time()
        logger.debug(f"Model {instance.model_id} returned to pool")

    def get_pool_stats(self) -> Dict[str, Any]:
        """获取池统计"""
        stats = {}
        for model_id, pool in self._model_pools.items():
            warm_count = sum(1 for i in pool if i.warm)
            active_count = sum(1 for i in pool if time.time() - i.last_used < 10)
            stats[model_id] = {
                "pool_size": len(pool),
                "warm_instances": warm_count,
                "active_instances": active_count,
                "total_usage": sum(i.usage_count for i in pool)
            }
        return stats


# 全局单例
_resource_manager_instance: Optional[MultiModalResourceManager] = None
_model_pool_manager_instance: Optional[ModelPoolManager] = None


def get_multimodal_resource_manager() -> MultiModalResourceManager:
    """获取多模态资源管理器单例"""
    global _resource_manager_instance
    if _resource_manager_instance is None:
        _resource_manager_instance = MultiModalResourceManager()
    return _resource_manager_instance


def get_model_pool_manager() -> ModelPoolManager:
    """获取模型池管理器单例"""
    global _model_pool_manager_instance
    if _model_pool_manager_instance is None:
        _model_pool_manager_instance = ModelPoolManager()
    return _model_pool_manager_instance


# 使用示例
async def example_usage():
    """资源池使用示例"""
    resource_manager = get_multimodal_resource_manager()
    model_pool = get_model_pool_manager()
    
    # 获取资源统计
    stats = resource_manager.get_statistics()
    print("Resource Statistics:", stats)
    
    # 为任务分配资源
    allocation = await resource_manager.allocate_for_multimodal_task({
        "task_id": "example_task_001",
        "task_type": "text_to_image",
        "requirements": {
            "gpu_memory": 8.0,
            "priority": "high"
        }
    })
    
    if allocation["success"]:
        print(f"Allocated resource: {allocation['resource_id']}")
        
        # 获取模型实例
        model = await model_pool.get_model("sdxl_1.0", "example_task_001")
        if model:
            print(f"Got model instance: {model.instance}")
            
            # 使用模型...
            
            # 释放模型（放回池中）
            await model_pool.release_model(model)
        
        # 释放资源
        await resource_manager.release_from_multimodal_task("example_task_001")
        print("Resource released")
