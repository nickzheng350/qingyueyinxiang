"""故障自愈框架模块 - 自动化故障检测与恢复"""
from .framework import SelfHealingFramework, HealingStrategy, Incident, RecoveryResult
from .strategies import (
    RestartStrategy,
    ScaleStrategy,
    CircuitBreakerStrategy,
    FailoverStrategy,
)

__all__ = [
    "SelfHealingFramework",
    "HealingStrategy",
    "Incident",
    "RecoveryResult",
    "RestartStrategy",
    "ScaleStrategy",
    "CircuitBreakerStrategy",
    "FailoverStrategy",
]
