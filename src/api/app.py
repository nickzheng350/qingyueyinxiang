"""FastAPI 应用创建与配置"""

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_config
from src.core.stability import get_stability_manager
from src.api.routes import api_router

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

    cors_origins = api_config.get("cors_origins", ["http://localhost:3000"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

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
