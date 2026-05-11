"""监控系统 - 结构化日志和指标收集"""

import logging
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import threading
import os

logger = logging.getLogger("hydraflow.monitor")


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class Metric:
    """指标数据"""
    name: str
    type: MetricType
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())
    description: str = ""


@dataclass
class LogEntry:
    """结构化日志条目"""
    level: LogLevel
    message: str
    timestamp: float = field(default_factory=lambda: time.time())
    module: str = ""
    function: str = ""
    line: int = 0
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, service_name: str = "hydraflow"):
        self._service_name = service_name
        self._logger = logging.getLogger(service_name)
        self._setup_formatter()
    
    def _setup_formatter(self) -> None:
        """设置日志格式化器"""
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # 文件处理器
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler("logs/hydraflow.log")
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        self._logger.setLevel(logging.INFO)
    
    def _format_log(self, entry: LogEntry) -> str:
        """格式化日志条目"""
        log_data = {
            "service": self._service_name,
            "level": entry.level.value,
            "message": entry.message,
            "timestamp": datetime.fromtimestamp(entry.timestamp).isoformat(),
            "module": entry.module,
            "function": entry.function,
            "line": entry.line,
        }
        
        if entry.trace_id:
            log_data["trace_id"] = entry.trace_id
        if entry.span_id:
            log_data["span_id"] = entry.span_id
        if entry.context:
            log_data["context"] = entry.context
        if entry.error:
            log_data["error"] = entry.error
        
        return json.dumps(log_data, ensure_ascii=False)
    
    def log(self, level: LogLevel, message: str, **kwargs) -> None:
        """记录日志"""
        entry = LogEntry(
            level=level,
            message=message,
            module=kwargs.get("module", ""),
            function=kwargs.get("function", ""),
            line=kwargs.get("line", 0),
            trace_id=kwargs.get("trace_id"),
            span_id=kwargs.get("span_id"),
            context=kwargs.get("context", {}),
            error=kwargs.get("error"),
        )
        
        formatted = self._format_log(entry)
        
        if level == LogLevel.DEBUG:
            self._logger.debug(formatted)
        elif level == LogLevel.INFO:
            self._logger.info(formatted)
        elif level == LogLevel.WARNING:
            self._logger.warning(formatted)
        elif level == LogLevel.ERROR:
            self._logger.error(formatted)
        elif level == LogLevel.CRITICAL:
            self._logger.critical(formatted)
    
    def debug(self, message: str, **kwargs) -> None:
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self.log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        self.log(LogLevel.CRITICAL, message, **kwargs)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def increment(self, name: str, value: float = 1.0, **labels) -> None:
        """增加计数器"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._metrics:
                self._metrics[key] = Metric(
                    name=name,
                    type=MetricType.COUNTER,
                    labels=labels,
                )
            self._metrics[key].value += value
            self._metrics[key].timestamp = time.time()
    
    def gauge(self, name: str, value: float, **labels) -> None:
        """设置仪表盘值"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._metrics:
                self._metrics[key] = Metric(
                    name=name,
                    type=MetricType.GAUGE,
                    labels=labels,
                )
            self._metrics[key].value = value
            self._metrics[key].timestamp = time.time()
    
    def histogram(self, name: str, value: float, **labels) -> None:
        """记录直方图样本"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
            
            # 同时维护统计指标
            samples = self._histograms[key]
            metrics_key = f"histogram_{key}"
            if metrics_key not in self._metrics:
                self._metrics[metrics_key] = Metric(
                    name=name,
                    type=MetricType.HISTOGRAM,
                    labels={**labels, "stat": "avg"},
                )
            self._metrics[metrics_key].value = sum(samples) / len(samples)
            self._metrics[metrics_key].timestamp = time.time()
    
    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        """生成唯一键"""
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}:{label_str}"
    
    def get_metrics(self) -> List[Dict[str, Any]]:
        """获取所有指标"""
        with self._lock:
            result = []
            for key, metric in self._metrics.items():
                result.append({
                    "name": metric.name,
                    "type": metric.type.value,
                    "value": metric.value,
                    "labels": metric.labels,
                    "timestamp": datetime.fromtimestamp(metric.timestamp).isoformat(),
                    "description": metric.description,
                })
            return result
    
    def reset(self, name: Optional[str] = None) -> None:
        """重置指标"""
        with self._lock:
            if name:
                keys_to_remove = [k for k in self._metrics if k.startswith(name)]
                for k in keys_to_remove:
                    del self._metrics[k]
            else:
                self._metrics.clear()
                self._histograms.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {
            "counters": [],
            "gauges": [],
            "histograms": [],
            "total_metrics": len(self._metrics),
        }
        
        for metric in self._metrics.values():
            entry = {
                "name": metric.name,
                "value": metric.value,
                "labels": metric.labels,
            }
            if metric.type == MetricType.COUNTER:
                summary["counters"].append(entry)
            elif metric.type == MetricType.GAUGE:
                summary["gauges"].append(entry)
            elif metric.type == MetricType.HISTOGRAM:
                summary["histograms"].append(entry)
        
        return summary


class Monitor:
    """监控管理器"""
    
    def __init__(self):
        self._logger = StructuredLogger()
        self._metrics = MetricsCollector()
        self._start_time = time.time()
    
    def log(self, level: LogLevel, message: str, **kwargs) -> None:
        """记录日志"""
        self._logger.log(level, message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        self._logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self._logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        self._logger.critical(message, **kwargs)
    
    def increment(self, name: str, value: float = 1.0, **labels) -> None:
        """增加计数器"""
        self._metrics.increment(name, value, **labels)
    
    def gauge(self, name: str, value: float, **labels) -> None:
        """设置仪表盘值"""
        self._metrics.gauge(name, value, **labels)
    
    def histogram(self, name: str, value: float, **labels) -> None:
        """记录直方图样本"""
        self._metrics.histogram(name, value, **labels)
    
    def record_request(self, endpoint: str, duration: float, status_code: int) -> None:
        """记录请求指标"""
        self.increment("requests_total", endpoint=endpoint, status_code=str(status_code))
        self.histogram("request_duration_ms", duration * 1000, endpoint=endpoint)
        if status_code >= 500:
            self.increment("errors_total", endpoint=endpoint)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return {
            "metrics": self._metrics.get_metrics(),
            "summary": self._metrics.get_summary(),
            "uptime": time.time() - self._start_time,
        }
    
    def get_health(self) -> Dict[str, Any]:
        """获取健康状态"""
        uptime = time.time() - self._start_time
        summary = self._metrics.get_summary()
        
        # 计算健康分数
        error_rate = 0.0
        total_requests = sum(c["value"] for c in summary["counters"] if c["name"] == "requests_total")
        errors = sum(c["value"] for c in summary["counters"] if c["name"] == "errors_total")
        if total_requests > 0:
            error_rate = errors / total_requests
        
        health_score = min(100, max(0, 100 - error_rate * 200))
        
        return {
            "status": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "unhealthy",
            "health_score": health_score,
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_uptime(uptime),
            "metrics": summary,
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        parts.append(f"{secs}秒")
        
        return " ".join(parts)
    
    def reset_metrics(self) -> None:
        """重置指标"""
        self._metrics.reset()


# 全局单例
_monitor = None

def get_monitor() -> Monitor:
    """获取监控管理器实例"""
    global _monitor
    if _monitor is None:
        _monitor = Monitor()
    return _monitor
