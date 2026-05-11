"""缓存系统 - 支持TTL过期和多级缓存"""

import time
import hashlib
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger("hydraflow.cache")


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float = field(default_factory=lambda: time.time())
    ttl: int = 3600  # 默认1小时
    hits: int = 0
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > self.ttl
    
    def touch(self) -> None:
        """更新访问时间（延长TTL）"""
        self.created_at = time.time()
        self.hits += 1


class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
        }
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        entry = self._cache.get(key)
        
        if not entry:
            self._stats["misses"] += 1
            return None
        
        if entry.is_expired:
            self._remove(key)
            self._stats["misses"] += 1
            return None
        
        entry.hits += 1
        self._stats["hits"] += 1
        return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        force: bool = False
    ) -> None:
        """设置缓存值"""
        # 检查大小限制
        if len(self._cache) >= self._max_size and key not in self._cache and not force:
            self._evict()
        
        entry = CacheEntry(
            key=key,
            value=value,
            ttl=ttl or self._default_ttl,
        )
        self._cache[key] = entry
        self._stats["sets"] += 1
    
    def _remove(self, key: str) -> None:
        """移除缓存条目"""
        if key in self._cache:
            del self._cache[key]
    
    def _evict(self) -> None:
        """驱逐策略：LRU（最近最少使用）"""
        if not self._cache:
            return
        
        # 找到访问次数最少的条目
        min_hits = min(entry.hits for entry in self._cache.values())
        candidates = [k for k, v in self._cache.items() if v.hits == min_hits]
        
        if candidates:
            key_to_remove = candidates[0]
            self._remove(key_to_remove)
            self._stats["evictions"] += 1
            logger.debug(f"缓存驱逐: {key_to_remove}")
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        if key in self._cache:
            self._remove(key)
            return True
        return False
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.info("缓存已清空")
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        entry = self._cache.get(key)
        if entry and not entry.is_expired:
            return True
        if entry and entry.is_expired:
            self._remove(key)
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            **self._stats,
            "size": len(self._cache),
            "max_size": self._max_size,
            "hit_rate": self._stats["hits"] / (self._stats["hits"] + self._stats["misses"]) if (self._stats["hits"] + self._stats["misses"]) > 0 else 0.0,
        }
    
    def keys(self) -> List[str]:
        """获取所有键（过滤过期）"""
        expired = [k for k, v in self._cache.items() if v.is_expired]
        for k in expired:
            self._remove(k)
        return list(self._cache.keys())


class CacheManager:
    """缓存管理器 - 支持命名空间和缓存预热"""
    
    def __init__(self):
        self._caches: Dict[str, MemoryCache] = {}
        self._namespace_configs: Dict[str, Dict[str, Any]] = {}
    
    def get_cache(self, namespace: str = "default") -> MemoryCache:
        """获取指定命名空间的缓存"""
        if namespace not in self._caches:
            config = self._namespace_configs.get(namespace, {})
            self._caches[namespace] = MemoryCache(
                max_size=config.get("max_size", 1000),
                default_ttl=config.get("default_ttl", 3600),
            )
        return self._caches[namespace]
    
    def configure_namespace(self, namespace: str, **kwargs) -> None:
        """配置命名空间"""
        self._namespace_configs[namespace] = kwargs
        # 如果缓存已存在，重新创建
        if namespace in self._caches:
            del self._caches[namespace]
    
    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """获取缓存值"""
        return self.get_cache(namespace).get(key)
    
    def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None,
    ) -> None:
        """设置缓存值"""
        self.get_cache(namespace).set(key, value, ttl)
    
    def delete(self, key: str, namespace: str = "default") -> bool:
        """删除缓存条目"""
        return self.get_cache(namespace).delete(key)
    
    def clear_namespace(self, namespace: str = "default") -> None:
        """清空命名空间"""
        cache = self._caches.get(namespace)
        if cache:
            cache.clear()
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        self._caches.clear()
        logger.info("所有缓存已清空")
    
    def warm_up(self, namespace: str, data: Dict[str, Any]) -> None:
        """预热缓存"""
        cache = self.get_cache(namespace)
        for key, value in data.items():
            cache.set(key, value)
        logger.info(f"缓存预热完成: {namespace}, {len(data)} 条数据")
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有命名空间的统计"""
        stats = {}
        for namespace, cache in self._caches.items():
            stats[namespace] = cache.get_stats()
        return stats


# 缓存装饰器
def cached(namespace: str = "default", ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in kwargs.items())
            key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            cache_manager = get_cache_manager()
            cached_value = cache_manager.get(key, namespace)
            
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache_manager.set(key, result, namespace, ttl)
            return result
        return wrapper
    return decorator


# 全局单例
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
