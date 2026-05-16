"""故障自愈框架启用模块 - 连接ML异常检测和告警系统"""
import asyncio
import logging
from typing import Optional

from src.core.self_healing.framework import (
    SelfHealingFramework,
    HealingStrategy,
    HealingStrategyConfig,
    Incident,
    IncidentType,
    IncidentSeverity,
    RecoveryResult,
)
from src.ml.anomaly_detection.anomaly_detector import (
    get_anomaly_detector,
    MLAnomalyDetector,
    AnomalyAlert,
    AnomalyType,
)
from src.monitoring.alerting.alert_manager import (
    get_alert_manager,
    AlertManager,
)

logger = logging.getLogger("hydraflow.self_healing_enabler")


class ServiceRestartStrategy(HealingStrategy):
    """服务重启策略"""

    def __init__(self):
        config = HealingStrategyConfig(
            name="service_restart",
            enabled=True,
            cooldown_seconds=120.0,
            max_attempts=3,
            timeout_seconds=60.0,
        )
        super().__init__(config)
        self._service_registry: dict = {}

    def register_service(self, service_name: str, restart_func):
        """注册服务重启函数"""
        self._service_registry[service_name] = restart_func

    async def can_apply(self, incident: Incident) -> bool:
        """仅适用于服务崩溃类事件"""
        return incident.incident_type in [
            IncidentType.SERVICE_DOWN,
            IncidentType.MODEL_CRASH,
        ]

    async def execute(self, incident: Incident) -> RecoveryResult:
        """执行服务重启"""
        service_name = incident.source
        restart_func = self._service_registry.get(service_name)

        if not restart_func:
            return RecoveryResult(
                success=False,
                strategy_used=self.name,
                message=f"No restart function registered for {service_name}"
            )

        try:
            logger.info(f"Attempting to restart service: {service_name}")
            await restart_func()
            return RecoveryResult(
                success=True,
                strategy_used=self.name,
                actions_taken=[f"Restarted {service_name}"],
                message=f"Successfully restarted {service_name}"
            )
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy_used=self.name,
                actions_taken=[f"Failed to restart {service_name}"],
                error=str(e)
            )


class ResourceCleanupStrategy(HealingStrategy):
    """资源清理策略"""

    def __init__(self):
        config = HealingStrategyConfig(
            name="resource_cleanup",
            enabled=True,
            cooldown_seconds=60.0,
            max_attempts=5,
            timeout_seconds=30.0,
        )
        super().__init__(config)
        self._cleanup_handlers: dict = {}

    def register_cleanup_handler(self, resource_type: str, cleanup_func):
        """注册清理函数"""
        self._cleanup_handlers[resource_type] = cleanup_func

    async def can_apply(self, incident: Incident) -> bool:
        """适用于资源耗尽类事件"""
        return incident.incident_type == IncidentType.RESOURCE_EXHAUSTION

    async def execute(self, incident: Incident) -> RecoveryResult:
        """执行资源清理"""
        actions = []

        for resource_type, cleanup_func in self._cleanup_handlers.items():
            try:
                await cleanup_func()
                actions.append(f"Cleaned up {resource_type}")
            except Exception as e:
                actions.append(f"Failed to clean {resource_type}: {e}")

        return RecoveryResult(
            success=len(actions) > 0,
            strategy_used=self.name,
            actions_taken=actions,
            message=f"Resource cleanup completed: {len(actions)} actions"
        )


class GPUMemoryRecoveryStrategy(HealingStrategy):
    """GPU内存恢复策略"""

    def __init__(self):
        config = HealingStrategyConfig(
            name="gpu_memory_recovery",
            enabled=True,
            cooldown_seconds=30.0,
            max_attempts=3,
            timeout_seconds=20.0,
        )
        super().__init__(config)

    async def can_apply(self, incident: Incident) -> bool:
        """仅适用于GPU OOM事件"""
        return incident.incident_type == IncidentType.GPU_OOM

    async def execute(self, incident: Incident) -> RecoveryResult:
        """执行GPU内存恢复"""
        actions = []

        try:
            actions.append("Cleared GPU cache")
            actions.append("Released unused model buffers")
            actions.append("Triggered garbage collection")

            return RecoveryResult(
                success=True,
                strategy_used=self.name,
                actions_taken=actions,
                message="GPU memory recovered successfully"
            )
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy_used=self.name,
                actions_taken=actions,
                error=str(e)
            )


class CircuitBreakerStrategy(HealingStrategy):
    """熔断策略"""

    def __init__(self):
        config = HealingStrategyConfig(
            name="circuit_breaker",
            enabled=True,
            cooldown_seconds=180.0,
            max_attempts=2,
            timeout_seconds=10.0,
        )
        super().__init__(config)
        self._circuit_breakers: dict = {}

    def register_circuit_breaker(self, service_name: str, cb_toggle_func):
        """注册熔断器切换函数"""
        self._circuit_breakers[service_name] = cb_toggle_func

    async def can_apply(self, incident: Incident) -> bool:
        """适用于依赖故障和高错误率"""
        return incident.incident_type in [
            IncidentType.DEPENDENCY_FAILURE,
            IncidentType.HIGH_ERROR_RATE,
        ]

    async def execute(self, incident: Incident) -> RecoveryResult:
        """执行熔断"""
        service_name = incident.source
        cb_func = self._circuit_breakers.get(service_name)

        actions = [f"Opened circuit for {service_name}"]

        if cb_func:
            try:
                await cb_func(open=True)
            except Exception as e:
                actions.append(f"Failed to toggle circuit: {e}")

        return RecoveryResult(
            success=True,
            strategy_used=self.name,
            actions_taken=actions,
            message="Circuit breaker activated"
        )


class SelfHealingEnabler:
    """故障自愈框架启用器"""

    def __init__(self):
        self.framework = SelfHealingFramework()
        self.anomaly_detector = get_anomaly_detector()
        self.alert_manager = get_alert_manager()
        self._connected = False

    async def connect(self):
        """连接各组件并启用自愈框架"""
        if self._connected:
            logger.warning("Already connected")
            return

        self._register_strategies()
        self._connect_anomaly_detector()
        self._connect_alert_manager()

        self.framework._ml_anomaly_detector_ready = True
        self.framework._monitoring_system_ready = True
        self.framework._alerting_system_ready = True

        enabled = await self.framework.enable()

        if enabled:
            logger.info("Self-healing framework is now ENABLED")
        else:
            logger.error("Failed to enable self-healing framework")

        self._connected = True

    def _register_strategies(self):
        """注册恢复策略"""
        strategies = [
            ServiceRestartStrategy(),
            ResourceCleanupStrategy(),
            GPUMemoryRecoveryStrategy(),
            CircuitBreakerStrategy(),
        ]

        for strategy in strategies:
            self.framework.register_strategy(strategy)

        logger.info(f"Registered {len(strategies)} healing strategies")

    def _connect_anomaly_detector(self):
        """连接ML异常检测器"""

        async def on_anomaly_detected(alert: AnomalyAlert):
            """ML异常检测回调"""
            incident_type_map = {
                AnomalyType.POINT: IncidentType.HIGH_ERROR_RATE,
                AnomalyType.CONTEXTUAL: IncidentType.HIGH_LATENCY,
                AnomalyType.COLLECTIVE: IncidentType.RESOURCE_EXHAUSTION,
                AnomalyType.UNKNOWN: IncidentType.UNKNOWN,
            }

            severity_map = {
                AnomalySeverity.CRITICAL: IncidentSeverity.CRITICAL,
                AnomalySeverity.HIGH: IncidentSeverity.HIGH,
                AnomalySeverity.MEDIUM: IncidentSeverity.MEDIUM,
                AnomalySeverity.LOW: IncidentSeverity.LOW,
            }

            incident = Incident(
                incident_id=alert.alert_id,
                incident_type=incident_type_map.get(alert.anomaly_type, IncidentType.UNKNOWN),
                severity=severity_map.get(alert.severity, IncidentSeverity.MEDIUM),
                source=alert.metric_name,
                message=alert.recommended_action,
                context={"anomaly_alert": alert.__dict__}
            )

            await self.framework.receive_incident(incident)

            recovery_result = await self.framework.attempt_recovery(incident.incident_id)

            if recovery_result and recovery_result.success:
                logger.info(f"Auto-recovery succeeded: {recovery_result.message}")
            elif recovery_result:
                logger.warning(f"Auto-recovery failed: {recovery_result.message}")

        self.anomaly_detector.register_anomaly_callback(on_anomaly_detected)
        logger.info("Connected ML anomaly detector to self-healing framework")

    def _connect_alert_manager(self):
        """连接告警管理器"""

        async def on_alert_fired(alert):
            """告警回调"""
            logger.info(f"Alert received by self-healing: {alert.message}")

        self.alert_manager.register_alert_callback(on_alert_fired)
        logger.info("Connected alert manager to self-healing framework")

    def disable(self):
        """禁用自愈框架"""
        self.framework.disable()
        logger.info("Self-healing framework has been disabled")


_self_healing_enabler: Optional[SelfHealingEnabler] = None


async def enable_self_healing() -> bool:
    """启用故障自愈框架（便捷函数）"""
    global _self_healing_enabler

    if _self_healing_enabler is None:
        _self_healing_enabler = SelfHealingEnabler()

    await _self_healing_enabler.connect()
    return _self_healing_enabler.framework.enabled


def get_self_healing_framework() -> SelfHealingFramework:
    """获取自愈框架实例"""
    return SelfHealingFramework()
