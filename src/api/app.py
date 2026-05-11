"""FastAPI 应用创建与配置"""

import time
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.core.config import get_config
from src.core.stability import get_stability_manager
from src.core.exceptions import HydraFlowError, ErrorResponse
from src.api.routes import api_router
from src.ws.manager import get_ws_manager
from src.ws.routes import WebSocketRoutes

logger = logging.getLogger("hydraflow.api")

_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("HydraFlow AI API 服务启动")
    yield
    logger.info("HydraFlow AI API 服务关闭")


def create_app() -> FastAPI:
    config = get_config()
    api_config = config.global_config.get("api", {})

    app = FastAPI(
        title="HydraFlow AI",
        description="九头蛇生成式工作流平台 API",
        version="1.1.0",
        lifespan=lifespan,
        docs_url="/docs" if api_config.get("docs_enabled", True) else None,
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    app.add_exception_handler(HydraFlowError, hydraflow_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)

    cors_origins = api_config.get("cors_origins", ["http://localhost:3000"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    ws_manager = get_ws_manager()
    ws_routes = WebSocketRoutes(ws_manager)
    ws_routes.register_routes(app)

    @app.get("/health")
    async def health_check():
        stability = get_stability_manager()
        return {
            "status": "healthy",
            "version": "1.1.0",
            "uptime": time.time() - _start_time,
            "health_score": stability.get_health_score(),
        }

    return app


async def hydraflow_exception_handler(
    request: Request, exc: HydraFlowError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        f"HydraFlow error: {exc.error_code} - {exc.detail}",
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
