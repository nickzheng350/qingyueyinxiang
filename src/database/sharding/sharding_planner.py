"""数据库分片评估和迁移规划模块"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger("hydraflow.database.sharding_planner")


class ShardReadiness(Enum):
    """分片就绪状态"""
    NOT_STARTED = "not_started"
    EVALUATING = "evaluating"
    PLANNING = "planning"
    MIGRATING = "migrating"
    VALIDATING = "validating"
    COMPLETED = "completed"


@dataclass
class TableMetrics:
    """表级指标"""
    table_name: str
    row_count: int
    size_mb: float
    avg_row_size_bytes: float
    index_count: int
    avg_query_latency_ms: float
    qps: float
    write_ratio: float


@dataclass
class ShardRecommendation:
    """分片建议"""
    table_name: str
    recommended_strategy: str
    estimated_shards: int
    estimated_cost_increase: float
    migration_complexity: str
    priority: int
    reasoning: str


@dataclass
class MigrationPlan:
    """迁移计划"""
    plan_id: str
    table_name: str
    strategy: str
    shard_key: str
    phases: List[Dict[str, Any]]
    estimated_duration_hours: float
    risk_level: str
    rollback_plan: str
    prerequisites: List[str]


class ShardingEvaluator:
    """分片评估器"""

    def __init__(self):
        self.current_metrics: Dict[str, TableMetrics] = {}
        self.recommendations: List[ShardRecommendation] = []
        self.evaluation_timestamp: float = 0

    def record_table_metrics(self, metrics: TableMetrics):
        """记录表指标"""
        self.current_metrics[metrics.table_name] = metrics
        self.evaluation_timestamp = time.time()

    async def evaluate_sharding_need(self) -> List[ShardRecommendation]:
        """评估是否需要分片"""
        recommendations = []

        for table_name, metrics in self.current_metrics.items():
            rec = self._evaluate_single_table(metrics)
            recommendations.append(rec)

        recommendations.sort(key=lambda x: x.priority, reverse=True)
        self.recommendations = recommendations

        return recommendations

    def _evaluate_single_table(self, metrics: TableMetrics) -> ShardRecommendation:
        """评估单个表"""
        row_count = metrics.row_count
        size_mb = metrics.size_mb
        qps = metrics.qps
        write_ratio = metrics.write_ratio

        complexity = "low"
        priority = 0
        reasoning = ""

        if row_count > 10_000_000 or size_mb > 1000:
            priority = 3
            complexity = "high"
            reasoning = f"表数据量巨大: {row_count:,}行, {size_mb:.1f}MB"
        elif row_count > 1_000_000 or size_mb > 100:
            priority = 2
            complexity = "medium"
            reasoning = f"表数据量较大: {row_count:,}行, {size_mb:.1f}MB"
        elif qps > 1000:
            priority = 2
            complexity = "medium"
            reasoning = f"高QPS: {qps:.1f} req/s"
        else:
            priority = 1
            complexity = "low"
            reasoning = f"表数据量适中，可以延后分片"

        strategy = "range"
        if write_ratio > 0.3:
            strategy = "hash"
            reasoning += ", 选择哈希分片策略优化写入"

        estimated_shards = 4
        if priority >= 3:
            estimated_shards = 8
        elif priority >= 2:
            estimated_shards = 4

        estimated_cost = estimated_shards * 0.5

        return ShardRecommendation(
            table_name=metrics.table_name,
            recommended_strategy=strategy,
            estimated_shards=estimated_shards,
            estimated_cost_increase=estimated_cost,
            migration_complexity=complexity,
            priority=priority,
            reasoning=reasoning
        )

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """获取评估摘要"""
        return {
            "tables_evaluated": len(self.current_metrics),
            "recommendations_count": len(self.recommendations),
            "high_priority_tables": sum(1 for r in self.recommendations if r.priority >= 2),
            "total_estimated_shards": sum(r.estimated_shards for r in self.recommendations),
            "last_evaluation": self.evaluation_timestamp,
            "recommendations": [
                {
                    "table": r.table_name,
                    "strategy": r.recommended_strategy,
                    "shards": r.estimated_shards,
                    "priority": r.priority
                }
                for r in self.recommendations[:5]
            ]
        }


class MigrationPlanner:
    """迁移规划器"""

    def __init__(self):
        self.plans: Dict[str, MigrationPlan] = {}
        self.migration_status: Dict[str, ShardReadiness] = {}

    def create_migration_plan(
        self,
        table_name: str,
        strategy: str,
        shard_key: str,
        table_size_gb: float
    ) -> MigrationPlan:
        """创建迁移计划"""
        plan_id = f"migrate_{table_name}_{int(time.time())}"

        phases = []

        if table_size_gb < 10:
            phases = [
                {"phase": 1, "name": "创建新分片表", "duration_hours": 0.5, "risk": "low"},
                {"phase": 2, "name": "双写阶段", "duration_hours": 24, "risk": "medium"},
                {"phase": 3, "name": "数据校验", "duration_hours": 2, "risk": "low"},
                {"phase": 4, "name": "切换读流量", "duration_hours": 1, "risk": "medium"},
                {"phase": 5, "name": "禁用旧表双写", "duration_hours": 0.5, "risk": "high"},
            ]
            estimated_duration = 28
            risk_level = "medium"
        else:
            phases = [
                {"phase": 1, "name": "创建新分片表和索引", "duration_hours": 4, "risk": "low"},
                {"phase": 2, "name": "历史数据迁移", "duration_hours": table_size_gb * 2, "risk": "medium"},
                {"phase": 3, "name": "增量数据同步", "duration_hours": 48, "risk": "medium"},
                {"phase": 4, "name": "数据一致性校验", "duration_hours": 8, "risk": "medium"},
                {"phase": 5, "name": "灰度切流", "duration_hours": 24, "risk": "high"},
                {"phase": 6, "name": "全量切流", "duration_hours": 2, "risk": "high"},
                {"phase": 7, "name": "旧表归档", "duration_hours": 24, "risk": "low"},
            ]
            estimated_duration = table_size_gb * 2 + 110
            risk_level = "high"

        rollback_plan = f"回滚方案：1) 保留旧表双写能力 2) 监控数据一致性 3) 发现问题立即切回"

        prerequisites = [
            "确认目标数据库集群容量充足",
            "完成分片键选择和验证",
            "准备好回滚脚本",
            "通知相关方维护窗口"
        ]

        plan = MigrationPlan(
            plan_id=plan_id,
            table_name=table_name,
            strategy=strategy,
            shard_key=shard_key,
            phases=phases,
            estimated_duration_hours=estimated_duration,
            risk_level=risk_level,
            rollback_plan=rollback_plan,
            prerequisites=prerequisites
        )

        self.plans[table_name] = plan
        self.migration_status[table_name] = ShardReadiness.PLANNING

        logger.info(f"Created migration plan for {table_name}: {plan_id}")

        return plan

    def get_plan(self, table_name: str) -> Optional[MigrationPlan]:
        """获取迁移计划"""
        return self.plans.get(table_name)

    def get_all_plans(self) -> List[MigrationPlan]:
        """获取所有迁移计划"""
        return list(self.plans.values())

    def update_migration_status(self, table_name: str, status: ShardReadiness):
        """更新迁移状态"""
        self.migration_status[table_name] = status
        logger.info(f"Migration status for {table_name}: {status.value}")

    def get_migration_summary(self) -> Dict[str, Any]:
        """获取迁移摘要"""
        return {
            "total_plans": len(self.plans),
            "by_status": {
                status.value: sum(1 for s in self.migration_status.values() if s == status)
                for status in ShardReadiness
            },
            "high_risk_plans": sum(1 for p in self.plans.values() if p.risk_level == "high"),
            "plans": [
                {
                    "table": p.table_name,
                    "strategy": p.strategy,
                    "estimated_hours": p.estimated_duration_hours,
                    "risk": p.risk_level,
                    "status": self.migration_status.get(p.table_name, ShardReadiness.NOT_STARTED).value
                }
                for p in self.plans.values()
            ]
        }


_evaluator_instance: Optional[ShardingEvaluator] = None
_planner_instance: Optional[MigrationPlanner] = None


def get_sharding_evaluator() -> ShardingEvaluator:
    """获取分片评估器"""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = ShardingEvaluator()
    return _evaluator_instance


def get_migration_planner() -> MigrationPlanner:
    """获取迁移规划器"""
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = MigrationPlanner()
    return _planner_instance
