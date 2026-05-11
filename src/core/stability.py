"""HydraFlow AI 稳定性管理器 - 错误处理、重试、熔断"""

import time
import functools
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger("hydraflow.stability")


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(Enum):
    FIXED = "fixed"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR = "linear"


@dataclass
class RetryConfig:
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ErrorRecord:
    timestamp: float
    error_type: str
    message: str
    severity: ErrorSeverity
    module: str
    details: dict = field(default_factory=dict)


class CircuitBreaker:
    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.half_open_calls = 0

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and (
                time.time() - self.last_failure_time >= self.config.recovery_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        return False

    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
        self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN


class StabilityManager:
    _instance: "StabilityManager | None" = None

    def __new__(cls) -> "StabilityManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._error_records: list[ErrorRecord] = []
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._max_records = 1000

    def record_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        module: str = "unknown",
        details: dict | None = None,
    ) -> None:
        record = ErrorRecord(
            timestamp=time.time(),
            error_type=type(error).__name__,
            message=str(error),
            severity=severity,
            module=module,
            details=details or {},
        )
        self._error_records.append(record)
        if len(self._error_records) > self._max_records:
            self._error_records = self._error_records[-self._max_records:]
        logger.error(f"[{severity.value}] {module}: {error}")

    def get_health_score(self) -> float:
        if not self._error_records:
            return 100.0
        recent = [r for r in self._error_records if time.time() - r.timestamp < 300]
        if not recent:
            return 100.0
        severity_weights = {
            ErrorSeverity.LOW: 1,
            ErrorSeverity.MEDIUM: 5,
            ErrorSeverity.HIGH: 15,
            ErrorSeverity.CRITICAL: 30,
        }
        total_penalty = sum(severity_weights.get(r.severity, 5) for r in recent)
        score = max(0.0, 100.0 - total_penalty)
        return score

    def get_error_statistics(self) -> dict[str, Any]:
        if not self._error_records:
            return {"total_errors": 0, "by_severity": {}, "by_module": {}}
        by_severity: dict[str, int] = {}
        by_module: dict[str, int] = {}
        for record in self._error_records:
            by_severity[record.severity.value] = by_severity.get(record.severity.value, 0) + 1
            by_module[record.module] = by_module.get(record.module, 0) + 1
        return {
            "total_errors": len(self._error_records),
            "by_severity": by_severity,
            "by_module": by_module,
        }

    def get_error_records(self, limit: int = 10, module: str | None = None) -> list[ErrorRecord]:
        records = self._error_records
        if module:
            records = [r for r in records if r.module == module]
        return records[-limit:]

    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
        if name not in self._circuit_breakers:
            self._circuit_breakers[name] = CircuitBreaker(name, config)
        return self._circuit_breakers[name]

    def retry(self, config: RetryConfig | None = None) -> Callable:
        retry_config = config or RetryConfig()

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_error = None
                for attempt in range(retry_config.max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        if attempt < retry_config.max_attempts - 1:
                            delay = self._calculate_delay(retry_config, attempt)
                            logger.warning(
                                f"重试 {attempt + 1}/{retry_config.max_attempts}: {func.__name__}, "
                                f"等待 {delay:.1f}s"
                            )
                            time.sleep(delay)
                        self.record_error(e, severity=ErrorSeverity.MEDIUM, module=func.__name__)
                raise last_error

            return wrapper

        return decorator

    def circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> Callable:
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                cb = self.get_circuit_breaker(name, config)
                if not cb.can_execute():
                    raise Exception(f"熔断器 [{name}] 已开启，请求被拒绝")
                try:
                    result = func(*args, **kwargs)
                    cb.record_success()
                    return result
                except Exception as e:
                    cb.record_failure()
                    self.record_error(e, severity=ErrorSeverity.HIGH, module=name)
                    raise

            return wrapper

        return decorator

    @staticmethod
    def _calculate_delay(config: RetryConfig, attempt: int) -> float:
        if config.strategy == RetryStrategy.FIXED:
            return config.initial_delay
        elif config.strategy == RetryStrategy.LINEAR:
            return min(config.initial_delay * (attempt + 1), config.max_delay)
        else:
            return min(config.initial_delay * (config.backoff_factor**attempt), config.max_delay)


_stability_instance: StabilityManager | None = None


def get_stability_manager() -> StabilityManager:
    global _stability_instance
    if _stability_instance is None:
        _stability_instance = StabilityManager()
    return _stability_instance
