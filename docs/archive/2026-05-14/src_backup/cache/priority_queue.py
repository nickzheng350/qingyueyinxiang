"""多级缓存优先队列 - 支持同步/异步/并行"""

import asyncio
import heapq
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, AsyncIterator, Dict, Generic, Iterator, List, Optional, Tuple, TypeVar

T = TypeVar("T")


class PriorityLevel(IntEnum):
    """优先级级别"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass(order=True)
class CacheItem(Generic[T]):
    """缓存项 - 支持优先级排序"""
    priority: int = field(compare=True)
    timestamp: float = field(compare=True)
    key: str = field(compare=False)
    value: T = field(compare=False)
    ttl: Optional[float] = field(default=None, compare=False)
    hit_count: int = field(default=0, compare=False)


class LRUCache(Generic[T]):
    """LRU 缓存层"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, Tuple[float, T]] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[T]:
        """获取项"""
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key][1]

    def put(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """放入项"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (time.time(), value)
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """删除项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """清空缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count


class PriorityQueueCache(Generic[T]):
    """优先级队列缓存"""

    def __init__(self, max_heap_size: int = 10000):
        self.max_heap_size = max_heap_size
        self._heap: List[CacheItem[T]] = []
        self._index: Dict[str, CacheItem[T]] = {}
        self._lock = threading.RLock()

    def put(
        self,
        key: str,
        value: T,
        priority: int = PriorityLevel.MEDIUM,
        ttl: Optional[float] = None,
    ) -> bool:
        """放入项"""
        with self._lock:
            if key in self._index:
                old_item = self._index[key]
                old_item.value = value
                old_item.hit_count += 1
                return False

            item = CacheItem(
                priority=priority,
                timestamp=time.time(),
                key=key,
                value=value,
                ttl=ttl,
            )

            heapq.heappush(self._heap, item)
            self._index[key] = item

            if len(self._heap) > self.max_heap_size:
                self._evict()

            return True

    def get(self, key: str) -> Optional[T]:
        """获取项"""
        with self._lock:
            item = self._index.get(key)
            if item is None:
                return None

            if item.ttl and (time.time() - item.timestamp) > item.ttl:
                self._remove_item(item)
                return None

            item.hit_count += 1
            return item.value

    def peek(self) -> Optional[CacheItem[T]]:
        """查看最高优先级项"""
        with self._lock:
            self._cleanup()
            if self._heap:
                return self._heap[0]
            return None

    def pop(self) -> Optional[CacheItem[T]]:
        """弹出最高优先级项"""
        with self._lock:
            self._cleanup()
            if not self._heap:
                return None

            item = heapq.heappop(self._heap)
            if item.key in self._index and self._index[item.key] is item:
                del self._index[item.key]
                return item
            return None

    def _cleanup(self) -> None:
        """清理过期项"""
        current_time = time.time()
        to_remove = []
        for item in list(self._index.values()):
            if item.ttl and (current_time - item.timestamp) > item.ttl:
                to_remove.append(item)
        for item in to_remove:
            self._remove_item(item)

    def _evict(self) -> None:
        """淘汰低优先级项"""
        while len(self._heap) > self.max_heap_size:
            item = heapq.heappop(self._heap)
            if item.key in self._index and self._index[item.key] is item:
                del self._index[item.key]

    def _remove_item(self, item: CacheItem[T]) -> None:
        """移除指定项"""
        if item.key in self._index:
            del self._index[item.key]

    def delete(self, key: str) -> bool:
        """删除项"""
        with self._lock:
            item = self._index.pop(key, None)
            return item is not None

    def clear(self) -> int:
        """清空缓存"""
        with self._lock:
            count = len(self._index)
            self._heap.clear()
            self._index.clear()
            return count

    def size(self) -> int:
        """缓存大小"""
        with self._lock:
            return len(self._index)


class MultiLevelCache(Generic[T]):
    """多级缓存 - L1(内存) + L2(优先级队列)"""

    def __init__(
        self,
        l1_max_size: int = 1000,
        l2_max_size: int = 10000,
    ):
        self.l1: LRUCache[T] = LRUCache(l1_max_size)
        self.l2: PriorityQueueCache[T] = PriorityQueueCache(l2_max_size)
        self._hits = {"l1": 0, "l2": 0, "total": 0}
        self._misses = 0

    def get(self, key: str) -> Optional[T]:
        """获取项"""
        self._hits["total"] += 1

        value = self.l1.get(key)
        if value is not None:
            self._hits["l1"] += 1
            return value

        value = self.l2.get(key)
        if value is not None:
            self._hits["l2"] += 1
            self.l1.put(key, value)
            return value

        self._misses += 1
        return None

    def put(
        self,
        key: str,
        value: T,
        priority: int = PriorityLevel.MEDIUM,
        ttl: Optional[float] = None,
    ) -> None:
        """放入项"""
        self.l1.put(key, value)
        self.l2.put(key, value, priority=priority, ttl=ttl)

    def put_high_priority(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """放入高优先级项"""
        self.put(key, value, priority=PriorityLevel.HIGH, ttl=ttl)

    def put_critical(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """放入关键项"""
        self.put(key, value, priority=PriorityLevel.CRITICAL, ttl=ttl)

    def delete(self, key: str) -> bool:
        """删除项"""
        l1_deleted = self.l1.delete(key)
        l2_deleted = self.l2.delete(key)
        return l1_deleted or l2_deleted

    def get_highest_priority(self) -> Optional[CacheItem[T]]:
        """获取最高优先级项"""
        return self.l2.peek()

    def pop_highest_priority(self) -> Optional[CacheItem[T]]:
        """弹出最高优先级项"""
        return self.l2.pop()

    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self._hits["total"]
        hit_rate = self._hits["total"] / (total + self._misses) if (total + self._misses) > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "l1_size": self.l1.max_size,
            "l2_size": self.l2.size(),
        }

    def clear(self) -> int:
        """清空所有缓存"""
        return self.l1.clear() + self.l2.clear()


class AsyncPriorityQueueCache(Generic[T]):
    """异步优先级队列缓存"""

    def __init__(self, max_heap_size: int = 10000):
        self.max_heap_size = max_heap_size
        self._heap: List[CacheItem[T]] = []
        self._index: Dict[str, CacheItem[T]] = {}
        self._lock = asyncio.Lock()

    async def put(
        self,
        key: str,
        value: T,
        priority: int = PriorityLevel.MEDIUM,
        ttl: Optional[float] = None,
    ) -> bool:
        """放入项"""
        async with self._lock:
            if key in self._index:
                old_item = self._index[key]
                old_item.value = value
                old_item.hit_count += 1
                return False

            item = CacheItem(
                priority=priority,
                timestamp=time.time(),
                key=key,
                value=value,
                ttl=ttl,
            )

            heapq.heappush(self._heap, item)
            self._index[key] = item

            if len(self._heap) > self.max_heap_size:
                await self._evict()

            return True

    async def get(self, key: str) -> Optional[T]:
        """获取项"""
        async with self._lock:
            item = self._index.get(key)
            if item is None:
                return None

            if item.ttl and (time.time() - item.timestamp) > item.ttl:
                await self._remove_item(item)
                return None

            item.hit_count += 1
            return item.value

    async def peek(self) -> Optional[CacheItem[T]]:
        """查看最高优先级项"""
        async with self._lock:
            await self._cleanup()
            if self._heap:
                return self._heap[0]
            return None

    async def pop(self) -> Optional[CacheItem[T]]:
        """弹出最高优先级项"""
        async with self._lock:
            await self._cleanup()
            if not self._heap:
                return None

            item = heapq.heappop(self._heap)
            if item.key in self._index and self._index[item.key] is item:
                del self._index[item.key]
                return item
            return None

    async def _cleanup(self) -> None:
        """清理过期项"""
        current_time = time.time()
        to_remove = []
        for item in list(self._index.values()):
            if item.ttl and (current_time - item.timestamp) > item.ttl:
                to_remove.append(item)
        for item in to_remove:
            await self._remove_item(item)

    async def _evict(self) -> None:
        """淘汰低优先级项"""
        while len(self._heap) > self.max_heap_size:
            item = heapq.heappop(self._heap)
            if item.key in self._index and self._index[item.key] is item:
                del self._index[item.key]

    async def _remove_item(self, item: CacheItem[T]) -> None:
        """移除指定项"""
        if item.key in self._index:
            del self._index[item.key]

    async def delete(self, key: str) -> bool:
        """删除项"""
        async with self._lock:
            item = self._index.pop(key, None)
            return item is not None

    async def size(self) -> int:
        """缓存大小"""
        async with self._lock:
            return len(self._index)


class AsyncMultiLevelCache(Generic[T]):
    """异步多级缓存"""

    def __init__(
        self,
        l1_max_size: int = 1000,
        l2_max_size: int = 10000,
    ):
        self.l1: LRUCache[T] = LRUCache(l1_max_size)
        self.l2: AsyncPriorityQueueCache[T] = AsyncPriorityQueueCache(l2_max_size)
        self._hits = {"l1": 0, "l2": 0, "total": 0}
        self._misses = 0
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[T]:
        """获取项"""
        async with self._lock:
            self._hits["total"] += 1

            value = self.l1.get(key)
            if value is not None:
                self._hits["l1"] += 1
                return value

            value = await self.l2.get(key)
            if value is not None:
                self._hits["l2"] += 1
                self.l1.put(key, value)
                return value

            self._misses += 1
            return None

    async def put(
        self,
        key: str,
        value: T,
        priority: int = PriorityLevel.MEDIUM,
        ttl: Optional[float] = None,
    ) -> None:
        """放入项"""
        async with self._lock:
            self.l1.put(key, value)
            await self.l2.put(key, value, priority=priority, ttl=ttl)

    async def put_high_priority(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """放入高优先级项"""
        await self.put(key, value, priority=PriorityLevel.HIGH, ttl=ttl)

    async def put_critical(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """放入关键项"""
        await self.put(key, value, priority=PriorityLevel.CRITICAL, ttl=ttl)

    async def delete(self, key: str) -> bool:
        """删除项"""
        async with self._lock:
            l1_deleted = self.l1.delete(key)
            l2_deleted = await self.l2.delete(key)
            return l1_deleted or l2_deleted

    async def get_highest_priority(self) -> Optional[CacheItem[T]]:
        """获取最高优先级项"""
        return await self.l2.peek()

    async def pop_highest_priority(self) -> Optional[CacheItem[T]]:
        """弹出最高优先级项"""
        return await self.l2.pop()

    async def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        async with self._lock:
            total = self._hits["total"]
            hit_rate = self._hits["total"] / (total + self._misses) if (total + self._misses) > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "l1_size": self.l1.max_size,
                "l2_size": await self.l2.size(),
            }

    async def clear(self) -> int:
        """清空所有缓存"""
        async with self._lock:
            l1_count = self.l1.clear()
            l2_count = self.l2._heap.clear()
            self.l2._index.clear()
            return l1_count + l2_count


# 全局缓存实例
_global_cache: Optional[MultiLevelCache[Any]] = None
_global_async_cache: Optional[AsyncMultiLevelCache[Any]] = None


def get_global_cache() -> MultiLevelCache[Any]:
    """获取全局同步缓存"""
    global _global_cache
    if _global_cache is None:
        _global_cache = MultiLevelCache()
    return _global_cache


def get_global_async_cache() -> AsyncMultiLevelCache[Any]:
    """获取全局异步缓存"""
    global _global_async_cache
    if _global_async_cache is None:
        _global_async_cache = AsyncMultiLevelCache()
    return _global_async_cache
