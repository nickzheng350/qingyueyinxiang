"""HydraFlow AI API 限流模块"""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from src.core.config import get_settings

settings = get_settings()


class RateLimitError(Exception):
    """限流错误"""
    pass


class RateLimitScope(Enum):
    """限流范围"""
    IP = "ip"
    USER = "user"
    GLOBAL = "global"


@dataclass
class RateLimit:
    """限流配置"""
    requests: int
    window: timedelta
    scope: RateLimitScope = RateLimitScope.IP


class TokenBucket:
    """令牌桶算法"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = datetime.utcnow()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """获取令牌"""
        async with self.lock:
            now = datetime.utcnow()
            time_passed = (now - self.last_refill).total_seconds()
            new_tokens = time_passed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class FixedWindowCounter:
    """固定窗口计数器"""

    def __init__(self, window: timedelta):
        self.window = window
        self.counters: dict[str, int] = defaultdict(int)
        self.window_start: dict[str, datetime] = {}
        self.lock = asyncio.Lock()

    async def increment(self, key: str, amount: int = 1) -> int:
        """增加计数"""
        async with self.lock:
            now = datetime.utcnow()

            if key not in self.window_start or now - self.window_start[key] > self.window:
                self.counters[key] = 0
                self.window_start[key] = now

            self.counters[key] += amount
            return self.counters[key]

    async def get_count(self, key: str) -> int:
        """获取当前计数"""
        async with self.lock:
            now = datetime.utcnow()
            if key not in self.window_start or now - self.window_start[key] > self.window:
                return 0
            return self.counters[key]


class SlidingWindowLog:
    """滑动窗口日志"""

    def __init__(self, window: timedelta):
        self.window = window
        self.logs: dict[str, list[datetime]] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def add_request(self, key: str) -> None:
        """添加请求"""
        async with self.lock:
            self.logs[key].append(datetime.utcnow())

    async def get_count(self, key: str) -> int:
        """获取窗口内请求数"""
        async with self.lock:
            now = datetime.utcnow()
            cutoff = now - self.window

            self.logs[key] = [ts for ts in self.logs[key] if ts > cutoff]
            return len(self.logs[key])


class RateLimiter:
    """限流器"""

    _instance: Optional["RateLimiter"] = None

    def __new__(cls) -> "RateLimiter":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.enabled = settings.rate_limit.enabled

        default_limit_parts = settings.rate_limit.default_limit.split("/")
        self.default_requests = int(default_limit_parts[0])
        self.default_window = self._parse_window(default_limit_parts[1])

        authenticated_limit_parts = settings.rate_limit.authenticated_limit.split("/")
        self.authenticated_requests = int(authenticated_limit_parts[0])
        self.authenticated_window = self._parse_window(authenticated_limit_parts[1])

        self.counter = SlidingWindowLog(self.default_window)
        self.auth_counter = SlidingWindowLog(self.authenticated_window)

    def _parse_window(self, window_str: str) -> timedelta:
        """解析窗口字符串"""
        units = {
            "s": timedelta(seconds=1),
            "m": timedelta(minutes=1),
            "h": timedelta(hours=1),
            "d": timedelta(days=1),
        }
        for unit, delta in units.items():
            if window_str.endswith(unit):
                count = int(window_str[:-1])
                return delta * count
        raise ValueError(f"无效的窗口格式: {window_str}")

    def _get_key(self, identifier: str, scope: RateLimitScope) -> str:
        """获取限流键"""
        return f"{scope.value}:{identifier}"

    async def check_rate_limit(
        self,
        identifier: str,
        is_authenticated: bool = False,
        scope: RateLimitScope = RateLimitScope.IP,
    ) -> bool:
        """检查是否超过限流"""
        if not self.enabled:
            return True

        if is_authenticated:
            limit = self.authenticated_requests
            counter = self.auth_counter
        else:
            limit = self.default_requests
            counter = self.counter

        key = self._get_key(identifier, scope)
        await counter.add_request(key)
        count = await counter.get_count(key)

        return count <= limit

    async def check_and_raise(
        self,
        identifier: str,
        is_authenticated: bool = False,
        scope: RateLimitScope = RateLimitScope.IP,
    ) -> None:
        """检查并抛出限流错误"""
        allowed = await self.check_rate_limit(identifier, is_authenticated, scope)
        if not allowed:
            raise RateLimitError("请求过于频繁，请稍后再试")

    async def reset(self, identifier: str, scope: RateLimitScope = RateLimitScope.IP) -> None:
        """重置限流计数"""
        key = self._get_key(identifier, scope)
        if key in self.counter.logs:
            self.counter.logs[key] = []
        if key in self.auth_counter.logs:
            self.auth_counter.logs[key] = []


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """熔断器错误"""
    pass


class CircuitBreaker:
    """熔断器"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.lock = asyncio.Lock()

    async def __aenter__(self):
        await self._check_state()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, self.expected_exception):
            await self._record_failure()
        elif exc_type is None:
            await self._record_success()
        return False

    async def _check_state(self):
        """检查熔断器状态"""
        async with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if self.last_failure_time:
                    time_since_failure = datetime.utcnow() - self.last_failure_time
                    if time_since_failure >= timedelta(seconds=self.recovery_timeout):
                        self.state = CircuitBreakerState.HALF_OPEN
            elif self.state == CircuitBreakerState.HALF_OPEN:
                pass
            elif self.state == CircuitBreakerState.CLOSED:
                pass

    async def _record_failure(self):
        """记录失败"""
        async with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.state in (CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN):
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitBreakerState.OPEN

    async def _record_success(self):
        """记录成功"""
        async with self.lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = 0

    async def call(self, func, *args, **kwargs):
        """调用函数并应用熔断逻辑"""
        await self._check_state()

        if self.state == CircuitBreakerState.OPEN:
            raise CircuitBreakerError("服务暂时不可用，请稍后再试")

        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except self.expected_exception:
            await self._record_failure()
            raise


def get_rate_limiter() -> RateLimiter:
    """获取限流器"""
    return RateLimiter()
