"""智能调度器进阶 - 基于机器学习的任务调度优化"""

import asyncio
import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple
from enum import Enum
import heapq

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

logger = logging.getLogger("hydraflow.core.smart_scheduler")


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskMetadata:
    """任务元数据"""
    task_id: str
    task_type: str
    priority: TaskPriority
    resource_requirements: Dict[str, float]  # gpu_memory, cpu_cores, ram
    estimated_duration: float
    dependencies: List[str]
    created_at: float = field(default_factory=time.time)
    user_id: Optional[str] = None
    project_id: Optional[str] = None


@dataclass
class SchedulerState:
    """调度器状态"""
    current_load: Dict[str, float]  # cpu, gpu, ram utilization
    active_tasks: int
    pending_tasks: int
    completed_tasks: int
    failed_tasks: int


class TaskFeatureExtractor:
    """任务特征提取器"""
    
    def __init__(self):
        self.priority_weights = {
            TaskPriority.CRITICAL: 10.0,
            TaskPriority.HIGH: 5.0,
            TaskPriority.MEDIUM: 2.0,
            TaskPriority.LOW: 1.0,
            TaskPriority.BACKGROUND: 0.5,
        }
    
    def extract(self, task: TaskMetadata, state: SchedulerState) -> np.ndarray:
        """提取任务特征向量"""
        features = [
            # 优先级权重
            self.priority_weights[task.priority],
            
            # 资源需求归一化
            task.resource_requirements.get("gpu_memory", 0) / 48.0,  # 假设最大48GB
            task.resource_requirements.get("cpu_cores", 1) / 64.0,    # 假设最大64核
            task.resource_requirements.get("ram", 0) / 256.0,         # 假设最大256GB
            
            # 预估时长归一化
            min(task.estimated_duration / 300.0, 1.0),  # 最大5分钟
            
            # 当前系统负载
            state.current_load.get("cpu", 0),
            state.current_load.get("gpu", 0),
            state.current_load.get("ram", 0),
            
            # 队列状态
            state.pending_tasks / 100.0,  # 归一化到100个任务
            state.active_tasks / 10.0,    # 归一化到10个活跃任务
            
            # 等待时间
            (time.time() - task.created_at) / 60.0,  # 分钟数
        ]
        return np.array(features, dtype=np.float32)


class SchedulingModel:
    """调度评分模型"""
    
    def __init__(self):
        # 预训练的权重（可通过实际数据训练优化）
        self.weights = np.array([
            3.0,   # 优先级权重
            1.5,   # GPU需求
            0.5,   # CPU需求
            0.3,   # RAM需求
            1.0,   # 预估时长
            -2.0,  # CPU负载（负权重：负载高时降低分数）
            -2.5,  # GPU负载（负权重）
            -1.0,  # RAM负载（负权重）
            0.8,   # 待处理任务数
            0.5,   # 活跃任务数
            1.2,   # 等待时间
        ])
    
    def predict(self, features: np.ndarray) -> float:
        """预测任务优先级分数"""
        # 基础分数 = 特征 · 权重
        base_score = np.dot(features, self.weights)
        
        # 添加非线性修正
        # 如果等待时间过长，增加优先级
        wait_time = features[-1]
        if wait_time > 5.0:  # 等待超过5分钟
            base_score += wait_time * 0.5
        
        # 如果资源需求低，可以适当提高优先级
        resource_sum = features[1] + features[2] + features[3]
        if resource_sum < 0.2:  # 资源需求很低
            base_score += 2.0
        
        return float(base_score)


class MLBasedScheduler:
    """基于机器学习的智能调度器"""
    
    def __init__(self):
        self.task_heap: List[tuple] = []
        self.queued_tasks: Dict[str, TaskMetadata] = {}
        self.active_tasks: Dict[str, TaskMetadata] = {}
        self.completed_tasks: Dict[str, float] = {}
        
        self.feature_extractor = TaskFeatureExtractor()
        self.scheduling_model = SchedulingModel()
        
        self.lock = asyncio.Lock()
        self.counter = 0
        
        # 状态追踪
        self._current_load = {"cpu": 0.0, "gpu": 0.0, "ram": 0.0}
        self._completed_count = 0
        self._failed_count = 0
        
        logger.info("MLBasedScheduler initialized")
    
    def _get_state(self) -> SchedulerState:
        """获取当前调度器状态"""
        return SchedulerState(
            current_load=self._current_load.copy(),
            active_tasks=len(self.active_tasks),
            pending_tasks=len(self.queued_tasks),
            completed_tasks=self._completed_count,
            failed_tasks=self._failed_count,
        )
    
    async def add_task(self, task: TaskMetadata):
        """添加任务到调度队列"""
        async with self.lock:
            # 提取特征
            state = self._get_state()
            features = self.feature_extractor.extract(task, state)
            
            # 使用ML模型计算优先级分数
            ml_score = self.scheduling_model.predict(features)
            
            # 组合优先级：ML分数 + 基础优先级
            combined_score = ml_score
            
            # 添加到优先队列（使用负分数因为heapq是最小堆）
            self.counter += 1
            heapq.heappush(
                self.task_heap,
                (-combined_score, self.counter, task.task_id)
            )
            
            self.queued_tasks[task.task_id] = task
            logger.debug(f"Task {task.task_id} queued with score {combined_score:.2f}")
    
    async def get_next_task(self, max_concurrent: int = 5) -> Optional[TaskMetadata]:
        """获取下一个最优任务"""
        async with self.lock:
            if len(self.active_tasks) >= max_concurrent:
                return None
            
            # 扫描队列找就绪任务
            ready_tasks = []
            temp_heap = []
            
            while self.task_heap:
                neg_score, counter, task_id = heapq.heappop(self.task_heap)
                
                if task_id not in self.queued_tasks:
                    continue
                
                task = self.queued_tasks[task_id]
                
                # 检查依赖
                if not await self._check_dependencies(task):
                    temp_heap.append((neg_score, counter, task_id))
                    continue
                
                # 检查资源可用性
                if not await self._check_resources(task):
                    temp_heap.append((neg_score, counter, task_id))
                    continue
                
                ready_tasks.append((neg_score, counter, task))
            
            # 恢复未就绪任务
            while temp_heap:
                heapq.heappush(self.task_heap, temp_heap.pop())
            
            # 选择最优任务（分数最高 = 负分数最小）
            if ready_tasks:
                ready_tasks.sort(key=lambda x: (x[0], x[1]))
                _, _, task = ready_tasks[0]
                
                del self.queued_tasks[task.task_id]
                self.active_tasks[task.task_id] = task
                
                # 更新负载估计
                self._update_load(task, is_acquire=True)
                
                logger.info(f"Selected task {task.task_id} (score: {-ready_tasks[0][0]:.2f})")
                return task
            
            return None
    
    async def _check_dependencies(self, task: TaskMetadata) -> bool:
        """检查依赖是否完成"""
        for dep_id in task.dependencies:
            if dep_id in self.active_tasks:
                return False
            # 依赖未提交也不算完成
            if dep_id not in self.completed_tasks:
                return False
        return True
    
    async def _check_resources(self, task: TaskMetadata) -> bool:
        """检查资源是否可用"""
        reqs = task.resource_requirements
        
        # 简单检查：预留20%安全余量
        cpu_available = self._current_load["cpu"] < 0.8
        gpu_available = self._current_load["gpu"] + (reqs.get("gpu_memory", 0) / 48.0) < 0.8
        ram_available = self._current_load["ram"] + (reqs.get("ram", 0) / 256.0) < 0.8
        
        return cpu_available and gpu_available and ram_available
    
    def _update_load(self, task: TaskMetadata, is_acquire: bool):
        """更新资源负载估计"""
        reqs = task.resource_requirements
        factor = 1.0 if is_acquire else -1.0
        
        self._current_load["cpu"] = max(0.0, min(1.0,
            self._current_load["cpu"] + factor * (reqs.get("cpu_cores", 1) / 64.0)
        ))
        self._current_load["gpu"] = max(0.0, min(1.0,
            self._current_load["gpu"] + factor * (reqs.get("gpu_memory", 0) / 48.0)
        ))
        self._current_load["ram"] = max(0.0, min(1.0,
            self._current_load["ram"] + factor * (reqs.get("ram", 0) / 256.0)
        ))
    
    async def complete_task(self, task_id: str, success: bool):
        """标记任务完成"""
        async with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks.pop(task_id)
                self.completed_tasks[task_id] = time.time()
                
                # 更新负载
                self._update_load(task, is_acquire=False)
                
                if success:
                    self._completed_count += 1
                else:
                    self._failed_count += 1
                
                # 限制已完成任务记录
                if len(self.completed_tasks) > 10000:
                    oldest = sorted(self.completed_tasks.keys(),
                                   key=lambda k: self.completed_tasks[k])[:5000]
                    for key in oldest:
                        del self.completed_tasks[key]
                
                logger.debug(f"Task {task_id} completed (success={success})")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "queued": len(self.queued_tasks),
            "active": len(self.active_tasks),
            "completed": self._completed_count,
            "failed": self._failed_count,
            "load": self._current_load.copy(),
            "heap_size": len(self.task_heap),
        }


class AdaptiveScheduler:
    """自适应调度器 - 结合规则和ML"""
    
    def __init__(self):
        self.ml_scheduler = MLBasedScheduler()
        self.rules_engine = RulesEngine()
        
        # 自适应权重：决定ML和规则的权重
        self.ml_weight = 0.7  # ML占70%
        self.rule_weight = 0.3  # 规则占30%
        
        self.adaptation_interval = 60  # 每分钟调整一次
        self._adaptation_task = None
        
        logger.info("AdaptiveScheduler initialized")
    
    async def start(self):
        """启动自适应调度器"""
        self._adaptation_task = asyncio.create_task(self._adaptation_loop())
    
    async def stop(self):
        """停止调度器"""
        if self._adaptation_task:
            self._adaptation_task.cancel()
    
    async def _adaptation_loop(self):
        """自适应调整循环"""
        while True:
            await asyncio.sleep(self.adaptation_interval)
            await self._adapt_weights()
    
    async def _adapt_weights(self):
        """根据系统状态调整ML和规则的权重"""
        stats = self.ml_scheduler.get_stats()
        
        # 如果系统负载很高，增加规则权重（更保守）
        avg_load = (stats["load"]["cpu"] + stats["load"]["gpu"] + stats["load"]["ram"]) / 3
        
        if avg_load > 0.8:
            self.ml_weight = 0.5
            self.rule_weight = 0.5
        elif avg_load < 0.3:
            self.ml_weight = 0.8
            self.rule_weight = 0.2
        else:
            self.ml_weight = 0.7
            self.rule_weight = 0.3
        
        logger.debug(f"Adapted weights: ML={self.ml_weight}, Rule={self.rule_weight}")
    
    async def add_task(self, task: TaskMetadata):
        """添加任务"""
        await self.ml_scheduler.add_task(task)
    
    async def get_next_task(self, max_concurrent: int = 5) -> Optional[TaskMetadata]:
        """获取下一个任务"""
        # 使用ML调度器获取任务
        task = await self.ml_scheduler.get_next_task(max_concurrent)
        
        if task:
            # 应用规则检查
            if await self.rules_engine.should_execute(task, self.ml_scheduler.get_stats()):
                return task
            else:
                # 规则拒绝，放回队列并尝试下一个
                await self.ml_scheduler.add_task(task)
                return await self.get_next_task(max_concurrent)
        
        return None
    
    async def complete_task(self, task_id: str, success: bool):
        """标记任务完成"""
        await self.ml_scheduler.complete_task(task_id, success)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        stats = self.ml_scheduler.get_stats()
        stats["weights"] = {
            "ml": self.ml_weight,
            "rule": self.rule_weight
        }
        return stats


class RulesEngine:
    """规则引擎 - 实现硬性规则约束"""
    
    async def should_execute(self, task: TaskMetadata, stats: Dict[str, Any]) -> bool:
        """判断任务是否应该执行"""
        # 规则1：CRITICAL任务必须立即执行
        if task.priority == TaskPriority.CRITICAL:
            return True
        
        # 规则2：后台任务只能在系统空闲时执行
        if task.priority == TaskPriority.BACKGROUND:
            if stats["load"]["cpu"] > 0.5 or stats["load"]["gpu"] > 0.5:
                return False
        
        # 规则3：高资源需求任务需要检查可用性
        if task.resource_requirements.get("gpu_memory", 0) > 24:  # 大模型
            if stats["load"]["gpu"] > 0.5:
                return False
        
        return True


# 全局单例
_adaptive_scheduler_instance: Optional[AdaptiveScheduler] = None


def get_adaptive_scheduler() -> AdaptiveScheduler:
    """获取自适应调度器单例"""
    global _adaptive_scheduler_instance
    if _adaptive_scheduler_instance is None:
        _adaptive_scheduler_instance = AdaptiveScheduler()
    return _adaptive_scheduler_instance


# 使用示例
async def example_usage():
    """智能调度器使用示例"""
    scheduler = get_adaptive_scheduler()
    await scheduler.start()
    
    # 添加任务
    task1 = TaskMetadata(
        task_id="task_001",
        task_type="text_to_image",
        priority=TaskPriority.HIGH,
        resource_requirements={"gpu_memory": 8.0, "cpu_cores": 4, "ram": 16.0},
        estimated_duration=30.0,
        dependencies=[],
        user_id="user_001"
    )
    await scheduler.add_task(task1)
    
    # 获取任务
    next_task = await scheduler.get_next_task(max_concurrent=3)
    if next_task:
        print(f"Selected task: {next_task.task_id}")
        
        # 执行任务...
        
        # 标记完成
        await scheduler.complete_task(next_task.task_id, success=True)
    
    # 获取统计
    stats = scheduler.get_stats()
    print(f"Scheduler stats: {stats}")
    
    await scheduler.stop()
