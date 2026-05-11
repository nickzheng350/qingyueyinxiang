# HydraFlow AI 零技术债规格文档

**版本**: 2.0.0
**日期**: 2026-05-12
**目标**: 实现零技术债，成为行业标杆

---

## 一、当前状态评估

### 1.1 技术债清单（修复进度）

| 债务项 | 状态 | 优先级 | 负责人 |
|--------|------|--------|--------|
| Bare except 语句 | ✅ 已修复 | P0 | AI |
| 过于宽泛的异常捕获 | ⚠️ 部分修复 (73→56) | P0 | AI |
| 循环中 len() 调用 | ✅ 已修复 | P1 | AI |
| httpx.AsyncClient 资源管理 | ✅ 已修复 | P0 | AI |
| 类型提示覆盖率 | ✅ 完整覆盖 | P1 | AI |
| 单元测试覆盖 | ❌ 不足 (~15%) | P1 | AI |
| 全局异常处理器 | ✅ 已实现 | P0 | AI |
| 结构化日志 | ⚠️ 基础实现 | P2 | AI |
| OpenTelemetry 链路追踪 | ✅ 已实现 | P1 | AI |
| 全异步架构 | ⚠️ 部分异步 | P2 | AI |
| RAG 系统 | ✅ 已实现 | P1 | AI |

### 1.2 行业定位

| 维度 | 当前 | 目标 | 差距 |
|------|------|------|------|
| 代码质量 | 8/10 | 10/10 | 测试 |
| 功能完整性 | 9/10 | 10/10 | 完善 |
| 性能优化 | 9/10 | 10/10 | 微优化 |
| 可观测性 | 9/10 | 10/10 | 完善 |
| 生产就绪 | 7/10 | 10/10 | 测试、文档 |

---

## 二、零技术债实现规格

### 2.1 P0: httpx 资源管理与全局异常处理

#### 目标
- 所有 httpx.AsyncClient 使用上下文管理器
- 实现全局异常处理器
- 自定义异常层次结构

#### 实现规格

```python
# src/core/exceptions.py - 扩展异常层次
class AppException(Exception):
    status_code: int = 500
    detail: str = "Internal Error"
    error_code: str = "INTERNAL_ERROR"

    def to_dict(self) -> dict:
        return {
            "error": self.__class__.__name__,
            "detail": self.detail,
            "error_code": self.error_code,
        }

class ModelNotFoundError(AppException):
    status_code = 404
    detail = "Model not found"
    error_code = "MODEL_NOT_FOUND"

class ParserError(AppException):
    status_code = 500
    detail = "Parser execution failed"
    error_code = "PARSER_ERROR"

class SkillExecutionError(AppException):
    status_code = 500
    detail = "Skill execution failed"
    error_code = "SKILL_EXECUTION_ERROR"
```

```python
# src/api/app.py - 全局异常处理器
from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.core.exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "detail": exc.detail,
            "path": str(request.url),
        }
    )
```

```python
# httpx.AsyncClient 使用规范
# ❌ 错误
client = httpx.AsyncClient()
result = await client.get(url)

# ✅ 正确
async with httpx.AsyncClient() as client:
    result = await client.get(url)
```

#### 验证标准
- [ ] 所有 httpx 调用使用上下文管理器
- [ ] 异常层次完整覆盖所有业务异常
- [ ] 全局处理器正确返回标准化错误响应

---

### 2.2 P1: 类型提示完整覆盖

#### 目标
- 核心模块类型提示 100% 覆盖
- 所有公共 API 有完整类型签名
- 消除 Any 类型滥用

#### 实现规格

```python
# src/intent_parser/factory.py - 完整类型提示
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@runtime_checkable
class IntentParser(Protocol):
    name: str

    def parse(self, text: str, **kwargs: Any) -> ParseResult: ...
    def get_info(self) -> dict[str, Any]: ...

@dataclass(frozen=True)
class ParserRegistryEntry:
    parser: IntentParser
    priority: int
    enabled: bool

class IntentParserFactory:
    _parsers: dict[str, ParserRegistryEntry] = {}
    _cache: dict[str, ParseResult] = {}
    _cache_ttl: int = 3600

    def register_parser(
        self,
        name: str,
        parser: IntentParser,
        *,
        priority: int = 0,
        enabled: bool = True,
    ) -> None:
        ...

    async def parse_async(
        self,
        text: str,
        *,
        parser_name: str | None = None,
        use_cache: bool = True,
    ) -> ParseResult:
        ...

    def list_parsers(self) -> list[dict[str, Any]]:
        ...
```

#### 验证标准
- [ ] mypy 检查通过（无 Any 警告）
- [ ] 核心模块 100% 类型覆盖
- [ ] 所有公共 API 有类型签名

---

### 2.3 P1: 轻量级 RAG 系统

#### 目标
- 实现文档向量化和检索
- 支持本地和远程向量存储
- 与现有意图解析系统集成

#### 实现规格

```python
# src/rag/embeddings.py
class EmbeddingModel(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        ...

class LocalEmbedding(EmbeddingModel):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model = None
        self._model_name = model_name

    async def embed(self, text: str) -> list[float]:
        if self._model is None:
            self._model = await self._load_model()
        return await self._model.encode(text)

# src/rag/vector_store.py
@dataclass
class Document:
    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

@dataclass
class SearchResult:
    document: Document
    score: float
    distance: float

class VectorStore(ABC):
    @abstractmethod
    async def add_document(self, doc: Document) -> None: ...

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[SearchResult]: ...

class InMemoryVectorStore(VectorStore):
    def __init__(self):
        self._documents: dict[str, Document] = {}
        self._index: list[Document] = []

    async def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[SearchResult]:
        # 余弦相似度计算
        ...

# src/rag/rag_engine.py
class RAGEngine:
    def __init__(
        self,
        embedding_model: EmbeddingModel,
        vector_store: VectorStore,
    ):
        self._embedder = embedding_model
        self._store = vector_store

    async def add_documents(
        self,
        documents: list[str],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        ...

    async def query(
        self,
        question: str,
        *,
        top_k: int = 5,
    ) -> str:
        query_embedding = await self._embedder.embed(question)
        results = await self._store.search(query_embedding, top_k=top_k)
        context = "\n".join(r.document.content for r in results)
        return self._build_prompt(question, context)
```

#### 验证标准
- [ ] RAG 引擎可添加文档和查询
- [ ] 向量检索返回相关结果
- [ ] 与意图解析系统无缝集成

---

### 2.4 P1: OpenTelemetry 链路追踪

#### 目标
- 全链路追踪支持
- Span 上下文传播
- 可观测性指标收集

#### 实现规格

```python
# src/monitoring/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

def setup_tracing(service_name: str) -> trace.Tracer:
    resource = Resource(attributes={
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
    })

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)

# 使用示例
tracer = setup_tracing("hydraflow-api")

@api_router.post("/intent/parse")
async def parse_intent(request: ParseRequest):
    with tracer.start_as_current_span("parse_intent") as span:
        span.set_attribute("parser", request.parser)
        span.set_attribute("text_length", len(request.text))

        result = await factory.parse(request.text, parser_name=request.parser)

        span.set_attribute("intent", result.intent.value)
        span.set_attribute("confidence", result.confidence)

        return {...}
```

#### 验证标准
- [ ] 链路追踪正确传播上下文
- [ ] Span 属性正确记录
- [ ] 追踪数据可导出到后端

---

### 2.5 P2: 单元测试覆盖 (70%+)

#### 目标
- 核心业务逻辑测试覆盖 70%+
- API 端点测试覆盖 80%+
- 集成测试覆盖关键路径

#### 实现规格

```python
# tests/test_intent_parser.py
import pytest
from src.intent_parser.factory import IntentParserFactory
from src.intent_parser.base import IntentType

class TestIntentParserFactory:
    @pytest.fixture
    def factory(self):
        return IntentParserFactory()

    @pytest.mark.asyncio
    async def test_parse_simple_image_query(self, factory):
        result = await factory.parse_async("生成一张猫的图片")
        assert result.intent == IntentType.IMAGE_GENERATION
        assert result.confidence >= 0.9

    @pytest.mark.asyncio
    async def test_parse_with_style(self, factory):
        result = await factory.parse_async("生成赛博朋克风格的图片")
        assert result.intent == IntentType.IMAGE_GENERATION
        assert result.style == "cyberpunk"

    @pytest.mark.asyncio
    async def test_cache_hit(self, factory):
        text = "生成一张猫的图片"
        result1 = await factory.parse_async(text)
        result2 = await factory.parse_async(text)
        assert result1 is result2  # 同一对象

# tests/test_api.py
class TestIntentParseEndpoint:
    @pytest.mark.asyncio
    async def test_parse_intent_success(self, client):
        response = await client.post(
            "/api/v1/intent/parse",
            json={"text": "生成一张图片"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data
        assert "confidence" in data

    @pytest.mark.asyncio
    async def test_parse_intent_invalid_request(self, client):
        response = await client.post(
            "/api/v1/intent/parse",
            json={}
        )
        assert response.status_code == 422
```

#### 验证标准
- [ ] 核心模块测试覆盖 70%+
- [ ] API 测试覆盖 80%+
- [ ] 所有测试通过

---

### 2.6 P2: 全异步架构重构

#### 目标
- 所有同步方法改为异步
- 使用 asyncio.TaskGroup 并发处理
- 消除阻塞调用

#### 实现规格

```python
# 同步 → 异步 重构示例
class ModelDispatcher:
    # 重构前
    def get_model(self, model_id: str) -> dict:
        return self._models.get(model_id)

    # 重构后
    async def get_model_async(self, model_id: str) -> dict:
        model = self._models.get(model_id)
        if model is None:
            raise ModelNotFoundError(model_id)
        # 异步操作（如缓存检查）
        cached = await self._cache.get(f"model:{model_id}")
        if cached:
            return cached
        return model

    # 兼容方法
    def get_model(self, model_id: str) -> dict:
        return asyncio.get_event_loop().run_until_complete(
            self.get_model_async(model_id)
        )
```

#### 验证标准
- [ ] 核心模块 100% 异步
- [ ] 无阻塞调用
- [ ] 并发处理正常

---

### 2.7 P3: 结构化日志完善

#### 目标
- JSON 格式日志
- 请求 ID 追踪
- 日志级别正确使用

#### 实现规格

```python
# src/core/logging.py
import logging
import json
import traceback
from datetime import datetime, timezone
from typing import Any

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        if record.levelno >= logging.ERROR:
            log_data["stack_trace"] = record.getMessage()

        return json.dumps(log_data)

def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(getattr(logging, level.upper()))
```

#### 验证标准
- [ ] 日志输出 JSON 格式
- [ ] 包含请求 ID
- [ ] 异常信息完整

---

## 三、实现路线图

### 阶段一：零技术债基础（P0 项目）
1. **httpx 资源管理** - 2 天
2. **全局异常处理器** - 1 天
3. **类型提示完善** - 3 天

### 阶段二：功能完整性（P1 项目）
4. **RAG 系统** - 5 天
5. **OpenTelemetry** - 3 天

### 阶段三：质量保证（P2 项目）
6. **单元测试覆盖** - 5 天
7. **全异步重构** - 5 天

### 阶段四：生产就绪（P3 项目）
8. **结构化日志** - 2 天
9. **性能基准测试** - 3 天

**总计**: 约 29 个工作日

---

## 四、验收标准

### 4.1 零技术债验收

| 检查项 | 标准 | 验证方法 |
|--------|------|----------|
| 代码异味 | 0 个 | flake8 + 自定义脚本 |
| 类型安全 | mypy 无警告 | mypy src/ |
| 测试覆盖 | 70%+ | pytest --cov |
| 文档完整 | 100% API 文档 | OpenAPI spec |

### 4.2 行业标杆验收

| 维度 | 目标 | 验证方法 |
|------|------|----------|
| 功能完整性 | 10/10 | 功能清单对比 |
| 代码质量 | 10/10 | 代码审查评分 |
| 性能优化 | 10/10 | 基准测试 |
| 可观测性 | 10/10 | 追踪覆盖率 |
| 生产就绪 | 10/10 | 部署检查清单 |

---

## 五、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 依赖项冲突 | 中 | 固定版本，使用虚拟环境 |
| 重构破坏现有功能 | 高 | 完整测试覆盖，分阶段部署 |
| 性能回退 | 中 | 持续基准测试监控 |
| 进度延迟 | 中 | 优先 P0/P1 项目，延后 P3 |

---

**文档结束**
