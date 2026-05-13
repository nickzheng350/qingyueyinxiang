"""数据库读写分离 - 主从复制架构"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod
import threading
import random

logger = logging.getLogger("hydraflow.read_write_split")


class QueryType(Enum):
    """查询类型"""
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"


@dataclass
class DatabaseReplica:
    """数据库副本"""
    replica_id: str
    host: str
    port: int
    database: str
    is_master: bool = False
    is_active: bool = True
    weight: int = 1  # 用于负载均衡权重
    latency_ms: float = 0.0
    current_load: int = 0  # 当前连接数
    last_health_check: float = field(default_factory=time.time)
    health_status: str = "healthy"


@dataclass
class ReplicaStats:
    """副本统计"""
    replica_id: str
    queries_executed: int = 0
    queries_failed: int = 0
    avg_latency_ms: float = 0.0
    last_query_time: Optional[float] = None


class ReplicaSelector:
    """副本选择器"""

    def __init__(self, strategy: str = "least_load"):
        self.strategy = strategy

    def select(self, replicas: List[DatabaseReplica], query_type: QueryType) -> Optional[DatabaseReplica]:
        """选择最佳副本"""
        if query_type == QueryType.WRITE:
            # 写操作只能选择主库
            masters = [r for r in replicas if r.is_master and r.is_active]
            return masters[0] if masters else None
        else:
            # 读操作选择从库
            active_replicas = [r for r in replicas if not r.is_master and r.is_active]

            if not active_replicas:
                # 没有从库，回退到主库
                masters = [r for r in replicas if r.is_master and r.is_active]
                return masters[0] if masters else None

            if self.strategy == "least_load":
                return min(active_replicas, key=lambda r: r.current_load)
            elif self.strategy == "weighted_random":
                return self._weighted_random_select(active_replicas)
            elif self.strategy == "round_robin":
                return self._round_robin_select(active_replicas)
            elif self.strategy == "lowest_latency":
                return min(active_replicas, key=lambda r: r.latency_ms)
            else:
                return random.choice(active_replicas)

    def _weighted_random_select(self, replicas: List[DatabaseReplica]) -> DatabaseReplica:
        """加权随机选择"""
        total_weight = sum(r.weight for r in replicas)
        rand_val = random.uniform(0, total_weight)
        cumulative = 0
        for replica in replicas:
            cumulative += replica.weight
            if rand_val <= cumulative:
                return replica
        return replicas[-1]

    def _round_robin_select(self, replicas: List[DatabaseReplica]) -> DatabaseReplica:
        """轮询选择（简化版）"""
        return replicas[int(time.time() * 1000) % len(replicas)]


class ReadWriteSplitter:
    """读写分离管理器"""

    def __init__(self):
        self.replicas: Dict[str, DatabaseReplica] = {}
        self.replica_stats: Dict[str, ReplicaStats] = {}
        self.selector = ReplicaSelector(strategy="least_load")
        self._lock = threading.RLock()

        # 事务亲和性：一个事务内的所有操作应该路由到同一个副本
        self._transaction_affinity: Dict[str, str] = {}  # transaction_id -> replica_id
        self._transaction_queries: Dict[str, List[str]] = {}  # transaction_id -> query_list

        # 健康检查配置
        self.health_check_interval = 30.0  # 秒
        self.health_check_task = None

        logger.info("ReadWriteSplitter initialized")

    def add_replica(self, replica: DatabaseReplica):
        """添加副本"""
        with self._lock:
            self.replicas[replica.replica_id] = replica
            self.replica_stats[replica.replica_id] = ReplicaStats(replica_id=replica.replica_id)
            logger.info(f"Added replica: {replica.replica_id} (master={replica.is_master})")

    def remove_replica(self, replica_id: str):
        """移除副本"""
        with self._lock:
            if replica_id in self.replicas:
                del self.replicas[replica_id]
                del self.replica_stats[replica_id]
                logger.info(f"Removed replica: {replica_id}")

    def start_transaction(self, transaction_id: str, query_type: QueryType) -> Optional[DatabaseReplica]:
        """开启事务 - 确定路由目标"""
        replica = self.selector.select(list(self.replicas.values()), query_type)
        if replica:
            self._transaction_affinity[transaction_id] = replica.replica_id
            self._transaction_queries[transaction_id] = []
            logger.debug(f"Transaction {transaction_id} started on {replica.replica_id}")
        return replica

    def get_replica_for_query(
        self,
        transaction_id: Optional[str],
        query_type: QueryType
    ) -> Optional[DatabaseReplica]:
        """获取查询对应的副本"""
        with self._lock:
            # 如果有事务亲和性，优先使用事务的副本
            if transaction_id and transaction_id in self._transaction_affinity:
                replica_id = self._transaction_affinity[transaction_id]
                if replica_id in self.replicas:
                    return self.replicas[replica_id]

            return self.selector.select(list(self.replicas.values()), query_type)

    def end_transaction(self, transaction_id: str):
        """结束事务"""
        with self._lock:
            if transaction_id in self._transaction_affinity:
                del self._transaction_affinity[transaction_id]
            if transaction_id in self._transaction_queries:
                del self._transaction_queries[transaction_id]
            logger.debug(f"Transaction {transaction_id} ended")

    def record_query(
        self,
        replica_id: str,
        query_type: QueryType,
        latency_ms: float,
        success: bool
    ):
        """记录查询统计"""
        with self._lock:
            if replica_id not in self.replica_stats:
                return

            stats = self.replica_stats[replica_id]
            stats.queries_executed += 1
            if not success:
                stats.queries_failed += 1

            # 更新平均延迟
            stats.avg_latency_ms = (
                (stats.avg_latency_ms * (stats.queries_executed - 1) + latency_ms)
                / stats.queries_executed
            )
            stats.last_query_time = time.time()

            # 更新副本延迟和负载
            if replica_id in self.replicas:
                self.replicas[replica_id].latency_ms = latency_ms
                if success:
                    self.replicas[replica_id].current_load = max(0, self.replicas[replica_id].current_load - 1)
                else:
                    self.replicas[replica_id].current_load += 1

    async def health_check(self):
        """健康检查"""
        while True:
            await asyncio.sleep(self.health_check_interval)

            with self._lock:
                for replica in self.replicas.values():
                    try:
                        # 简化：模拟健康检查
                        is_healthy = await self._check_replica_health(replica)

                        replica.is_active = is_healthy
                        replica.last_health_check = time.time()
                        replica.health_status = "healthy" if is_healthy else "unhealthy"

                        if not is_healthy:
                            logger.warning(f"Replica {replica.replica_id} is unhealthy")

                    except Exception as e:
                        replica.is_active = False
                        replica.health_status = f"error: {str(e)}"
                        logger.error(f"Health check failed for {replica.replica_id}: {e}")

    async def _check_replica_health(self, replica: DatabaseReplica) -> bool:
        """检查副本健康状态"""
        # 简化实现：模拟ping
        await asyncio.sleep(0.01)
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "total_replicas": len(self.replicas),
                "active_replicas": sum(1 for r in self.replicas.values() if r.is_active),
                "master_count": sum(1 for r in self.replicas.values() if r.is_master),
                "replicas": {
                    rid: {
                        "is_master": r.is_master,
                        "is_active": r.is_active,
                        "latency_ms": r.latency_ms,
                        "current_load": r.current_load,
                        "health_status": r.health_status,
                    }
                    for rid, r in self.replicas.items()
                },
                "stats": {
                    rid: {
                        "queries_executed": s.queries_executed,
                        "queries_failed": s.queries_failed,
                        "avg_latency_ms": s.avg_latency_ms,
                    }
                    for rid, s in self.replica_stats.items()
                },
            }

    def get_read_replica_stats(self) -> Dict[str, float]:
        """获取读副本负载情况"""
        with self._lock:
            read_replicas = [r for r in self.replicas.values() if not r.is_master and r.is_active]
            if not read_replicas:
                return {"avg_load": 0, "min_load": 0, "max_load": 0}

            loads = [r.current_load for r in read_replicas]
            return {
                "avg_load": sum(loads) / len(loads),
                "min_load": min(loads),
                "max_load": max(loads),
            }


# 全局单例
_splitter_instance: Optional[ReadWriteSplitter] = None


def get_read_write_splitter() -> ReadWriteSplitter:
    """获取读写分离器单例"""
    global _splitter_instance
    if _splitter_instance is None:
        _splitter_instance = ReadWriteSplitter()
    return _splitter_instance
