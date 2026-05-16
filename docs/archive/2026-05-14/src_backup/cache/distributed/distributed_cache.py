"""分布式缓存 - 支持多节点缓存同步"""
import asyncio
import logging
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod
import threading

logger = logging.getLogger("hydraflow.distributed_cache")


class CacheConsistency(Enum):
    """缓存一致性策略"""
    STRONG = "strong"       # 强一致性
    EVENTUAL = "eventual"   # 最终一致性
    CAUSAL = "causal"       # 因果一致性


@dataclass
class CacheNode:
    """缓存节点"""
    node_id: str
    host: str
    port: int
    weight: int = 1
    is_local: bool = False
    is_active: bool = True
    last_heartbeat: float = field(default_factory=time.time)
    current_items: int = 0
    memory_used_mb: float = 0.0


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    version: int = 1
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    source_node: Optional[str] = None


class DistributedCacheManager:
    """分布式缓存管理器"""

    def __init__(
        self,
        node_id: str,
        consistency: CacheConsistency = CacheConsistency.EVENTUAL,
        replication_factor: int = 2
    ):
        self.node_id = node_id
        self.consistency = consistency
        self.replication_factor = replication_factor

        self.nodes: Dict[str, CacheNode] = {}
        self.local_cache: Dict[str, CacheEntry] = {}
        self.version_map: Dict[str, int] = {}  # key -> version

        self.hits = 0
        self.misses = 0
        self.network_errors = 0

        self._lock = threading.RLock()
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(f"DistributedCacheManager initialized (node={node_id})")

    def add_node(self, node: CacheNode):
        """添加节点"""
        with self._lock:
            self.nodes[node.node_id] = node
            logger.info(f"Added cache node: {node.node_id}")

    def remove_node(self, node_id: str):
        """移除节点"""
        with self._lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
                logger.info(f"Removed cache node: {node_id}")

    def _get_nodes_for_key(self, key: str, count: int = None) -> List[CacheNode]:
        """根据key获取负责的节点"""
        with self._lock:
            active_nodes = [n for n in self.nodes.values() if n.is_active]

            if not active_nodes:
                return []

            count = count or self.replication_factor

            hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
            nodes = []

            for i in range(count):
                index = (hash_value + i) % len(active_nodes)
                nodes.append(active_nodes[index])

            return nodes

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            entry = self.local_cache.get(key)

            if entry:
                if entry.expires_at and time.time() > entry.expires_at:
                    del self.local_cache[key]
                    self.misses += 1
                    return None

                self.hits += 1
                return entry.value

            self.misses += 1

        if self.consistency == CacheConsistency.EVENTUAL:
            entry = await self._fetch_from_replicas(key)
            if entry:
                with self._lock:
                    self.local_cache[key] = entry
                return entry.value

        return None

    async def _fetch_from_replicas(self, key: str) -> Optional[CacheEntry]:
        """从副本节点获取"""
        nodes = self._get_nodes_for_key(key)

        for node in nodes:
            if node.is_local:
                continue

            try:
                entry = await self._fetch_from_node(node, key)
                if entry:
                    return entry
            except Exception as e:
                logger.warning(f"Failed to fetch from {node.node_id}: {e}")
                self.network_errors += 1

        return None

    async def _fetch_from_node(self, node: CacheNode, key: str) -> Optional[CacheEntry]:
        """从指定节点获取（简化实现）"""
        await asyncio.sleep(0.01)
        return None

    async def put(
        self,
        key: str,
        value: Any,
        ttl: float = 3600.0,
        replicate: bool = True
    ):
        """设置缓存"""
        entry = CacheEntry(
            key=key,
            value=value,
            version=self.version_map.get(key, 0) + 1,
            expires_at=time.time() + ttl if ttl > 0 else None,
            source_node=self.node_id,
        )

        with self._lock:
            self.local_cache[key] = entry
            self.version_map[key] = entry.version

        if replicate and self.consistency == CacheConsistency.EVENTUAL:
            asyncio.create_task(self._replicate_to_nodes(key, entry))

    async def _replicate_to_nodes(self, key: str, entry: CacheEntry):
        """复制到其他节点"""
        nodes = self._get_nodes_for_key(key)

        replication_tasks = []
        for node in nodes:
            if node.is_local:
                continue

            replication_tasks.append(self._replicate_to_node(node, key, entry))

        if replication_tasks:
            await asyncio.gather(*replication_tasks, return_exceptions=True)

    async def _replicate_to_node(self, node: CacheNode, key: str, entry: CacheEntry):
        """复制到指定节点（简化实现）"""
        try:
            await asyncio.sleep(0.01)
        except Exception as e:
            logger.warning(f"Failed to replicate to {node.node_id}: {e}")
            self.network_errors += 1

    async def delete(self, key: str, replicate: bool = True):
        """删除缓存"""
        with self._lock:
            if key in self.local_cache:
                del self.local_cache[key]
            if key in self.version_map:
                del self.version_map[key]

        if replicate and self.consistency == CacheConsistency.EVENTUAL:
            asyncio.create_task(self._delete_from_replicas(key))

    async def _delete_from_replicas(self, key: str):
        """从副本节点删除"""
        nodes = self._get_nodes_for_key(key)

        delete_tasks = []
        for node in nodes:
            if node.is_local:
                continue
            delete_tasks.append(self._delete_from_node(node, key))

        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)

    async def _delete_from_node(self, node: CacheNode, key: str):
        """从指定节点删除（简化实现）"""
        try:
            await asyncio.sleep(0.01)
        except Exception as e:
            logger.warning(f"Failed to delete from {node.node_id}: {e}")

    async def invalidate_local(self, pattern: str = None):
        """使本地缓存失效"""
        with self._lock:
            if pattern:
                keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.local_cache[key]
            else:
                self.local_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        with self._lock:
            total_hits = self.hits + self.misses
            hit_rate = self.hits / total_hits if total_hits > 0 else 0

            return {
                "node_id": self.node_id,
                "local_cache_size": len(self.local_cache),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "network_errors": self.network_errors,
                "total_nodes": len(self.nodes),
                "active_nodes": sum(1 for n in self.nodes.values() if n.is_active),
                "consistency": self.consistency.value,
                "replication_factor": self.replication_factor,
            }

    async def start_sync(self):
        """启动同步任务"""
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Cache sync started")

    async def stop_sync(self):
        """停止同步任务"""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
        logger.info("Cache sync stopped")

    async def _sync_loop(self):
        """同步循环"""
        while self._running:
            try:
                await asyncio.sleep(30.0)

                with self._lock:
                    current_time = time.time()
                    for node in self.nodes.values():
                        if current_time - node.last_heartbeat > 60.0:
                            node.is_active = False
                            logger.warning(f"Node {node.node_id} marked as inactive")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync error: {e}")


# 全局管理器
_cache_managers: Dict[str, DistributedCacheManager] = {}


def get_distributed_cache(node_id: str = "default") -> DistributedCacheManager:
    """获取分布式缓存管理器"""
    if node_id not in _cache_managers:
        _cache_managers[node_id] = DistributedCacheManager(node_id=node_id)
    return _cache_managers[node_id]
