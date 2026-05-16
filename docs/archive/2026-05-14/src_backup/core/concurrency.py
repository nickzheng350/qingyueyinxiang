"""同步/异步/并行结构机制 - 统一并发框架"""

import asyncio
import concurrent.futures
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
)

T = TypeVar("T")
R = TypeVar("R")


class ExecutionMode(Enum):
    """执行模式"""
    SYNC = "sync"
    ASYNC = "async"
    PARALLEL = "parallel"


@dataclass
class TaskResult(Generic[R]):
    """任务结果"""
    success: bool
    result: Optional[R] = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    mode: ExecutionMode = ExecutionMode.SYNC


@dataclass
class BatchResult(Generic[R]):
    """批量任务结果"""
    results: List[TaskResult[R]]
    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    total_time: float = 0.0

    def __post_init__(self):
        self.total_count = len(self.results)
        self.success_count = sum(1 for r in self.results if r.success)
        self.failed_count = self.total_count - self.success_count


class SyncExecutor:
    """同步执行器"""

    @staticmethod
    def execute(func: Callable[..., R], *args, **kwargs) -> TaskResult[R]:
        """同步执行函数"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            return TaskResult(
                success=True,
                result=result,
                execution_time=execution_time,
                mode=ExecutionMode.SYNC,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TaskResult(
                success=False,
                error=e,
                execution_time=execution_time,
                mode=ExecutionMode.SYNC,
            )

    @staticmethod
    def batch_execute(
        tasks: List[Tuple[Callable[..., R], Tuple, Dict]],
    ) -> BatchResult[R]:
        """批量同步执行"""
        start_time = time.time()
        results = []
        for func, args, kwargs in tasks:
            results.append(SyncExecutor.execute(func, *args, **kwargs))
        total_time = time.time() - start_time
        return BatchResult(results=results, total_time=total_time)


class AsyncExecutor:
    """异步执行器"""

    @staticmethod
    async def execute(func: Callable[..., R], *args, **kwargs) -> TaskResult[R]:
        """异步执行函数"""
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            return TaskResult(
                success=True,
                result=result,
                execution_time=execution_time,
                mode=ExecutionMode.ASYNC,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TaskResult(
                success=False,
                error=e,
                execution_time=execution_time,
                mode=ExecutionMode.ASYNC,
            )

    @staticmethod
    async def batch_execute(
        tasks: List[Tuple[Callable[..., R], Tuple, Dict]],
        max_concurrent: Optional[int] = None,
    ) -> BatchResult[R]:
        """批量异步执行"""
        start_time = time.time()

        if max_concurrent:
            semaphore = asyncio.Semaphore(max_concurrent)

            async def _wrapped(func, args, kwargs):
                async with semaphore:
                    return await AsyncExecutor.execute(func, *args, **kwargs)

            coroutines = [_wrapped(func, args, kwargs) for func, args, kwargs in tasks]
        else:
            coroutines = [AsyncExecutor.execute(func, args, kwargs) for func, args, kwargs in tasks]

        results = await asyncio.gather(*coroutines, return_exceptions=False)
        total_time = time.time() - start_time
        return BatchResult(results=results, total_time=total_time)

    @staticmethod
    async def batch_execute_with_group(
        tasks: List[Tuple[Callable[..., R], Tuple, Dict]],
    ) -> BatchResult[R]:
        """使用 TaskGroup 批量执行"""
        start_time = time.time()
        results = []

        async with asyncio.TaskGroup() as tg:
            for func, args, kwargs in tasks:
                task = tg.create_task(AsyncExecutor.execute(func, *args, **kwargs))
                results.append(task)

        completed_results = [t.result() for t in results]
        total_time = time.time() - start_time
        return BatchResult(results=completed_results, total_time=total_time)


class ParallelExecutor:
    """并行执行器 (线程池)"""

    _default_executor: Optional[ThreadPoolExecutor] = None
    _executors: Dict[str, ThreadPoolExecutor] = {}
    _lock = threading.Lock()

    @classmethod
    def get_executor(cls, name: str = "default", max_workers: int = 4) -> ThreadPoolExecutor:
        """获取或创建执行器"""
        with cls._lock:
            if name not in cls._executors:
                cls._executors[name] = ThreadPoolExecutor(max_workers=max_workers)
            return cls._executors[name]

    @classmethod
    def shutdown_executor(cls, name: str = "default") -> None:
        """关闭执行器"""
        with cls._lock:
            if name in cls._executors:
                cls._executors[name].shutdown(wait=True)
                del cls._executors[name]

    @classmethod
    def shutdown_all(cls) -> None:
        """关闭所有执行器"""
        with cls._lock:
            for executor in cls._executors.values():
                executor.shutdown(wait=True)
            cls._executors.clear()

    @staticmethod
    def execute(
        func: Callable[..., R],
        *args,
        executor_name: str = "default",
        max_workers: int = 4,
        **kwargs,
    ) -> TaskResult[R]:
        """并行执行函数"""
        executor = ParallelExecutor.get_executor(executor_name, max_workers)
        start_time = time.time()
        try:
            future = executor.submit(func, *args, **kwargs)
            result = future.result()
            execution_time = time.time() - start_time
            return TaskResult(
                success=True,
                result=result,
                execution_time=execution_time,
                mode=ExecutionMode.PARALLEL,
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TaskResult(
                success=False,
                error=e,
                execution_time=execution_time,
                mode=ExecutionMode.PARALLEL,
            )

    @staticmethod
    def batch_execute(
        tasks: List[Tuple[Callable[..., R], Tuple, Dict]],
        executor_name: str = "default",
        max_workers: int = 4,
    ) -> BatchResult[R]:
        """批量并行执行"""
        executor = ParallelExecutor.get_executor(executor_name, max_workers)
        start_time = time.time()

        futures = []
        for func, args, kwargs in tasks:
            future = executor.submit(func, *args, **kwargs)
            futures.append(future)

        results = []
        for future in futures:
            try:
                result = future.result()
                results.append(
                    TaskResult(
                        success=True,
                        result=result,
                        execution_time=0.0,
                        mode=ExecutionMode.PARALLEL,
                    )
                )
            except Exception as e:
                results.append(
                    TaskResult(
                        success=False,
                        error=e,
                        execution_time=0.0,
                        mode=ExecutionMode.PARALLEL,
                    )
                )

        total_time = time.time() - start_time
        for i, result in enumerate(results):
            result.execution_time = total_time / len(results) if results else 0.0

        return BatchResult(results=results, total_time=total_time)


class UnifiedExecutor(Generic[R]):
    """统一执行器 - 自动选择模式"""

    @staticmethod
    def execute(
        func: Callable[..., R],
        *args,
        mode: Optional[ExecutionMode] = None,
        **kwargs,
    ) -> TaskResult[R]:
        """统一执行接口"""
        if mode is None:
            if asyncio.iscoroutinefunction(func):
                mode = ExecutionMode.ASYNC
            else:
                mode = ExecutionMode.SYNC

        if mode == ExecutionMode.SYNC:
            return SyncExecutor.execute(func, *args, **kwargs)
        elif mode == ExecutionMode.ASYNC:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(AsyncExecutor.execute(func, *args, **kwargs))
        elif mode == ExecutionMode.PARALLEL:
            return ParallelExecutor.execute(func, *args, **kwargs)
        else:
            return SyncExecutor.execute(func, *args, **kwargs)

    @staticmethod
    async def async_execute(
        func: Callable[..., R],
        *args,
        mode: Optional[ExecutionMode] = None,
        **kwargs,
    ) -> TaskResult[R]:
        """异步统一执行"""
        if mode is None:
            if asyncio.iscoroutinefunction(func):
                mode = ExecutionMode.ASYNC
            else:
                mode = ExecutionMode.SYNC

        if mode == ExecutionMode.SYNC:
            return SyncExecutor.execute(func, *args, **kwargs)
        elif mode == ExecutionMode.ASYNC:
            return await AsyncExecutor.execute(func, *args, **kwargs)
        elif mode == ExecutionMode.PARALLEL:
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(None, lambda: ParallelExecutor.execute(func, *args, **kwargs))
            return await future
        else:
            return await AsyncExecutor.execute(func, *args, **kwargs)


def sync_to_async(func: Callable[..., R]) -> Callable[..., Any]:
    """同步函数转异步"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> R:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper


def async_to_sync(func: Callable[..., Any]) -> Callable[..., R]:
    """异步函数转同步"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> R:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper


@contextmanager
def parallel_context(
    name: str = "temp",
    max_workers: int = 4,
) -> Iterator[ThreadPoolExecutor]:
    """并行执行上下文管理器"""
    executor = ParallelExecutor.get_executor(name, max_workers)
    try:
        yield executor
    finally:
        pass


@asynccontextmanager
async def async_parallel_context(
    name: str = "temp",
    max_workers: int = 4,
) -> AsyncIterator[ThreadPoolExecutor]:
    """异步并行执行上下文管理器"""
    executor = ParallelExecutor.get_executor(name, max_workers)
    try:
        yield executor
    finally:
        pass


class ConcurrencyManager:
    """并发管理器 - 统一入口"""

    @staticmethod
    def sync(func: Callable[..., R], *args, **kwargs) -> TaskResult[R]:
        """同步执行"""
        return SyncExecutor.execute(func, *args, **kwargs)

    @staticmethod
    async def async_(func: Callable[..., R], *args, **kwargs) -> TaskResult[R]:
        """异步执行"""
        return await AsyncExecutor.execute(func, *args, **kwargs)

    @staticmethod
    def parallel(func: Callable[..., R], *args, **kwargs) -> TaskResult[R]:
        """并行执行"""
        return ParallelExecutor.execute(func, *args, **kwargs)

    @staticmethod
    def sync_batch(tasks: List[Tuple[Callable[..., R], Tuple, Dict]]) -> BatchResult[R]:
        """同步批量执行"""
        return SyncExecutor.batch_execute(tasks)

    @staticmethod
    async def async_batch(
        tasks: List[Tuple[Callable[..., R], Tuple, Dict]],
        max_concurrent: Optional[int] = None,
    ) -> BatchResult[R]:
        """异步批量执行"""
        return await AsyncExecutor.batch_execute(tasks, max_concurrent)

    @staticmethod
    def parallel_batch(
        tasks: List[Tuple[Callable[..., R], Tuple, Dict]],
        **kwargs,
    ) -> BatchResult[R]:
        """并行批量执行"""
        return ParallelExecutor.batch_execute(tasks, **kwargs)

    @staticmethod
    def cleanup() -> None:
        """清理资源"""
        ParallelExecutor.shutdown_all()
