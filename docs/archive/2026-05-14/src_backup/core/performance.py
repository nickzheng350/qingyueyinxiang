"""性能监控与优化模块 - 效能增长，成本节约"""
import logging
import time
import threading
import psutil
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from collections import defaultdict

logger = logging.getLogger("hydraflow.core.performance")


class OptimizationStrategy(str, Enum):
    """优化策略"""
    AUTO = "auto"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    COST = "cost"
    BALANCED = "balanced"


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricSnapshot:
    """指标快照"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    network_io: Optional[tuple] = None


@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_id: str
    level: AlertLevel
    message: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class OptimizationAction:
    """优化动作"""
    action_id: str
    action_type: str
    description: str
    estimated_improvement: float
    applied: bool = False
    applied_at: Optional[float] = None
    result: Optional[str] = None


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self.snapshots: List[MetricSnapshot] = []
        self.alerts: List[PerformanceAlert] = []
        self.thresholds: Dict[str, float] = {
            "cpu_high": 85.0,
            "cpu_critical": 95.0,
            "memory_high": 90.0,
            "memory_critical": 98.0,
        }
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable[[PerformanceAlert], None]] = []
        self.lock = threading.RLock()
    
    def take_snapshot(self) -> MetricSnapshot:
        """获取指标快照"""
        cpu_usage = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        
        snapshot = MetricSnapshot(
            timestamp=time.time(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
        )
        
        with self.lock:
            self.snapshots.append(snapshot)
            if len(self.snapshots) > 100:
                self.snapshots = self.snapshots[-100:]
        
        self._check_thresholds(snapshot)
        
        return snapshot
    
    def _check_thresholds(self, snapshot: MetricSnapshot):
        """检查阈值"""
        import uuid
        
        if snapshot.cpu_usage > self.thresholds["cpu_critical"]:
            alert = PerformanceAlert(
                alert_id=str(uuid.uuid4()),
                level=AlertLevel.CRITICAL,
                message="CPU usage critically high",
                metric_name="cpu_usage",
                metric_value=snapshot.cpu_usage,
                threshold=self.thresholds["cpu_critical"],
            )
            self._send_alert(alert)
        elif snapshot.cpu_usage > self.thresholds["cpu_high"]:
            alert = PerformanceAlert(
                alert_id=str(uuid.uuid4()),
                level=AlertLevel.WARNING,
                message="CPU usage high",
                metric_name="cpu_usage",
                metric_value=snapshot.cpu_usage,
                threshold=self.thresholds["cpu_high"],
            )
            self._send_alert(alert)
        
        if snapshot.memory_usage > self.thresholds["memory_critical"]:
            alert = PerformanceAlert(
                alert_id=str(uuid.uuid4()),
                level=AlertLevel.CRITICAL,
                message="Memory usage critically high",
                metric_name="memory_usage",
                metric_value=snapshot.memory_usage,
                threshold=self.thresholds["memory_critical"],
            )
            self._send_alert(alert)
        elif snapshot.memory_usage > self.thresholds["memory_high"]:
            alert = PerformanceAlert(
                alert_id=str(uuid.uuid4()),
                level=AlertLevel.WARNING,
                message="Memory usage high",
                metric_name="memory_usage",
                metric_value=snapshot.memory_usage,
                threshold=self.thresholds["memory_high"],
            )
            self._send_alert(alert)
    
    def _send_alert(self, alert: PerformanceAlert):
        """发送告警"""
        with self.lock:
            self.alerts.append(alert)
            if len(self.alerts) > 1000:
                self.alerts = self.alerts[-1000:]
        
        for callback in self.callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        logger.warning(f"[{alert.level}] {alert.message}")
    
    def add_callback(self, callback: Callable[[PerformanceAlert], None]):
        """添加告警回调"""
        self.callbacks.append(callback)
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self.take_snapshot()
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            time.sleep(self.interval)
    
    def start(self):
        """启动监控"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitor started")
    
    def stop(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Performance monitor stopped")
    
    def get_recent_snapshots(self, count: int = 20) -> List[MetricSnapshot]:
        """获取最近的快照"""
        with self.lock:
            return self.snapshots[-count:]
    
    def get_average_usage(self, window: float = 60.0) -> Dict[str, float]:
        """获取平均使用率"""
        now = time.time()
        cutoff = now - window
        relevant = [s for s in self.snapshots if s.timestamp >= cutoff]
        
        if not relevant:
            return {"cpu": 0.0, "memory": 0.0}
        
        cpu_avg = sum(s.cpu_usage for s in relevant) / len(relevant)
        mem_avg = sum(s.memory_usage for s in relevant) / len(relevant)
        
        return {"cpu": cpu_avg, "memory": mem_avg}
    
    def get_alerts(self, level: Optional[AlertLevel] = None, limit: int = 50) -> List[PerformanceAlert]:
        """获取告警"""
        with self.lock:
            alerts = self.alerts.copy()
            if level:
                alerts = [a for a in alerts if a.level == level]
            return alerts[-limit:]


class CostTracker:
    """成本追踪器"""
    
    def __init__(self):
        self.costs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.total_cost: float = 0.0
        self.savings: float = 0.0
        self.lock = threading.RLock()
    
    def record_cost(self, task_id: str, task_type: str, cost: float, optimized: bool = False):
        """记录成本"""
        with self.lock:
            entry = {
                "task_id": task_id,
                "task_type": task_type,
                "cost": cost,
                "timestamp": time.time(),
                "optimized": optimized,
            }
            self.costs[task_type].append(entry)
            self.total_cost += cost
            if optimized:
                self.savings += cost * 0.3
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """获取成本摘要"""
        with self.lock:
            summary = {
                "total_cost": self.total_cost,
                "estimated_savings": self.savings,
                "by_type": {},
            }
            
            for task_type, entries in self.costs.items():
                total = sum(e["cost"] for e in entries)
                count = len(entries)
                summary["by_type"][task_type] = {
                    "total": total,
                    "count": count,
                    "average": total / count if count > 0 else 0.0,
                }
            
            return summary


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, monitor: PerformanceMonitor, cost_tracker: CostTracker):
        self.monitor = monitor
        self.cost_tracker = cost_tracker
        self.strategy = OptimizationStrategy.AUTO
        self.history: List[OptimizationAction] = []
        self.adaptive_settings: Dict[str, Any] = {
            "cache_enabled": True,
            "batch_processing": False,
            "max_concurrent": 5,
            "prefetch_enabled": False,
        }
        self.lock = threading.RLock()
    
    def set_strategy(self, strategy: OptimizationStrategy):
        """设置优化策略"""
        with self.lock:
            self.strategy = strategy
            self._apply_strategy()
    
    def _apply_strategy(self):
        """应用策略"""
        strategy_settings = {
            OptimizationStrategy.LATENCY: {
                "max_concurrent": 2,
                "cache_enabled": True,
                "batch_processing": False,
                "prefetch_enabled": True,
            },
            OptimizationStrategy.THROUGHPUT: {
                "max_concurrent": 10,
                "cache_enabled": True,
                "batch_processing": True,
                "prefetch_enabled": False,
            },
            OptimizationStrategy.COST: {
                "max_concurrent": 3,
                "cache_enabled": True,
                "batch_processing": True,
                "prefetch_enabled": False,
            },
            OptimizationStrategy.BALANCED: {
                "max_concurrent": 5,
                "cache_enabled": True,
                "batch_processing": True,
                "prefetch_enabled": True,
            },
        }
        
        if self.strategy in strategy_settings:
            self.adaptive_settings.update(strategy_settings[self.strategy])
    
    def analyze_and_optimize(self) -> List[OptimizationAction]:
        """分析并优化"""
        import uuid
        actions = []
        
        usage = self.monitor.get_average_usage()
        
        if usage["cpu"] > 80.0:
            action = OptimizationAction(
                action_id=str(uuid.uuid4()),
                action_type="reduce_concurrency",
                description="Reduce concurrent tasks due to high CPU usage",
                estimated_improvement=20.0,
            )
            actions.append(action)
            self.adaptive_settings["max_concurrent"] = max(
                2, self.adaptive_settings["max_concurrent"] - 1
            )
        
        if usage["cpu"] < 30.0 and self.adaptive_settings["max_concurrent"] < 8:
            action = OptimizationAction(
                action_id=str(uuid.uuid4()),
                action_type="increase_concurrency",
                description="Increase concurrent tasks due to low CPU usage",
                estimated_improvement=30.0,
            )
            actions.append(action)
            self.adaptive_settings["max_concurrent"] += 1
        
        for action in actions:
            action.applied = True
            action.applied_at = time.time()
            self.history.append(action)
        
        return actions
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置"""
        with self.lock:
            return self.adaptive_settings.copy()
    
    def get_optimization_history(self, limit: int = 100) -> List[OptimizationAction]:
        """获取优化历史"""
        with self.lock:
            return self.history[-limit:]


class UnifiedPerformanceManager:
    """统一性能管理器"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.cost_tracker = CostTracker()
        self.optimizer = PerformanceOptimizer(self.monitor, self.cost_tracker)
        self.running = False
    
    def start(self):
        """启动"""
        self.monitor.start()
        self.running = True
        
        self.monitor.add_callback(self._on_alert)
        logger.info("UnifiedPerformanceManager started")
    
    def stop(self):
        """停止"""
        self.monitor.stop()
        self.running = False
        logger.info("UnifiedPerformanceManager stopped")
    
    def _on_alert(self, alert: PerformanceAlert):
        """处理告警"""
        if alert.level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
            self.optimizer.analyze_and_optimize()
    
    def record_task(self, task_id: str, task_type: str, cost: float, optimized: bool = False):
        """记录任务"""
        self.cost_tracker.record_cost(task_id, task_type, cost, optimized)
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "performance": self.monitor.get_average_usage(),
            "cost": self.cost_tracker.get_cost_summary(),
            "settings": self.optimizer.get_current_settings(),
            "alerts": [
                {"level": a.level.value, "message": a.message}
                for a in self.monitor.get_alerts(limit=10)
            ],
        }
    
    def set_optimization_strategy(self, strategy: OptimizationStrategy):
        """设置优化策略"""
        self.optimizer.set_strategy(strategy)
