"""高级缓存系统 - 多级缓存优化与智能驱逐策略"""

import asyncio
import logging
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple, Union
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger("hydraflow.cache.advanced_cache")


class CacheLevel(Enum):
    """缓存级别"""
    L1 = "l1"  # 内存缓存 - 最快，容量小
    L2 = "l2"  # 本地磁盘/Redis - 较快，容量中等
    L3 = "l3"  # 分布式缓存 - 较慢，容量大


class CachePolicy(Enum):
    """缓存策略"""
    LRU = "lru"           # 最近最少使用
    LFU = "lfu"           # 最不经常使用
    ML_BASED = "ml_based" # 机器学习驱动


@dataclass
class CacheItem:
    """缓存项"""
    key: str
    value: Any
    ttl: float  # 过期时间戳
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    size: int = 0  # 字节数
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0  # 总字节数
    item_count: int = 0
    hit_rate: float = 0.0
    efficiency: float = 0.0  # L1命中率 / 总命中率


class AccessPredictor:
    """访问预测器 - 基于历史模式预测未来访问"""
    
    def __init__(self):
        self.access_patterns: Dict[str, List[float]] = {}  # key -> 访问时间戳列表
        self.predictor_model = SimplePatternPredictor()
    
    def record_access(self, key: str):
        """记录访问"""
        if key not in self.access_patterns:
            self.access_patterns[key] = []
        self.access_patterns[key].append(time.time())
        
        # 限制历史记录数量
        if len(self.access_patterns[key]) > 100:
            self.access_patterns[key] = self.access_patterns[key][-50:]
    
    def predict_next_access(self, key: str) -> float:
        """预测下一次访问的概率（0-1）"""
        if key not in self.access_patterns:
            return 0.5  # 默认50%
        
        pattern = self.access_patterns[key]
        if len(pattern) < 3:
            return 0.3  # 数据不足，预测较低
        
        return self.predictor_model.predict(pattern)


class SimplePatternPredictor:
    """简单模式预测器"""
    
    def predict(self, timestamps: List[float]) -> float:
        """基于时间间隔模式预测访问概率"""
        if len(timestamps) < 3:
            return 0.3
        
        # 计算时间间隔
        intervals = []
        for i in range(1, len(timestamps)):
            intervals.append(timestamps[i] - timestamps[i-1])
        
        # 计算平均间隔和标准差
        avg_interval = sum(intervals) / len(intervals)
        std_interval = (sum((x - avg_interval)**2 for x in intervals) / len(intervals))**0.5
        
        # 最近访问时间
        last_access = timestamps[-1]
        time_since_last = time.time() - last_access
        
        # 如果最近访问且间隔规律，预测高概率
        if time_since_last < avg_interval + std_interval:
            return min(0.9, 0.5 + (1 - time_since_last / avg_interval) * 0.4)
        else:
            return max(0.1, 0.5 - (time_since_last - avg_interval) / (avg_interval * 2) * 0.4)


class BaseCache(ABC):
    """缓存基类"""
    
    def __init__(self, max_size_bytes: int, policy: CachePolicy):
        self.max_size = max_size_bytes
        self.policy = policy
        self.items: Dict[str, CacheItem] = {}
        self.stats = CacheStats()
        self.access_predictor = AccessPredictor()
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass
    
    @abstractmethod
    async def put(self, key: str, value: Any, ttl: float = 3600.0):
        """设置缓存"""
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        """删除缓存"""
        pass
    
    @abstractmethod
    def _evict(self, count: int = 1):
        """驱逐缓存项"""
        pass
    
    def _calculate_size(self, value: Any) -> int:
        """估算值的大小（字节）"""
        if isinstance(value, bytes):
            return len(value)
        elif isinstance(value, str):
            return len(value.encode('utf-8'))
        elif isinstance(value, (int, float, bool)):
            return 64  # 近似值
        else:
            # 对于复杂对象，使用pickle估算
            import pickle
            return len(pickle.dumps(value))


class L1MemoryCache(BaseCache):
    """L1内存缓存 - 最快，容量小"""
    
    def __init__(self, max_size_mb: int = 256):
        super().__init__(max_size_mb * 1024 * 1024, CachePolicy.ML_BASED)
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        item = self.items.get(key)
        
        if item:
            # 检查过期
            if time.time() >= item.ttl:
                del self.items[key]
                self.stats.misses += 1
                return None
            
            # 更新访问信息
            item.accessed_at = time.time()
            item.access_count += 1
            self.access_predictor.record_access(key)
            
            self.stats.hits += 1
            return item.value
        
        self.stats.misses += 1
        return None
    
    async def put(self, key: str, value: Any, ttl: float = 3600.0):
        """设置缓存"""
        size = self._calculate_size(value)
        
        # 如果大小超过限制，直接不缓存
        if size > self.max_size * 0.1:  # 超过10%大小限制
            logger.debug(f"Item too large for L1 cache: {size} bytes")
            return
        
        # 确保有足够空间
        while self.stats.size + size > self.max_size:
            self._evict()
        
        item = CacheItem(
            key=key,
            value=value,
            ttl=time.time() + ttl,
            size=size
        )
        
        self.items[key] = item
        self.stats.size += size
        self.stats.item_count += 1
    
    async def delete(self, key: str):
        """删除缓存"""
        if key in self.items:
            self.stats.size -= self.items[key].size
            self.stats.item_count -= 1
            del self.items[key]
    
    def _evict(self, count: int = 1):
        """智能驱逐策略"""
        if not self.items:
            return
        
        # 使用ML预测选择驱逐目标
        candidates = []
        for key, item in self.items.items():
            # 计算驱逐分数（越高越应该被驱逐）
            # 1. 预测访问概率（越低越应该驱逐）
            predict_score = self.access_predictor.predict_next_access(key)
            
            # 2. 访问频率（越低越应该驱逐）
            freq_score = item.access_count / max(1, (time.time() - item.accessed_at) / 3600)
            
            # 3. 大小惩罚（越大越应该驱逐）
            size_penalty = item.size / self.max_size
            
            # 综合分数
            evict_score = (1 - predict_score) * 0.5 + (1 - min(freq_score / 100, 1)) * 0.3 + size_penalty * 0.2
            candidates.append((evict_score, key))
        
        # 按驱逐分数排序
        candidates.sort(reverse=True)
        
        # 驱逐分数最高的项
        for _, key in candidates[:count]:
            if key in self.items:
                self.stats.size -= self.items[key].size
                self.stats.item_count -= 1
                del self.items[key]
                self.stats.evictions += 1
                logger.debug(f"Evicted from L1: {key}")


class L2RedisCache(BaseCache):
    """L2 Redis缓存 - 较快，容量中等"""
    
    def __init__(self, max_size_mb: int = 2048):
        super().__init__(max_size_mb * 1024 * 1024, CachePolicy.LRU)
        self._client = None
    
    async def _get_client(self):
        """获取Redis客户端"""
        if self._client is None:
            try:
                import redis.asyncio as redis
                self._client = redis.Redis(host='localhost', port=6379, db=0)
            except ImportError:
                logger.warning("Redis not available, falling back to memory")
                self._fallback = {}
        
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            client = await self._get_client()
            if client:
                value = await client.get(key)
                if value:
                    self.stats.hits += 1
                    return self._deserialize(value)
            
            # Fallback
            if hasattr(self, '_fallback') and key in self._fallback:
                self.stats.hits += 1
                return self._fallback[key]
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        
        self.stats.misses += 1
        return None
    
    async def put(self, key: str, value: Any, ttl: float = 3600.0):
        """设置缓存"""
        try:
            client = await self._get_client()
            if client:
                serialized = self._serialize(value)
                await client.set(key, serialized, ex=int(ttl))
                self.stats.size += len(serialized)
                self.stats.item_count += 1
            else:
                # Fallback
                if not hasattr(self, '_fallback'):
                    self._fallback = {}
                self._fallback[key] = value
        except Exception as e:
            logger.error(f"Redis put error: {e}")
    
    async def delete(self, key: str):
        """删除缓存"""
        try:
            client = await self._get_client()
            if client:
                await client.delete(key)
            if hasattr(self, '_fallback') and key in self._fallback:
                del self._fallback[key]
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
    
    def _evict(self, count: int = 1):
        """Redis自动处理驱逐，这里留空"""
        pass
    
    def _serialize(self, value: Any) -> bytes:
        """序列化"""
        import pickle
        return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """反序列化"""
        import pickle
        return pickle.loads(value)


class L3DistributedCache(BaseCache):
    """L3分布式缓存 - 较慢，容量大"""
    
    def __init__(self, max_size_mb: int = 16384):
        super().__init__(max_size_mb * 1024 * 1024, CachePolicy.LFU)
        self._memcached_client = None
    
    async def _get_client(self):
        """获取Memcached客户端"""
        if self._memcached_client is None:
            try:
                import aiomcache
                self._memcached_client = aiomcache.Client('localhost', 11211)
            except ImportError:
                logger.warning("Memcached not available, falling back to memory")
                self._fallback = {}
        
        return self._memcached_client
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            client = await self._get_client()
            if client:
                value = await client.get(key.encode())
                if value:
                    self.stats.hits += 1
                    return self._deserialize(value)
            
            # Fallback
            if hasattr(self, '_fallback') and key in self._fallback:
                self.stats.hits += 1
                return self._fallback[key]
        except Exception as e:
            logger.error(f"Memcached get error: {e}")
        
        self.stats.misses += 1
        return None
    
    async def put(self, key: str, value: Any, ttl: float = 86400.0):
        """设置缓存（L3 TTL更长）"""
        try:
            client = await self._get_client()
            if client:
                serialized = self._serialize(value)
                await client.set(key.encode(), serialized, int(ttl))
                self.stats.size += len(serialized)
                self.stats.item_count += 1
            else:
                # Fallback
                if not hasattr(self, '_fallback'):
                    self._fallback = {}
                self._fallback[key] = value
        except Exception as e:
            logger.error(f"Memcached put error: {e}")
    
    async def delete(self, key: str):
        """删除缓存"""
        try:
            client = await self._get_client()
            if client:
                await client.delete(key.encode())
            if hasattr(self, '_fallback') and key in self._fallback:
                del self._fallback[key]
        except Exception as e:
            logger.error(f"Memcached delete error: {e}")
    
    def _evict(self, count: int = 1):
        """Memcached自动处理驱逐"""
        pass
    
    def _serialize(self, value: Any) -> bytes:
        """序列化"""
        import pickle
        return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """反序列化"""
        import pickle
        return pickle.loads(value)


class MultiLevelCacheManager:
    """多级缓存管理器"""
    
    def __init__(self, l1_size_mb: int = 256, l2_size_mb: int = 2048, l3_size_mb: int = 16384):
        self.l1 = L1MemoryCache(l1_size_mb)
        self.l2 = L2RedisCache(l2_size_mb)
        self.l3 = L3DistributedCache(l3_size_mb)
        
        self.stats = MultiLevelCacheStats()
        
        logger.info("MultiLevelCacheManager initialized")
    
    async def get(self, key: str) -> Optional[Any]:
        """从多级缓存获取数据"""
        start_time = time.time()
        
        # L1查询
        value = await self.l1.get(key)
        if value is not None:
            self.stats.l1_hits += 1
            self.stats.record_latency(CacheLevel.L1, time.time() - start_time)
            return value
        
        # L2查询
        value = await self.l2.get(key)
        if value is not None:
            self.stats.l2_hits += 1
            self.stats.record_latency(CacheLevel.L2, time.time() - start_time)
            
            # 提升到L1
            await self.l1.put(key, value)
            return value
        
        # L3查询
        value = await self.l3.get(key)
        if value is not None:
            self.stats.l3_hits += 1
            self.stats.record_latency(CacheLevel.L3, time.time() - start_time)
            
            # 提升到L2和L1
            await self.l2.put(key, value)
            await self.l1.put(key, value)
            return value
        
        self.stats.misses += 1
        return None
    
    async def put(self, key: str, value: Any, ttl: float = 3600.0, level: CacheLevel = CacheLevel.L1):
        """设置缓存到指定级别"""
        if level == CacheLevel.L1:
            await self.l1.put(key, value, ttl)
            await self.l2.put(key, value, ttl * 2)
            await self.l3.put(key, value, ttl * 4)
        elif level == CacheLevel.L2:
            await self.l2.put(key, value, ttl)
            await self.l3.put(key, value, ttl * 2)
        elif level == CacheLevel.L3:
            await self.l3.put(key, value, ttl)
        
        self.stats.puts += 1
    
    async def delete(self, key: str):
        """从所有级别删除"""
        await self.l1.delete(key)
        await self.l2.delete(key)
        await self.l3.delete(key)
        
        self.stats.deletes += 1
    
    async def warm_up(self, keys: List[str], fetch_func: Callable[[str], Any]):
        """预热缓存"""
        logger.info(f"Starting cache warm-up for {len(keys)} keys")
        
        async def warm_key(key):
            value = await fetch_func(key)
            if value is not None:
                await self.put(key, value, level=CacheLevel.L1)
        
        # 并行预热
        tasks = [warm_key(key) for key in keys]
        await asyncio.gather(*tasks)
        
        logger.info(f"Cache warm-up completed")
    
    def get_combined_stats(self) -> Dict[str, Any]:
        """获取综合统计"""
        total_hits = self.stats.l1_hits + self.stats.l2_hits + self.stats.l3_hits
        total_requests = total_hits + self.stats.misses
        
        return {
            "hits": total_hits,
            "misses": self.stats.misses,
            "hit_rate": total_hits / max(total_requests, 1),
            "l1_hit_rate": self.stats.l1_hits / max(total_requests, 1),
            "l2_hit_rate": self.stats.l2_hits / max(total_requests, 1),
            "l3_hit_rate": self.stats.l3_hits / max(total_requests, 1),
            "avg_latency_ms": self.stats.get_avg_latency() * 1000,
            "puts": self.stats.puts,
            "deletes": self.stats.deletes,
            "l1_evictions": self.l1.stats.evictions,
            "l1_size": self.l1.stats.size,
            "l1_item_count": self.l1.stats.item_count,
        }


@dataclass
class MultiLevelCacheStats:
    """多级缓存统计"""
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    misses: int = 0
    puts: int = 0
    deletes: int = 0
    
    # 延迟统计
    _latencies: List[Tuple[CacheLevel, float]] = field(default_factory=list)
    
    def record_latency(self, level: CacheLevel, latency: float):
        """记录延迟"""
        self._latencies.append((level, latency))
        # 限制记录数量
        if len(self._latencies) > 10000:
            self._latencies = self._latencies[-5000:]
    
    def get_avg_latency(self) -> float:
        """获取平均延迟"""
        if not self._latencies:
            return 0.0
        return sum(lat for _, lat in self._latencies) / len(self._latencies)


# 全局单例
_cache_manager_instance: Optional[MultiLevelCacheManager] = None


def get_multi_level_cache() -> MultiLevelCacheManager:
    """获取多级缓存管理器单例"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = MultiLevelCacheManager()
    return _cache_manager_instance


# 使用示例
async def example_usage():
    """多级缓存使用示例"""
    cache = get_multi_level_cache()
    
    # 设置缓存
    await cache.put("user:123", {"name": "John", "age": 30})
    
    # 获取缓存（第一次会miss，之后hit）
    result = await cache.get("user:123")
    print(f"Result: {result}")
    
    # 再次获取（应该命中L1）
    result = await cache.get("user:123")
    print(f"Result: {result}")
    
    # 获取统计
    stats = cache.get_combined_stats()
    print(f"Stats: {stats}")
    
    # 删除缓存
    await cache.delete("user:123")


# 辅助函数：生成缓存键
def generate_cache_key(prefix: str, *args) -> str:
    """生成唯一缓存键"""
    key_parts = [prefix] + list(args)
    key_string = ":".join(str(k) for k in key_parts)
    
    # 如果key太长，使用hash
    if len(key_string) > 250:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    return key_string
