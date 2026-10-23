"""缓存模块。

注意：本模块存在两套多级缓存实现，用途不同，请勿混用：

* ``MultiLevelCache``（来自 priority_queue）— 纯内存，LRU + 优先级队列，
  无外部依赖，是本包的默认实现。
* ``BackendMultiLevelCache``（来自 multi_level 的 MultiLevelCache）—
  基于 ``CacheBackend`` 抽象，L1 内存 + L2 可插拔（支持 Redis），
  适合需要跨进程共享缓存的场景。

之所以在导出时给后者加别名，是因为两者原名相同，
直接从子模块导入极易拿错实现。
"""

from .manager import CacheManager, MemoryCache, get_cache_manager, cached

from .priority_queue import (
    PriorityLevel,
    CacheItem,
    LRUCache,
    PriorityQueueCache,
    MultiLevelCache,
    AsyncPriorityQueueCache,
    AsyncMultiLevelCache,
    get_global_cache,
    get_global_async_cache,
)

from .multi_level import (
    CacheBackend,
    MemoryL1Cache,
    RedisL2Cache,
    CacheKeyBuilder,
    AsyncBatchCache,
    get_multilevel_cache,
)
from .multi_level import MultiLevelCache as BackendMultiLevelCache

__all__ = [
    # 基础缓存
    "CacheManager",
    "MemoryCache",
    "get_cache_manager",
    "cached",
    # 优先级队列实现（默认）
    "PriorityLevel",
    "CacheItem",
    "LRUCache",
    "PriorityQueueCache",
    "MultiLevelCache",
    "AsyncPriorityQueueCache",
    "AsyncMultiLevelCache",
    "get_global_cache",
    "get_global_async_cache",
    # 可插拔后端实现
    "CacheBackend",
    "MemoryL1Cache",
    "RedisL2Cache",
    "BackendMultiLevelCache",
    "CacheKeyBuilder",
    "AsyncBatchCache",
    "get_multilevel_cache",
]
