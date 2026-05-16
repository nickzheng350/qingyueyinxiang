"""HydraFlow AI 异步批量处理优化模块"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Generic, TypeVar, Optional
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

T = TypeVar("T")
R = TypeVar("R")

logger = logging.getLogger("hydraflow.batch")


@dataclass
class BatchConfig:
    """批量处理配置"""
    max_batch_size: int = 100
    max_wait_time: float = 0.1
    max_concurrent_batches: int = 10
    retry_attempts: int = 3
    retry_delay: float = 0.5


@dataclass
class BatchResult(Generic[T]):
    """批量处理结果"""
    items: list[T]
    successful: list[T]
    failed: list[tuple[T, Exception]]
    duration: float
    total: int
    success_count: int
    failure_count: int

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total == 0:
            return 0.0
        return self.success_count / self.total


class BatchProcessor(ABC, Generic[T, R]):
    """批量处理器抽象基类"""

    @abstractmethod
    async def process_item(self, item: T) -> R:
        """处理单个项目"""
        pass

    async def process_batch(self, items: list[T]) -> BatchResult[R]:
        """批量处理"""
        start_time = time.time()
        successful = []
        failed = []

        for item in items:
            try:
                result = await self.process_item(item)
                successful.append(result)
            except Exception as e:
                failed.append((item, e))

        duration = time.time() - start_time

        return BatchResult(
            items=items,
            successful=successful,
            failed=failed,
            duration=duration,
            total=len(items),
            success_count=len(successful),
            failure_count=len(failed),
        )


class AsyncBatcher(Generic[T]):
    """异步批处理器 - 自动收集项目并批量处理"""

    def __init__(
        self,
        processor: Callable[[list[T]], Awaitable[list[R]]],
        config: Optional[BatchConfig] = None,
    ):
        self._processor = processor
        self._config = config or BatchConfig()
        self._queue: asyncio.Queue[tuple[T, asyncio.Future[R]]] = asyncio.Queue(
            maxsize=self._config.max_batch_size * 2
        )
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()

    async def _process_loop(self) -> None:
        """处理循环"""
        while self._running:
            batch: list[tuple[T, asyncio.Future[R]]] = []
            timeout_task = asyncio.create_task(asyncio.sleep(self._config.max_wait_time))

            try:
                while len(batch) < self._config.max_batch_size:
                    try:
                        item_task = asyncio.create_task(self._queue.get())
                        done, pending = await asyncio.wait(
                            [item_task, timeout_task],
                            return_when=asyncio.FIRST_COMPLETED,
                        )

                        if item_task in done:
                            batch_item = item_task.result()
                            batch.append(batch_item)
                            timeout_task.cancel()
                        else:
                            item_task.cancel()
                            timeout_task.cancel()
                            break

                    except Exception:
                        break

                if batch:
                    items = [item for item, _ in batch]
                    futures = [future for _, future in batch]

                    try:
                        results = await self._processor(items)
                        for future, result in zip(futures, results):
                            future.set_result(result)
                    except Exception as e:
                        for future in futures:
                            if not future.done():
                                future.set_exception(e)

            except Exception as e:
                for _, future in batch:
                    if not future.done():
                        future.set_exception(e)

            await asyncio.sleep(0)

    async def submit(self, item: T) -> R:
        """提交项目并等待结果"""
        if not self._running:
            async with self._lock:
                if not self._running:
                    self._running = True
                    self._processing_task = asyncio.create_task(self._process_loop())

        future: asyncio.Future[R] = asyncio.get_event_loop().create_future()
        await self._queue.put((item, future))
        return await future

    async def close(self) -> None:
        """关闭批处理器"""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass


class SemaphoreLimiter:
    """信号量限制器 - 控制并发"""

    def __init__(self, max_concurrent: int):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active = 0
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self):
        """获取许可"""
        async with self._semaphore:
            async with self._lock:
                self._active += 1
            try:
                yield
            finally:
                async with self._lock:
                    self._active -= 1

    async def run(self, coro: Awaitable[T]) -> T:
        """运行协程（带并发限制）"""
        async with self.acquire():
            return await coro

    @property
    def active_count(self) -> int:
        """当前活跃数量"""
        return self._active


class RateLimiter:
    """速率限制器 - 控制请求速率"""

    def __init__(self, max_per_second: float):
        self._max_per_second = max_per_second
        self._min_interval = 1.0 / max_per_second if max_per_second > 0 else 0
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """获取许可（等待直到可以执行）"""
        async with self._lock:
            now = time.time()
            time_since_last = now - self._last_call

            if time_since_last < self._min_interval:
                wait_time = self._min_interval - time_since_last
                await asyncio.sleep(wait_time)

            self._last_call = time.time()


class ConcurrencyController:
    """并发控制器 - 组合信号量和速率限制"""

    def __init__(
        self,
        max_concurrent: int = 10,
        max_per_second: float = 0,
    ):
        self._semaphore = SemaphoreLimiter(max_concurrent)
        self._rate_limiter = RateLimiter(max_per_second) if max_per_second > 0 else None

    @asynccontextmanager
    async def limit(self):
        """上下文管理器获取许可"""
        if self._rate_limiter:
            await self._rate_limiter.acquire()

        async with self._semaphore.acquire():
            yield


class ChunkedProcessor(Generic[T, R]):
    """分块处理器 - 将大列表分块处理"""

    def __init__(
        self,
        processor: Callable[[list[T]], Awaitable[list[R]]],
        chunk_size: int = 50,
        max_concurrent: int = 5,
    ):
        self._processor = processor
        self._chunk_size = chunk_size
        self._concurrency = SemaphoreLimiter(max_concurrent)

    async def _process_chunk(self, chunk: list[T]) -> list[R]:
        """处理单个块"""
        async with self._concurrency.acquire():
            return await self._processor(chunk)

    async def process(self, items: list[T]) -> list[R]:
        """分块处理所有项目"""
        chunks = [
            items[i:i + self._chunk_size]
            for i in range(0, len(items), self._chunk_size)
        ]

        tasks = [self._process_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)

        flattened = []
        for result in results:
            flattened.extend(result)

        return flattened


class RetryProcessor(Generic[T, R]):
    """重试处理器 - 失败自动重试"""

    def __init__(
        self,
        processor: Callable[[T], Awaitable[R]],
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 0.1,
    ):
        self._processor = processor
        self._max_attempts = max_attempts
        self._backoff_factor = backoff_factor
        self._initial_delay = initial_delay

    async def process(self, item: T) -> R:
        """处理项目（带重试）"""
        last_exception = None

        for attempt in range(self._max_attempts):
            try:
                return await self._processor(item)
            except Exception as e:
                last_exception = e
                if attempt < self._max_attempts - 1:
                    delay = self._initial_delay * (self._backoff_factor ** attempt)
                    await asyncio.sleep(delay)

        raise last_exception


class PipelineProcessor(Generic[T]):
    """管道处理器 - 多步骤处理"""

    def __init__(self):
        self._steps: list[Callable[[Any], Awaitable[Any]]] = []

    def add_step(self, step: Callable[[Any], Awaitable[Any]]) -> "PipelineProcessor":
        """添加处理步骤"""
        self._steps.append(step)
        return self

    async def process(self, item: T) -> Any:
        """处理项目（经过所有步骤）"""
        result = item
        for step in self._steps:
            result = await step(result)
        return result

    async def process_batch(self, items: list[T]) -> list[Any]:
        """批量处理"""
        return [await self.process(item) for item in items]
