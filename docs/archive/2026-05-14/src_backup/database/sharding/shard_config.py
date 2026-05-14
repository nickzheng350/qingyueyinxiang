"""数据库分片配置"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum

from .shard_manager import Shard, ShardConfig, ShardingStrategy, ShardKey, get_default_shard_config


class TableShardingStrategy(Enum):
    """表级分片策略"""
    SINGLE_TABLE = "single_table"      # 单表
    VERTICAL = "vertical"             # 垂直分表
    HORIZONTAL = "horizontal"         # 水平分表


@dataclass
class TableShardConfig:
    """表分片配置"""
    table_name: str
    strategy: TableShardingStrategy
    shard_key: Optional[str] = None
    shard_strategy: Optional[ShardingStrategy] = None
    num_shards: int = 1
    columns: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatabaseShardingPlan:
    """数据库分片计划"""
    plan_id: str
    description: str
    estimated_data_size_gb: float
    estimated_qps: int
    recommended_num_shards: int
    recommended_strategy: ShardingStrategy
    table_configs: List[TableShardConfig]
    migration_steps: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


# 常用表的分片策略配置
DEFAULT_TABLE_CONFIGS: Dict[str, TableShardConfig] = {
    "users": TableShardConfig(
        table_name="users",
        strategy=TableShardingStrategy.SINGLE_TABLE,
        shard_key="user_id",
        shard_strategy=ShardingStrategy.CONSISTENT_HASH,
        num_shards=4,
        indexes=["email", "created_at"],
    ),
    "tasks": TableShardConfig(
        table_name="tasks",
        strategy=TableShardingStrategy.HORIZONTAL,
        shard_key="user_id",
        shard_strategy=ShardingStrategy.RANGE,
        num_shards=8,
        indexes=["status", "created_at", "priority"],
    ),
    "projects": TableShardConfig(
        table_name="projects",
        strategy=TableShardingStrategy.HORIZONTAL,
        shard_key="user_id",
        shard_strategy=ShardingStrategy.HASH,
        num_shards=4,
        indexes=["status", "created_at"],
    ),
    "assets": TableShardConfig(
        table_name="assets",
        strategy=TableShardingStrategy.HORIZONTAL,
        shard_key="project_id",
        shard_strategy=ShardingStrategy.HASH,
        num_shards=16,
        indexes=["asset_type", "created_at"],
    ),
    "audit_logs": TableShardConfig(
        table_name="audit_logs",
        strategy=TableShardingStrategy.HORIZONTAL,
        shard_key="user_id",
        shard_strategy=ShardingStrategy.TIME,
        num_shards=12,  # 按月分片
        indexes=["action", "timestamp"],
    ),
}


def get_table_config(table_name: str) -> Optional[TableShardConfig]:
    """获取表分片配置"""
    return DEFAULT_TABLE_CONFIGS.get(table_name)


def generate_sharding_plan(
    estimated_data_size_gb: float,
    estimated_qps: int,
    table_access_patterns: Dict[str, Dict[str, float]]
) -> DatabaseShardingPlan:
    """生成分片计划

    基于数据量和访问模式生成分片建议

    Args:
        estimated_data_size_gb: 预估数据大小（GB）
        estimated_qps: 预估QPS
        table_access_patterns: 表访问模式，如 {"users": {"read": 0.7, "write": 0.3}}
    """
    # 基于数据量估算分片数
    if estimated_data_size_gb < 100:
        recommended_shards = 4
    elif estimated_data_size_gb < 500:
        recommended_shards = 8
    elif estimated_data_size_gb < 1000:
        recommended_shards = 16
    else:
        recommended_shards = 32

    # 基于QPS调整
    if estimated_qps > 10000:
        recommended_shards = max(recommended_shards, 16)
    elif estimated_qps > 50000:
        recommended_shards = max(recommended_shards, 32)

    # 选择分片策略
    # 热点用户数据 -> 一致性哈希
    # 时间序列数据 -> 时间分片
    # 范围查询多 -> 范围分片
    recommended_strategy = ShardingStrategy.CONSISTENT_HASH

    migration_steps = [
        "1. 创建新分片数据库",
        "2. 迁移索引表到新数据库",
        "3. 使用双写策略迁移业务表",
        "4. 验证数据一致性",
        "5. 切换读流量到分片",
        "6. 切换写流量到分片",
        "7. 清理遗留数据",
    ]

    risks = [
        "分片键选择不当导致数据倾斜",
        "跨分片查询性能下降",
        "迁移过程中数据一致性问题",
        "分片扩缩容期间服务中断",
    ]

    return DatabaseShardingPlan(
        plan_id=f"plan_{int(estimated_data_size_gb)}_{recommended_shards}",
        description=f"推荐使用{recommended_shards}个分片，策略为{recommended_strategy.value}",
        estimated_data_size_gb=estimated_data_size_gb,
        estimated_qps=estimated_qps,
        recommended_num_shards=recommended_shards,
        recommended_strategy=recommended_strategy,
        table_configs=[
            get_table_config(name) or TableShardConfig(
                table_name=name,
                strategy=TableShardingStrategy.SINGLE_TABLE,
            )
            for name in table_access_patterns.keys()
        ],
        migration_steps=migration_steps,
        risks=risks,
    )


__all__ = [
    "Shard",
    "ShardConfig",
    "ShardKey",
    "ShardingStrategy",
    "ShardManager",
    "ShardRouter",
    "TableShardConfig",
    "TableShardingStrategy",
    "DatabaseShardingPlan",
    "get_default_shard_config",
    "get_table_config",
    "generate_sharding_plan",
]
