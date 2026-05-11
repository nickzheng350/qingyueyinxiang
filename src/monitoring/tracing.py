"""OpenTelemetry 链路追踪模块"""

import logging
from typing import Optional, Any, Callable, TypeVar, ParamSpec
from functools import wraps
from contextlib import asynccontextmanager

logger = logging.getLogger("hydraflow.tracing")

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.resource import ResourceAttributes
    from opentelemetry.trace import (
        Tracer,
        Span,
        Status,
        StatusCode,
        Link,
    )
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    from opentelemetry.context import Context
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.sdk.extension.aws.resource.eks import AwsEksResourceDetector
    from opentelemetry.sdk.extension.aws.resource.ec2 import AwsEc2ResourceDetector

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not installed. Tracing will be disabled.")


T = TypeVar("T")
P = ParamSpec("P")


class TracingManager:
    """链路追踪管理器"""

    def __init__(self, service_name: str = "hydraflow"):
        self._service_name = service_name
        self._tracer: Optional[Tracer] = None
        self._provider: Optional[Any] = None
        self._propagator = TraceContextTextMapPropagator()
        self._enabled = False

    def setup(
        self,
        service_version: str = "1.0.0",
        exporter: str = "console",
        endpoint: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> "TracingManager":
        """初始化链路追踪"""
        if not OTEL_AVAILABLE:
            logger.warning("OpenTelemetry not available. Skipping tracing setup.")
            return self

        try:
            resource_attributes = {
                ResourceAttributes.SERVICE_NAME: self._service_name,
                ResourceAttributes.SERVICE_VERSION: service_version,
            }

            if environment:
                resource_attributes[ResourceAttributes.DEPLOYMENT_ENVIRONMENT] = environment

            resource = Resource.create(resource_attributes)

            self._provider = TracerProvider(resource=resource)

            if exporter == "console":
                span_exporter = ConsoleSpanExporter()
                processor = SimpleSpanProcessor(span_exporter)
            elif exporter == "otlp" and endpoint:
                try:
                    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                        OTLPSpanExporter,
                    )
                    span_exporter = OTLPSpanExporter(endpoint=endpoint)
                    processor = BatchSpanProcessor(span_exporter)
                except ImportError:
                    logger.warning("OTLP exporter not available, using console.")
                    span_exporter = ConsoleSpanExporter()
                    processor = BatchSpanProcessor(span_exporter)
            else:
                span_exporter = ConsoleSpanExporter()
                processor = BatchSpanProcessor(span_exporter)

            self._provider.add_span_processor(processor)

            trace.set_tracer_provider(self._provider)

            set_global_textmap(self._propagator)

            self._tracer = trace.get_tracer(self._service_name)
            self._enabled = True

            logger.info(f"Tracing initialized for service: {self._service_name}")

        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")

        return self

    @property
    def tracer(self) -> Optional[Tracer]:
        """获取追踪器"""
        return self._tracer

    @property
    def is_enabled(self) -> bool:
        """是否启用"""
        return self._enabled and OTEL_AVAILABLE

    def create_span(
        self,
        name: str,
        *,
        kind: Optional[Any] = None,
        attributes: Optional[dict[str, Any]] = None,
        links: Optional[list[Link]] = None,
    ) -> Optional[Span]:
        """创建 span"""
        if not self.is_enabled or not self._tracer:
            return None

        span = self._tracer.start_span(
            name=name,
            kind=kind,
            links=links,
        )

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        return span

    @asynccontextmanager
    async def span_async(
        self,
        name: str,
        *,
        kind: Optional[Any] = None,
        attributes: Optional[dict[str, Any]] = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
    ):
        """异步上下文管理器创建 span"""
        if not self.is_enabled or not self._tracer:
            yield None
            return

        async with self._tracer.start_as_current_span(
            name=name,
            kind=kind,
            record_exception=record_exception,
            set_status_on_exception=set_status_on_exception,
        ) as span:
            if span and attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span

    @asynccontextmanager
    async def trace_async(
        self,
        operation_name: str,
        *,
        attributes: Optional[dict[str, Any]] = None,
    ):
        """追踪异步操作"""
        async with self.span_async(operation_name, attributes=attributes) as span:
            try:
                yield span
                if span:
                    span.set_status(Status(StatusCode.OK))
            except Exception as e:
                if span:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                raise

    def extract_context(self, carrier: dict[str, str]) -> Optional[Context]:
        """从 carrier 中提取上下文"""
        if not OTEL_AVAILABLE:
            return None

        try:
            return self._propagator.extract(carrier)
        except Exception as e:
            logger.debug(f"Failed to extract context: {e}")
            return None

    def inject_context(self, carrier: dict[str, str]) -> dict[str, str]:
        """注入上下文到 carrier"""
        if not OTEL_AVAILABLE:
            return carrier

        try:
            self._propagator.inject(carrier)
        except Exception as e:
            logger.debug(f"Failed to inject context: {e}")

        return carrier

    def get_current_span(self) -> Optional[Span]:
        """获取当前 span"""
        if not OTEL_AVAILABLE:
            return None

        return trace.get_current_span()

    def get_current_trace_id(self) -> Optional[str]:
        """获取当前 trace ID"""
        span = self.get_current_span()
        if span and OTEL_AVAILABLE:
            context = span.get_span_context()
            if context.is_valid:
                return format(context.trace_id, "032x")
        return None

    def get_current_span_id(self) -> Optional[str]:
        """获取当前 span ID"""
        span = self.get_current_span()
        if span and OTEL_AVAILABLE:
            context = span.get_span_context()
            if context.is_valid:
                return format(context.span_id, "016x")
        return None

    def add_span_attributes(self, attributes: dict[str, Any]) -> None:
        """为当前 span 添加属性"""
        span = self.get_current_span()
        if span:
            for key, value in attributes.items():
                span.set_attribute(key, value)

    def record_exception(self, exception: Exception) -> None:
        """记录异常到当前 span"""
        span = self.get_current_span()
        if span:
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))

    def set_span_status(self, status: StatusCode, description: str = "") -> None:
        """设置 span 状态"""
        span = self.get_current_span()
        if span:
            span.set_status(Status(status, description))

    def shutdown(self) -> None:
        """关闭追踪器"""
        if self._provider:
            try:
                self._provider.shutdown()
                logger.info("Tracing shutdown completed")
            except Exception as e:
                logger.error(f"Error shutting down tracing: {e}")


def traced(
    operation_name: Optional[str] = None,
    *,
    attributes: Optional[dict[str, Any]] = None,
    record_exception: bool = True,
):
    """装饰器：为异步函数添加链路追踪"""

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        if not OTEL_AVAILABLE:
            return func

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            tracer = trace.get_tracer("hydraflow.tracing")

            span_name = operation_name or f"{func.__module__}.{func.__name__}"

            async with tracer.start_as_current_span(
                span_name,
                record_exception=record_exception,
            ) as span:
                if span and attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    result = await func(*args, **kwargs)
                    if span:
                        span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    if span:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                    raise

        return wrapper

    return decorator


_tracing_manager: Optional[TracingManager] = None


def get_tracing_manager(service_name: str = "hydraflow") -> TracingManager:
    """获取全局追踪管理器"""
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager(service_name)
    return _tracing_manager


def setup_tracing(
    service_name: str = "hydraflow",
    service_version: str = "1.0.0",
    exporter: str = "console",
    endpoint: Optional[str] = None,
    environment: Optional[str] = None,
) -> TracingManager:
    """设置全局追踪"""
    manager = get_tracing_manager(service_name)
    manager.setup(
        service_version=service_version,
        exporter=exporter,
        endpoint=endpoint,
        environment=environment,
    )
    return manager
