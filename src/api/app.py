"""FastAPI 应用创建与配置"""

import time
import uuid
import logging
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, Request, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.exceptions import RequestValidationError
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    
try:
    from pydantic import ValidationError
except ImportError:
    class ValidationError(Exception):
        pass

try:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
except ImportError:
    _rate_limit_exceeded_handler = None
    class RateLimitExceeded(Exception):
        pass

from src.core.config import get_config
from src.core.stability import get_stability_manager
from src.core.exceptions import QingYueYinXiangError, ErrorResponse
from src.api.api_routes import api_router
from src.api.routes_plugins import router as plugins_router
from src.api.security import (
    SecurityHeadersMiddleware,
    InputValidationMiddleware,
    limiter,
)
from src.ws.manager import get_ws_manager
from src.ws.routes import WebSocketRoutes
from src.plugins.manager import PluginManager

logger = logging.getLogger("qingyue-yinxiang.api")

_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("清悦印象 AI API 服务启动")

    # 初始化插件系统
    plugin_manager = PluginManager()
    plugin_manager.discover_plugins()
    loaded_plugins = plugin_manager.load_all_plugins()
    logger.info(f"已加载 {len(loaded_plugins)} 个插件")

    # 注册插件端点
    for plugin_name, plugin_inst in loaded_plugins.items():
        endpoints = plugin_inst.get_endpoints()
        for endpoint in endpoints:
            if "router" in endpoint:
                app.include_router(
                    endpoint["router"],
                    prefix=endpoint.get("prefix", ""),
                    tags=endpoint.get("tags", [plugin_name])
                )
                logger.info(f"注册插件端点: {plugin_name}")

    yield
    logger.info("清悦印象 AI API 服务关闭")


def create_app() -> FastAPI:
    config = get_config()
    api_config = {"docs_enabled": config.api.docs_enabled, "cors_origins": config.auth.cors_origins}

    app = FastAPI(
        title="清悦印象 AI",
        description="清悦印象 - 企业级智能工作流平台 API",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs" if api_config.get("docs_enabled", True) else None,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    app.add_exception_handler(QingYueYinXiangError, qingyue_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)

    cors_origins = api_config.get("cors_origins", ["http://localhost:3000"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "X-Request-ID"],
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(InputValidationMiddleware)

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(plugins_router)

    ws_manager = get_ws_manager()
    ws_routes = WebSocketRoutes(ws_manager)
    ws_routes.register_routes(app)

    app.mount("/ui", StaticFiles(directory="ui/public", html=True), name="ui")
    app.mount("/test_skills", StaticFiles(directory="test_skills"), name="test_skills")

    @app.get("/")
    async def root():
        return FileResponse("ui/public/index.html")

    @app.get("/health")
    async def health_check():
        stability = get_stability_manager()
        return {
            "status": "healthy",
            "version": "2.0.0",
            "uptime": time.time() - _start_time,
            "health_score": stability.get_health_score(),
        }

    return app


async def qingyue_exception_handler(
    request: Request, exc: QingYueYinXiangError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        f"清悦印象 error: {exc.error_code} - {exc.detail}",
        extra={"request_id": request_id, "path": str(request.url)},
    )
    error_response = exc.to_error_response(request_id)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={"request_id": request_id, "path": str(request.url)},
    )
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "detail": "Request validation failed",
            "message": "One or more fields are invalid",
            "errors": errors,
            "request_id": request_id,
        },
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        f"Pydantic validation error: {exc.errors()}",
        extra={"request_id": request_id, "path": str(request.url)},
    )
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "detail": "Data validation failed",
            "message": "One or more fields are invalid",
            "errors": errors,
            "request_id": request_id,
        },
    )


app = create_app()
