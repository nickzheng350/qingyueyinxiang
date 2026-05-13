"""智能告警系统 - 动态阈值、自适应告警"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod
import threading

logger = logging.getLogger("hydraflow.alert_manager")


class AlertSeverity(Enum):
    """告警严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(Enum):
    """告警状态"""
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertChannel(Enum):
    """告警渠道"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"
    DINGTALK = "dingtalk"


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    severity: AlertSeverity
    channels: List[AlertChannel] = field(default_factory=list)
    enabled: bool = True
    cooldown_seconds: float = 300.0
    description: str = ""

    # 动态阈值配置
    use_dynamic_threshold: bool = False
    historical_window_seconds: float = 3600.0  # 历史数据窗口
    deviation_factor: float = 2.0  # 标准差倍数


@dataclass
class Alert:
    """告警"""
    alert_id: str
    rule: AlertRule
    severity: AlertSeverity
    message: str
    metric_value: float
    threshold: float
    timestamp: float = field(default_factory=time.time)
    status: AlertStatus = AlertStatus.FIRING
    acknowledged_at: Optional[float] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertChannelHandler(ABC):
    """告警渠道处理器基类"""

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """发送告警"""
        pass


class LogChannelHandler(AlertChannelHandler):
    """日志渠道"""

    async def send(self, alert: Alert) -> bool:
        log_method = {
            AlertSeverity.CRITICAL: logger.critical,
            AlertSeverity.HIGH: logger.error,
            AlertSeverity.MEDIUM: logger.warning,
            AlertSeverity.LOW: logger.info,
            AlertSeverity.INFO: logger.info,
        }.get(alert.severity, logger.info)

        log_method(f"[ALERT] {alert.message}")
        return True


class WebhookChannelHandler(AlertChannelHandler):
    """Webhook渠道"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, alert: Alert) -> bool:
        # 简化实现
        logger.info(f"[WEBHOOK] Sending alert to {self.webhook_url}")
        return True


class DynamicThresholdCalculator:
    """动态阈值计算器"""

    def __init__(self, window_seconds: float = 3600.0, deviation_factor: float = 2.0):
        self.window_seconds = window_seconds
        self.deviation_factor = deviation_factor
        self._historical_values: Dict[str, List[float]] = {}
        self._lock = threading.RLock()

    def add_value(self, metric_name: str, value: float):
        """添加指标值"""
        with self._lock:
            if metric_name not in self._historical_values:
                self._historical_values[metric_name] = []

            self._historical_values[metric_name].append(value)

            # 清理过期数据
            cutoff_time = time.time() - self.window_seconds
            self._historical_values[metric_name] = [
                v for v in self._historical_values[metric_name]
                if v > cutoff_time
            ]

    def calculate_threshold(
        self,
        metric_name: str,
        base_threshold: float,
        direction: str = "upper"
    ) -> float:
        """计算动态阈值"""
        with self._lock:
            values = self._historical_values.get(metric_name, [])

            if len(values) < 10:
                return base_threshold

            # 计算均值和标准差
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5

            if direction == "upper":
                return mean + (self.deviation_factor * std_dev)
            else:
                return mean - (self.deviation_factor * std_dev)


class AlertManager:
    """智能告警管理器"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.channel_handlers: Dict[AlertChannel, AlertChannelHandler] = {}

        self.threshold_calculator = DynamicThresholdCalculator()
        self.metrics_buffer: Dict[str, List[float]] = {}

        self._lock = threading.RLock()
        self._alert_callbacks: List[Callable] = []

        # 注册默认渠道
        self.register_channel_handler(AlertChannel.LOG, LogChannelHandler())

        logger.info("AlertManager initialized")

    def register_rule(self, rule: AlertRule):
        """注册告警规则"""
        with self._lock:
            self.rules[rule.rule_id] = rule
            logger.info(f"Registered alert rule: {rule.name}")

    def register_channel_handler(self, channel: AlertChannel, handler: AlertChannelHandler):
        """注册渠道处理器"""
        self.channel_handlers[channel] = handler
        logger.info(f"Registered channel handler: {channel.value}")

    def register_alert_callback(self, callback: Callable):
        """注册告警回调"""
        self._alert_callbacks.append(callback)

    async def evaluate_metric(
        self,
        metric_name: str,
        metric_value: float,
        labels: Dict[str, str] = None
    ):
        """评估指标是否触发告警"""
        with self._lock:
            applicable_rules = [
                rule for rule in self.rules.values()
                if rule.enabled and rule.metric_name == metric_name
            ]

        for rule in applicable_rules:
            # 计算阈值
            threshold = rule.threshold
            if rule.use_dynamic_threshold:
                direction = "upper" if rule.condition in ["gt", "gte"] else "lower"
                threshold = self.threshold_calculator.calculate_threshold(
                    metric_name, threshold, direction
                )

            # 检查条件
            triggered = self._check_condition(metric_value, rule.condition, threshold)

            if triggered:
                await self._fire_alert(rule, metric_value, threshold, labels)

    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        """检查条件"""
        if condition == "gt":
            return value > threshold
        elif condition == "gte":
            return value >= threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "lte":
            return value <= threshold
        elif condition == "eq":
            return abs(value - threshold) < 0.0001
        return False

    async def _fire_alert(
        self,
        rule: AlertRule,
        metric_value: float,
        threshold: float,
        labels: Dict[str, str] = None
    ):
        """触发告警"""
        # 检查是否在冷却中
        existing_alert = self._find_existing_alert(rule.rule_id)
        if existing_alert and existing_alert.status == AlertStatus.FIRING:
            return

        alert = Alert(
            alert_id=f"alert_{int(time.time() * 1000)}",
            rule=rule,
            severity=rule.severity,
            message=f"{rule.name}: {metric_value} {rule.condition} {threshold}",
            metric_value=metric_value,
            threshold=threshold,
            metadata={"labels": labels or {}}
        )

        with self._lock:
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)

            # 限制历史记录数量
            if len(self.alert_history) > 10000:
                self.alert_history = self.alert_history[-5000:]

        # 发送告警
        asyncio.create_task(self._send_alert(alert))

        # 触发回调
        for callback in self._alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

        logger.warning(f"Alert fired: {alert.message}")

    async def _send_alert(self, alert: Alert):
        """发送告警到各渠道"""
        tasks = []
        for channel in alert.rule.channels:
            handler = self.channel_handlers.get(channel)
            if handler:
                tasks.append(handler.send(alert))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _find_existing_alert(self, rule_id: str) -> Optional[Alert]:
        """查找已存在的告警"""
        for alert in self.active_alerts.values():
            if alert.rule.rule_id == rule_id and alert.status == AlertStatus.FIRING:
                return alert
        return None

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """确认告警"""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = time.time()
                alert.acknowledged_by = acknowledged_by
                logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = time.time()
                del self.active_alerts[alert_id]
                logger.info(f"Alert {alert_id} resolved")
                return True
        return False

    def get_active_alerts(
        self,
        severity: AlertSeverity = None,
        status: AlertStatus = None
    ) -> List[Alert]:
        """获取活跃告警"""
        with self._lock:
            alerts = list(self.active_alerts.values())

            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            if status:
                alerts = [a for a in alerts if a.status == status]

            return alerts

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        with self._lock:
            return {
                "total_rules": len(self.rules),
                "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
                "active_alerts": len(self.active_alerts),
                "total_alerts": len(self.alert_history),
                "alerts_by_severity": {
                    sev.value: sum(1 for a in self.active_alerts.values() if a.severity == sev)
                    for sev in AlertSeverity
                },
                "alerts_by_status": {
                    st.value: sum(1 for a in self.active_alerts.values() if a.status == st)
                    for st in AlertStatus
                },
            }


# 全局单例
_alert_manager_instance: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """获取告警管理器单例"""
    global _alert_manager_instance
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager()
    return _alert_manager_instance
