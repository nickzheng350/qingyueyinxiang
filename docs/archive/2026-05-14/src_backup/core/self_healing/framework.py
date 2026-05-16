"""故障自愈框架 - 预留接口，暂不启用核心逻辑"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger("hydraflow.self_healing")


class IncidentSeverity(Enum):
    """事件严重程度"""
    CRITICAL = "critical"    # 需要立即处理
    HIGH = "high"           # 需要尽快处理
    MEDIUM = "medium"       # 可以延后处理
    LOW = "low"            # 建议处理


class IncidentType(Enum):
    """事件类型"""
    SERVICE_DOWN = "service_down"
    HIGH_LATENCY = "high_latency"
    HIGH_ERROR_RATE = "high_error_rate"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_FAILURE = "dependency_failure"
    MODEL_CRASH = "model_crash"
    GPU_OOM = "gpu_oom"
    UNKNOWN = "unknown"


@dataclass
class Incident:
    """故障事件"""
    incident_id: str
    incident_type: IncidentType
    severity: IncidentSeverity
    source: str  # 哪个服务/组件
    message: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)  # 包含相关指标和日志
    related_incidents: List[str] = field(default_factory=list)  # 关联的事件ID


@dataclass
class RecoveryResult:
    """恢复结果"""
    success: bool
    strategy_used: str
    actions_taken: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    message: str = ""
    new_state: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class HealingStrategyConfig:
    """恢复策略配置"""
    name: str
    enabled: bool = False  # 默认禁用
    cooldown_seconds: float = 60.0  # 冷却时间
    max_attempts: int = 3  # 最大尝试次数
    timeout_seconds: float = 300.0  # 超时时间
    conditions: Dict[str, Any] = field(default_factory=dict)  # 触发条件


class HealingStrategy(ABC):
    """恢复策略基类"""

    def __init__(self, config: HealingStrategyConfig):
        self.config = config
        self.name = config.name
        self.enabled = config.enabled
        self.last_execution_time: Optional[float] = None
        self.execution_count: int = 0

    @abstractmethod
    async def can_apply(self, incident: Incident) -> bool:
        """判断此策略是否适用于此事件"""
        pass

    @abstractmethod
    async def execute(self, incident: Incident) -> RecoveryResult:
        """执行恢复策略"""
        pass

    def is_in_cooldown(self) -> bool:
        """是否在冷却中"""
        if self.last_execution_time is None:
            return False
        return (time.time() - self.last_execution_time) < self.config.cooldown_seconds

    def record_execution(self, success: bool):
        """记录执行结果"""
        self.last_execution_time = time.time()
        if not success:
            self.execution_count += 1

    def should_abort(self) -> bool:
        """是否应该中止（超过最大尝试次数）"""
        return self.execution_count >= self.config.max_attempts


class SelfHealingFramework:
    """故障自愈框架

    预留接口设计，暂不启用核心逻辑。
    需要等待以下前置条件成熟后启用：
    1. P2 ML异常检测系统
    2. P1 监控系统
    3. 完整的告警系统
    """

    _instance: Optional["SelfHealingFramework"] = None

    def __new__(cls) -> "SelfHealingFramework":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.enabled = False  # 默认禁用
        self.strategies: Dict[str, HealingStrategy] = {}
        self.incident_history: List[Incident] = []
        self.active_incidents: Dict[str, Incident] = {}
        self.recovery_handlers: List[Callable] = []

        self._ml_anomaly_detector_ready = False
        self._monitoring_system_ready = False
        self._alerting_system_ready = False

        self._lock = asyncio.Lock()

        logger.info("SelfHealingFramework initialized (DISABLED - requires P2 ML anomaly detection)")

    def register_strategy(self, strategy: HealingStrategy):
        """注册恢复策略"""
        self.strategies[strategy.name] = strategy
        logger.info(f"Registered healing strategy: {strategy.name} (enabled={strategy.enabled})")

    async def enable(self) -> bool:
        """启用自愈框架"""
        checks_passed = await self._check_prerequisites()

        if not checks_passed:
            logger.warning(
                "Self-healing framework cannot be enabled - prerequisites not met:"
                f"\n  ML Anomaly Detector: {self._ml_anomaly_detector_ready}"
                f"\n  Monitoring System: {self._monitoring_system_ready}"
                f"\n  Alerting System: {self._alerting_system_ready}"
            )
            return False

        self.enabled = True
        logger.info("SelfHealingFramework ENABLED")
        return True

    def disable(self):
        """禁用自愈框架"""
        self.enabled = False
        logger.info("SelfHealingFramework DISABLED")

    async def _check_prerequisites(self) -> bool:
        """检查前置条件"""
        return (
            self._ml_anomaly_detector_ready and
            self._monitoring_system_ready and
            self._alerting_system_ready
        )

    async def receive_incident(self, incident: Incident):
        """接收故障事件"""
        async with self._lock:
            self.active_incidents[incident.incident_id] = incident
            self.incident_history.append(incident)

            logger.info(
                f"Received incident: {incident.incident_type.value} "
                f"severity={incident.severity.value} from {incident.source}"
            )

    async def attempt_recovery(self, incident_id: str) -> Optional[RecoveryResult]:
        """尝试恢复事件"""
        if not self.enabled:
            logger.warning(
                f"Attempted recovery for {incident_id} but framework is disabled"
            )
            return RecoveryResult(
                success=False,
                strategy_used="none",
                message="Framework disabled - requires ML anomaly detection (P2)"
            )

        async with self._lock:
            incident = self.active_incidents.get(incident_id)
            if not incident:
                logger.warning(f"Incident {incident_id} not found")
                return None

        applicable_strategy = None
        for name, strategy in self.strategies.items():
            if not strategy.enabled:
                continue
            if strategy.is_in_cooldown():
                continue
            if strategy.should_abort():
                continue

            if await strategy.can_apply(incident):
                applicable_strategy = strategy
                break

        if not applicable_strategy:
            return RecoveryResult(
                success=False,
                strategy_used="none",
                message="No applicable strategy found"
            )

        logger.info(f"Executing strategy {applicable_strategy.name} for {incident_id}")
        start_time = time.time()

        try:
            result = await asyncio.wait_for(
                applicable_strategy.execute(incident),
                timeout=applicable_strategy.config.timeout_seconds
            )

            result.duration_seconds = time.time() - start_time
            applicable_strategy.record_execution(result.success)

            for handler in self.recovery_handlers:
                try:
                    await handler(incident, result)
                except Exception as e:
                    logger.error(f"Recovery handler error: {e}")

            if result.success:
                async with self._lock:
                    if incident_id in self.active_incidents:
                        del self.active_incidents[incident_id]

            return result

        except asyncio.TimeoutError:
            logger.error(f"Recovery timeout for {incident_id}")
            return RecoveryResult(
                success=False,
                strategy_used=applicable_strategy.name,
                actions_taken=[],
                duration_seconds=time.time() - start_time,
                error="Recovery timeout"
            )
        except Exception as e:
            logger.error(f"Recovery error for {incident_id}: {e}")
            return RecoveryResult(
                success=False,
                strategy_used=applicable_strategy.name,
                actions_taken=[],
                duration_seconds=time.time() - start_time,
                error=str(e)
            )

    def register_recovery_handler(self, handler: Callable):
        """注册恢复完成处理器"""
        self.recovery_handlers.append(handler)

    async def get_incident_status(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """获取事件状态"""
        async with self._lock:
            incident = self.active_incidents.get(incident_id)
            if not incident:
                return None

            return {
                "incident_id": incident.incident_id,
                "type": incident.incident_type.value,
                "severity": incident.severity.value,
                "source": incident.source,
                "message": incident.message,
                "timestamp": incident.timestamp,
                "age_seconds": time.time() - incident.timestamp,
                "related_incidents": incident.related_incidents,
            }

    def get_framework_status(self) -> Dict[str, Any]:
        """获取框架状态"""
        return {
            "enabled": self.enabled,
            "prerequisites": {
                "ml_anomaly_detector": self._ml_anomaly_detector_ready,
                "monitoring_system": self._monitoring_system_ready,
                "alerting_system": self._alerting_system_ready,
            },
            "active_incidents": len(self.active_incidents),
            "total_incidents": len(self.incident_history),
            "registered_strategies": [
                {
                    "name": s.name,
                    "enabled": s.enabled,
                    "in_cooldown": s.is_in_cooldown(),
                    "execution_count": s.execution_count,
                }
                for s in self.strategies.values()
            ],
        }

    def update_prerequisite_status(
        self,
        ml_detector: bool = None,
        monitoring: bool = None,
        alerting: bool = None
    ):
        """更新前置条件状态"""
        if ml_detector is not None:
            self._ml_anomaly_detector_ready = ml_detector
        if monitoring is not None:
            self._monitoring_system_ready = monitoring
        if alerting is not None:
            self._alerting_system_ready = alerting

        logger.info(
            f"Updated prerequisite status: "
            f"ML={self._ml_anomaly_detector_ready}, "
            f"Monitor={self._monitoring_system_ready}, "
            f"Alert={self._alerting_system_ready}"
        )


def get_self_healing_framework() -> SelfHealingFramework:
    """获取自愈框架单例"""
    return SelfHealingFramework()
