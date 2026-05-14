"""数据库分片管理器 - 设计阶段，暂不实施"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import hashlib

logger = logging.getLogger("hydraflow.database.sharding")


class ShardingStrategy(Enum):
    """分片策略"""
    HASH = "hash"              # 哈希分片
    RANGE = "range"           # 范围分片
    GEO = "geo"               # 地理位置分片
    TIME = "time"             # 时间分片
    CONSISTENT_HASH = "consistent_hash"  # 一致性哈希


@dataclass
class ShardKey:
    """分片键"""
    field: str
    strategy: ShardingStrategy
    config: Dict[str, Any]  # 策略特定配置


@dataclass
class Shard:
    """分片信息"""
    shard_id: str
    host: str
    port: int
    database: str
    weight: int = 1  # 权重（用于负载均衡）
    is_active: bool = True
    metadata: Dict[str, Any] = None


@dataclass
class ShardConfig:
    """分片配置"""
    strategy: ShardingStrategy
    num_shards: int
    shard_key: ShardKey
    shards: List[Shard]
    replication_factor: int = 1  # 副本数
    failover_enabled: bool = True


class ShardManager:
    """分片管理器

    设计阶段，暂不实施。
    将在P3阶段根据实际数据量和性能需求实施。
    """

    def __init__(self, config: ShardConfig):
        self.config = config
        self.shards = {s.shard_id: s for s in config.shards}
        self.ring: List[tuple] = []  # 用于一致性哈希环

        if config.strategy == ShardingStrategy.CONSISTENT_HASH:
            self._build_hash_ring()

    def _build_hash_ring(self):
        """构建一致性哈希环"""
        for shard in self.shards.values():
            for i in range(shard.weight * 100):  # 虚拟节点
                key = f"{shard.shard_id}:{i}"
                hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
                self.ring.append((hash_value, shard.shard_id))

        self.ring.sort(key=lambda x: x[0])

    def get_shard_for_key(self, key_value: str) -> Optional[Shard]:
        """根据键值获取分片"""
        strategy = self.config.strategy

        if strategy == ShardingStrategy.HASH:
            return self._hash_shard(key_value)
        elif strategy == ShardingStrategy.RANGE:
            return self._range_shard(key_value)
        elif strategy == ShardingStrategy.CONSISTENT_HASH:
            return self._consistent_hash_shard(key_value)
        elif strategy == ShardingStrategy.TIME:
            return self._time_shard(key_value)
        elif strategy == ShardingStrategy.GEO:
            return self._geo_shard(key_value)

        return None

    def _hash_shard(self, key_value: str) -> Optional[Shard]:
        """哈希分片"""
        hash_value = int(hashlib.md5(key_value.encode()).hexdigest(), 16)
        shard_index = hash_value % self.config.num_shards

        shard_id = f"shard_{shard_index}"
        return self.shards.get(shard_id)

    def _range_shard(self, key_value: str) -> Optional[Shard]:
        """范围分片"""
        # 假设key_value是数值或可以转换为数值
        try:
            numeric_value = float(key_value)
            shard_index = int(numeric_value / self.config.shard_key.config.get("range_size", 1000))
            shard_id = f"shard_{shard_index % self.config.num_shards}"
            return self.shards.get(shard_id)
        except ValueError:
            return self._hash_shard(key_value)

    def _consistent_hash_shard(self, key_value: str) -> Optional[Shard]:
        """一致性哈希分片"""
        if not self.ring:
            return None

        hash_value = int(hashlib.md5(key_value.encode()).hexdigest(), 16)

        # 二分查找第一个 >= hash_value 的节点
        left, right = 0, len(self.ring) - 1
        while left < right:
            mid = (left + right) // 2
            if self.ring[mid][0] < hash_value:
                left = mid + 1
            else:
                right = mid

        if left == len(self.ring):
            shard_id = self.ring[0][1]
        else:
            shard_id = self.ring[left][1]

        return self.shards.get(shard_id)

    def _time_shard(self, key_value: str) -> Optional[Shard]:
        """时间分片"""
        from datetime import datetime

        try:
            if isinstance(key_value, str):
                dt = datetime.fromisoformat(key_value)
            else:
                dt = datetime.fromtimestamp(float(key_value))

            shard_index = (dt.year - 2024) * 12 + dt.month
            shard_id = f"shard_{shard_index % self.config.num_shards}"
            return self.shards.get(shard_id)
        except (ValueError, TypeError):
            return self._hash_shard(key_value)

    def _geo_shard(self, key_value: str) -> Optional[Shard]:
        """地理位置分片"""
        # 简化的地理分片：按区域划分
        geo_regions = self.config.shard_key.config.get("regions", ["us", "eu", "asia"])

        try:
            region = key_value.lower()
            if region in geo_regions:
                shard_index = geo_regions.index(region)
                shard_id = f"shard_{shard_index}"
                return self.shards.get(shard_id)
        except (ValueError, AttributeError):
            pass

        return self._hash_shard(key_value)

    def add_shard(self, shard: Shard) -> bool:
        """添加分片"""
        if shard.shard_id in self.shards:
            logger.warning(f"Shard {shard.shard_id} already exists")
            return False

        self.shards[shard.shard_id] = shard

        if self.config.strategy == ShardingStrategy.CONSISTENT_HASH:
            self._build_hash_ring()

        logger.info(f"Added shard: {shard.shard_id}")
        return True

    def remove_shard(self, shard_id: str) -> bool:
        """移除分片"""
        if shard_id not in self.shards:
            logger.warning(f"Shard {shard_id} not found")
            return False

        del self.shards[shard_id]

        if self.config.strategy == ShardingStrategy.CONSISTENT_HASH:
            self._build_hash_ring()

        logger.info(f"Removed shard: {shard_id}")
        return True

    def get_shard_stats(self) -> Dict[str, Any]:
        """获取分片统计"""
        return {
            "total_shards": len(self.shards),
            "active_shards": sum(1 for s in self.shards.values() if s.is_active),
            "strategy": self.config.strategy.value,
            "shards": {
                shard_id: {
                    "host": shard.host,
                    "port": shard.port,
                    "is_active": shard.is_active,
                    "weight": shard.weight,
                }
                for shard_id, shard in self.shards.items()
            },
        }


class ShardRouter:
    """分片路由 - 根据分片管理器路由查询"""

    def __init__(self, shard_manager: ShardManager):
        self.shard_manager = shard_manager

    def route_query(
        self,
        table: str,
        operation: str,
        shard_key_value: Optional[str] = None
    ) -> List[Shard]:
        """路由查询

        Args:
            table: 表名
            operation: 操作类型 (read, write, read_write)
            shard_key_value: 分片键值

        Returns:
            需要查询的分片列表
        """
        if operation == "read":
            return self._route_read(table, shard_key_value)
        elif operation == "write":
            return self._route_write(table, shard_key_value)
        else:  # read_write
            return self._route_read_write(table, shard_key_value)

    def _route_read(
        self,
        table: str,
        shard_key_value: Optional[str] = None
    ) -> List[Shard]:
        """路由读操作"""
        if shard_key_value:
            shard = self.shard_manager.get_shard_for_key(shard_key_value)
            return [shard] if shard else []
        else:
            # 全表扫描，路由到所有分片
            return [s for s in self.shard_manager.shards.values() if s.is_active]

    def _route_write(
        self,
        table: str,
        shard_key_value: Optional[str] = None
    ) -> List[Shard]:
        """路由写操作"""
        if not shard_key_value:
            raise ValueError("Shard key required for write operations")

        shard = self.shard_manager.get_shard_for_key(shard_key_value)
        return [shard] if shard else []

    def _route_read_write(
        self,
        table: str,
        shard_key_value: Optional[str] = None
    ) -> List[Shard]:
        """路由读写操作"""
        return self._route_write(table, shard_key_value)


def get_default_shard_config() -> ShardConfig:
    """获取默认分片配置（设计参考）

    实际实施时需要根据数据量和性能需求调整
    """
    shards = [
        Shard(shard_id=f"shard_{i}", host=f"db-host-{i}", port=5432, database=f"hydraflow_{i}")
        for i in range(4)
    ]

    return ShardConfig(
        strategy=ShardingStrategy.CONSISTENT_HASH,
        num_shards=4,
        shard_key=ShardKey(
            field="user_id",
            strategy=ShardingStrategy.CONSISTENT_HASH,
            config={"virtual_nodes": 100}
        ),
        shards=shards,
        replication_factor=2,
        failover_enabled=True,
    )
