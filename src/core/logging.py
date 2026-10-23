"""结构化日志。

提供 JSON 格式输出与 request_id 全链路传播：

* ``request_id`` 通过 ``contextvars`` 在协程间传递，
  无需在每个函数中显式传参，也不会被并发请求串扰。
* 日志以 JSON 单行输出，便于日志系统采集与检索。

用法::

    from src.core.logging import setup_logging, bind_request_id, get_logger

    setup_logging("INFO")
    logger = get_logger("hydraflow.api")

    bind_request_id("req-123")
    logger.info("处理完成")
"""

import contextvars
import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "hydraflow_request_id", default=None
)


def bind_request_id(request_id: str | None) -> None:
    """把 request_id 绑定到当前上下文（协程安全）"""
    request_id_var.set(request_id)


def get_request_id() -> str | None:
    """读取当前上下文的 request_id"""
    return request_id_var.get()


class RequestIdFilter(logging.Filter):
    """把上下文中的 request_id 注入每条日志记录"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JSONFormatter(logging.Formatter):
    """单行 JSON 日志格式器"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        request_id = getattr(record, "request_id", None)
        if request_id:
            log_data["request_id"] = request_id

        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            log_data["exception"] = {
                "type": getattr(exc_type, "__name__", "Exception"),
                "message": str(exc_value),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """人类可读格式，带 request_id 前缀"""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        request_id = getattr(record, "request_id", None)
        return f"[{request_id}] {base}" if request_id else base


def setup_logging(
    level: str = "INFO",
    *,
    json_format: bool = True,
    force: bool = True,
) -> None:
    """配置根日志器。

    Args:
        level: 日志级别名称，如 INFO / DEBUG
        json_format: True 输出 JSON，False 输出可读文本
        force: 是否移除已存在的 handler（避免重复输出）
    """
    root = logging.getLogger()
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(resolved_level)

    if force:
        for handler in list(root.handlers):
            root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(resolved_level)
    handler.setFormatter(JSONFormatter() if json_format else TextFormatter())
    handler.addFilter(RequestIdFilter())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """获取日志器（约定以 hydraflow. 为前缀）"""
    return logging.getLogger(name)
