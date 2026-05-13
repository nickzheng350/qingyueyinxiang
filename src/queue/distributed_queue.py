"""分布式任务队列 - 支持延迟任务、任务重试、优先级队列"""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod
import heapq
import threading

logger = logging.getLogger("hydraflow.distributed_queue")


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    DELAYED = "delayed"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """任务"""
    task_id: str
    task_type: str
    payload: Any
    priority: int = 0  # 越小优先级越高
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    scheduled_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 300.0
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class DelayedTask(Task):
    """延迟任务"""
    execute_at: float = 0.0

    def __lt__(self, other):
        if isinstance(other, DelayedTask):
            return self.execute_at < other.execute_at
        return False


class RetryStrategy:
    """重试策略"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        exponential_base: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.exponential_base = exponential_base
        self.max_delay = max_delay
        self.jitter = jitter

    def get_delay(self, retry_count: int) -> float:
        """计算重试延迟"""
        delay = min(
            self.base_delay * (self.exponential_base ** retry_count),
            self.max_delay
        )

        if self.jitter:
            import random
            delay *= (0.5 + random.random())

        return delay


class DistributedTaskQueue:
    """分布式任务队列"""

    def __init__(
        self,
        name: str = "default",
        max_workers: int = 10,
        retry_strategy: Optional[RetryStrategy] = None
    ):
        self.name = name
        self.max_workers = max_workers
        self.retry_strategy = retry_strategy or RetryStrategy()

        # 任务存储
        self.tasks: Dict[str, Task] = {}
        self.pending_heap: List[DelayedTask] = []  # 延迟任务堆
        self.ready_heap: List[DelayedTask] = []  # 就绪任务堆（优先级队列）
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}

        # 工作者
        self.workers: Dict[str, asyncio.Task] = {}
        self.worker_semaphore = asyncio.Semaphore(max_workers)

        # 任务处理器
        self.task_handlers: Dict[str, Callable] = {}

        # 统计
        self.stats = {
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_retried": 0,
        }

        # 控制
        self._running = False
        self._lock = threading.RLock()
        self._scheduler_task: Optional[asyncio.Task] = None

        logger.info(f"DistributedTaskQueue '{name}' initialized")

    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    def enqueue(
        self,
        task_type: str,
        payload: Any,
        priority: int = 0,
        delay_seconds: float = 0.0,
        max_retries: int = None
    ) -> str:
        """入队任务"""
        task_id = str(uuid.uuid4())

        task = Task(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority,
            max_retries=max_retries if max_retries is not None else self.retry_strategy.max_retries,
        )

        with self._lock:
            self.tasks[task_id] = task

            if delay_seconds > 0:
                task.status = TaskStatus.DELAYED
                delayed_task = DelayedTask(
                    **{**task.__dict__, "execute_at": time.time() + delay_seconds}
                )
                heapq.heappush(self.pending_heap, delayed_task)
            else:
                task.status = TaskStatus.QUEUED
                heapq.heappush(self.ready_heap, task)

            self.stats["total_enqueued"] += 1

        logger.debug(f"Enqueued task {task_id} ({task_type}), delay={delay_seconds}s")

        # 触发调度
        asyncio.create_task(self._schedule_if_needed())

        return task_id

    async def _schedule_if_needed(self):
        """必要时触发调度"""
        if not self._running:
            return

        if self._scheduler_task is None or self._scheduler_task.done():
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def _scheduler_loop(self):
        """调度循环"""
        while self._running:
            try:
                await self._process_delayed_tasks()
                await self._process_ready_tasks()
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

    async def _process_delayed_tasks(self):
        """处理延迟任务"""
        with self._lock:
            while self.pending_heap:
                task = self.pending_heap[0]
                if task.execute_at > time.time():
                    break

                heapq.heappop(self.pending_heap)
                task.status = TaskStatus.QUEUED
                heapq.heappush(self.ready_heap, task)

    async def _process_ready_tasks(self):
        """处理就绪任务"""
        with self._lock:
            while self.ready_heap and len(self.running_tasks) < self.max_workers:
                task = heapq.heappop(self.ready_heap)
                if task.status == TaskStatus.QUEUED:
                    self.running_tasks[task.task_id] = task
                    asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: Task):
        """执行任务"""
        async with self.worker_semaphore:
            if task.task_type not in self.task_handlers:
                task.status = TaskStatus.FAILED
                task.error = f"No handler for task type: {task.task_type}"
                logger.error(f"Task {task.task_id} failed: {task.error}")
                return

            task.status = TaskStatus.RUNNING
            task.started_at = time.time()

            handler = self.task_handlers[task.task_type]

            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await asyncio.wait_for(
                        handler(task.payload),
                        timeout=task.timeout_seconds
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, lambda: handler(task.payload)),
                        timeout=task.timeout_seconds
                    )

                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = time.time()
                self.stats["total_completed"] += 1

                logger.info(f"Task {task.task_id} completed")

            except asyncio.TimeoutError:
                task.status = TaskStatus.FAILED
                task.error = "Task timeout"
                await self._handle_task_failure(task)

            except Exception as e:
                task.error = str(e)
                await self._handle_task_failure(task)

            finally:
                with self._lock:
                    if task.task_id in self.running_tasks:
                        del self.running_tasks[task.task_id]
                    self.completed_tasks[task.task_id] = task

    async def _handle_task_failure(self, task: Task):
        """处理任务失败"""
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            delay = self.retry_strategy.get_delay(task.retry_count)

            task.status = TaskStatus.DELAYED
            task.execute_at = time.time() + delay

            with self._lock:
                heapq.heappush(self.pending_heap, task)

            self.stats["total_retried"] += 1
            logger.warning(f"Task {task.task_id} failed, retrying in {delay:.2f}s (attempt {task.retry_count})")

        else:
            task.status = TaskStatus.FAILED
            self.stats["total_failed"] += 1
            logger.error(f"Task {task.task_id} failed permanently after {task.retry_count} retries")

    def cancel(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status in [TaskStatus.PENDING, TaskStatus.DELAYED, TaskStatus.QUEUED]:
                    task.status = TaskStatus.CANCELLED
                    logger.info(f"Task {task_id} cancelled")
                    return True
        return False

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        if task_id in self.tasks:
            return self.tasks[task_id].status
        return None

    def get_task_result(self, task_id: str) -> Optional[Any]:
        """获取任务结果"""
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            if task.status == TaskStatus.COMPLETED:
                return task.result
            elif task.status == TaskStatus.FAILED:
                return {"error": task.error}
        return None

    async def start(self):
        """启动队列"""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"DistributedTaskQueue '{self.name}' started")

    async def stop(self):
        """停止队列"""
        self._running = False

        if self._scheduler_task:
            self._scheduler_task.cancel()

        # 等待所有运行中的任务完成
        if self.running_tasks:
            logger.info(f"Waiting for {len(self.running_tasks)} running tasks to complete")
            await asyncio.gather(
                *[asyncio.shield(t) for t in asyncio.all_tasks() if not t.done()],
                return_exceptions=True
            )

        logger.info(f"DistributedTaskQueue '{self.name}' stopped")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        with self._lock:
            return {
                "name": self.name,
                "running": self._running,
                "total_tasks": len(self.tasks),
                "pending_tasks": len(self.pending_heap),
                "ready_tasks": len(self.ready_heap),
                "running_tasks": len(self.running_tasks),
                "completed_tasks": len(self.completed_tasks),
                **self.stats,
            }


# 全局队列管理器
_queue_manager: Dict[str, DistributedTaskQueue] = {}


def get_distributed_queue(name: str = "default", max_workers: int = 10) -> DistributedTaskQueue:
    """获取分布式队列"""
    if name not in _queue_manager:
        _queue_manager[name] = DistributedTaskQueue(name=name, max_workers=max_workers)
    return _queue_manager[name]
