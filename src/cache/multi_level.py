"""HydraFlow AI 多级缓存系统 - 支持内存/L1 + Redis/L2 缓存"""

import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional, Generic, TypeVar
from contextlib import asynccontextmanager

from src.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("hydraflow.cache.advanced")

T = TypeVar("T")


class CacheBackend(ABC):
    """缓存后端抽象基类"""

    @abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        """获取缓存值"""
        pass

    @abstractmethod
    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""
        pass


class MemoryL1Cache(CacheBackend):
    """L1 内存缓存 - 基于 LRU"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache: OrderedDict[str, tuple[bytes, float]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[bytes]:
        async with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                return None

            self._cache.move_to_end(key)
            return value

    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> None:
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    self._cache.popitem(last=False)

            ttl_val = ttl or self._default_ttl
            self._cache[key] = (value, time.time() + ttl_val)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        async with self._lock:
            if key not in self._cache:
                return False
            _, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                return False
            return True

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()


class RedisL2Cache(CacheBackend):
    """L2 Redis 缓存"""

    def __init__(self, redis_url: Optional[str] = None, key_prefix: str = "hydraflow:"):
        self._redis_url = redis_url or settings.redis.url
        self._key_prefix = key_prefix
        self._client: Optional[Any] = None
        self._lock = asyncio.Lock()

    async def _get_client(self):
        """获取或创建 Redis 客户端"""
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    try:
                        import redis.asyncio as aioredis
                        self._client = await aioredis.from_url(
                            self._redis_url,
                            encoding="utf-8",
                            decode_responses=False,
                        )
                    except ImportError:
                        logger.warning("Redis 不可用，缓存将仅使用 L1")
                        return None
        return self._client

    async def get(self, key: str) -> Optional[bytes]:
        client = await self._get_client()
        if not client:
            return None

        full_key = f"{self._key_prefix}{key}"
        try:
            value = await client.get(full_key)
            return value
        except Exception as e:
            logger.warning(f"Redis GET 失败: {e}")
            return None

    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> None:
        client = await self._get_client()
        if not client:
            return

        full_key = f"{self._key_prefix}{key}"
        try:
            if ttl:
                await client.setex(full_key, ttl, value)
            else:
                await client.set(full_key, value)
        except Exception as e:
            logger.warning(f"Redis SET 失败: {e}")

    async def delete(self, key: str) -> bool:
        client = await self._get_client()
        if not client:
            return False

        full_key = f"{self._key_prefix}{key}"
        try:
            result = await client.delete(full_key)
            return result > 0
        except Exception as e:
            logger.warning(f"Redis DELETE 失败: {e}")
            return False

    async def exists(self, key: str) -> bool:
        client = await self._get_client()
        if not client:
            return False

        full_key = f"{self._key_prefix}{key}"
        try:
            return await client.exists(full_key) > 0
        except Exception as e:
            logger.warning(f"Redis EXISTS 失败: {e}")
            return False

    async def clear(self) -> None:
        client = await self._get_client()
        if not client:
            return

        try:
            pattern = f"{self._key_prefix}*"
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                if keys:
                    await client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Redis CLEAR 失败: {e}")

    async def close(self) -> None:
        if self._client:
            await self._client.close()


class MultiLevelCache:
    """多级缓存 - L1(内存) + L2(Redis)"""

    def __init__(
        self,
        l1_size: int = 1000,
        l1_ttl: int = 300,
        l2_ttl: int = 3600,
        enable_l2: bool = True,
    ):
        self._l1 = MemoryL1Cache(max_size=l1_size, default_ttl=l1_ttl)
        self._l2 = RedisL2Cache() if enable_l2 else None
        self._l2_ttl = l2_ttl
        self._stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "sets": 0,
        }
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值 - 先查 L1，再查 L2"""
        l1_value = await self._l1.get(key)
        if l1_value:
            self._stats["l1_hits"] += 1
            try:
                return json.loads(l1_value.decode("utf-8"))
            except Exception:
                return l1_value

        if self._l2:
            l2_value = await self._l2.get(key)
            if l2_value:
                self._stats["l2_hits"] += 1
                try:
                    value = json.loads(l2_value.decode("utf-8"))
                    await self._l1.set(key, l2_value, ttl=self._l2_ttl // 2)
                    return value
                except Exception:
                    return l2_value

        self._stats["misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值 - 同时写入 L1 和 L2"""
        try:
            serialized = json.dumps(value).encode("utf-8")
        except (TypeError, ValueError):
            serialized = str(value).encode("utf-8")

        ttl_val = ttl or self._l2_ttl

        await self._l1.set(key, serialized, ttl=ttl_val // 4)

        if self._l2:
            await self._l2.set(key, serialized, ttl=ttl_val)

        self._stats["sets"] += 1

    async def delete(self, key: str) -> None:
        """删除缓存"""
        await self._l1.delete(key)
        if self._l2:
            await self._l2.delete(key)

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if await self._l1.exists(key):
            return True
        if self._l2:
            return await self._l2.exists(key)
        return False

    async def clear(self) -> None:
        """清空缓存"""
        await self._l1.clear()
        if self._l2:
            await self._l2.clear()

    def get_stats(self) -> dict:
        """获取缓存统计"""
        total = self._stats["l1_hits"] + self._stats["l2_hits"] + self._stats["misses"]
        hit_rate = 0.0
        if total > 0:
            hit_rate = (self._stats["l1_hits"] + self._stats["l2_hits"]) / total

        return {
            "l1_hits": self._stats["l1_hits"],
            "l2_hits": self._stats["l2_hits"],
            "misses": self._stats["misses"],
            "total_requests": total,
            "hit_rate": round(hit_rate * 100, 2),
            "l1_hit_rate": self._stats["l1_hits"] / max(1, self._stats["l1_hits"] + self._stats["misses"]) * 100,
            "l2_hit_rate": self._stats["l2_hits"] / max(1, self._stats["l2_hits"] + self._stats["misses"]) * 100,
            "sets": self._stats["sets"],
        }

    def reset_stats(self) -> None:
        """重置统计"""
        self._stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "sets": 0,
        }


class CacheKeyBuilder:
    """缓存键构建器"""

    @staticmethod
    def build(*parts: Any, separator: str = ":") -> str:
        """构建缓存键"""
        str_parts = []
        for part in parts:
            if part is None:
                str_parts.append("null")
            elif isinstance(part, (list, dict)):
                str_parts.append(hashlib.md5(json.dumps(part, sort_keys=True).encode()).hexdigest()[:8])
            else:
                str_parts.append(str(part))
        return separator.join(str_parts)

    @staticmethod
    def build_with_prefix(prefix: str, *parts: Any) -> str:
        """构建带前缀的缓存键"""
        return CacheKeyBuilder.build(prefix, *parts, separator=":")


class AsyncBatchCache:
    """异步批量缓存 - 合并多个缓存请求"""

    def __init__(self, cache: MultiLevelCache, batch_size: int = 10, wait_time: float = 0.05):
        self._cache = cache
        self._batch_size = batch_size
        self._wait_time = wait_time
        self._pending: dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """异步获取缓存，自动批量合并"""
        async with self._lock:
            if key not in self._pending:
                self._pending[key] = asyncio.get_event_loop().create_future()
            future = self._pending[key]

        return await future

    async def _fetch_from_cache(self, key: str) -> Any:
        """从缓存获取"""
        return await self._cache.get(key)

    async def _batch_fetch(self, keys: list[str]) -> dict[str, Any]:
        """批量获取"""
        results = {}
        for key in keys:
            value = await self._cache.get(key)
            if value is not None:
                results[key] = value
        return results

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        await self._cache.set(key, value, ttl)


_multilevel_cache_instance: Optional[MultiLevelCache] = None


def get_multilevel_cache() -> MultiLevelCache:
    """获取多级缓存实例"""
    global _multilevel_cache_instance
    if _multilevel_cache_instance is None:
        _multilevel_cache_instance = MultiLevelCache(
            l1_size=1000,
            l1_ttl=300,
            l2_ttl=3600,
            enable_l2=True,
        )
    return _multilevel_cache_instance
