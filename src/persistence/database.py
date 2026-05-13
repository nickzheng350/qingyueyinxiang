"""HydraFlow AI 数据库模块 - SQLAlchemy ORM"""

import contextlib
import re
from datetime import datetime
from typing import Any, AsyncGenerator, Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncAttrs,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    Mapped,
    mapped_column,
)
from sqlalchemy.pool import StaticPool

from src.core.config import get_settings


def _get_database_url() -> str:
    """获取数据库URL，处理驱动缺失的情况"""
    settings = get_settings()
    url = settings.database.url

    if url.startswith("postgresql"):
        try:
            __import__("psycopg2")
            return url
        except ImportError:
            pass
        try:
            __import__("asyncpg")
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        except ImportError:
            pass
        print(f"[HydraFlow] PostgreSQL驱动不可用，降级到SQLite")
        match = re.match(r"postgresql://[^@]+@?[^/]+/(.+)$", url)
        sqlite_path = match.group(1) if match else "hydraflow.db"
        return f"sqlite+aiosqlite:///./data/{sqlite_path}"

    return url


def _create_async_engine():
    """延迟创建引擎，避免模块级错误"""
    url = _get_database_url()
    settings = get_settings()

    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=settings.database.echo,
        )
    return create_async_engine(
        url,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        echo=settings.database.echo,
    )


async_engine = _create_async_engine()
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(AsyncAttrs, DeclarativeBase):
    """基础模型类"""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self, exclude: Optional[list[str]] = None) -> dict[str, Any]:
        exclude_set = exclude or []
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_set:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                else:
                    result[column.name] = value
        return result


class TaskStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, PyEnum):
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO_GENERATION = "audio_generation"
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    IMAGE_UPSCALE = "image_upscale"
    IMAGE_EDIT = "image_edit"
    SKILL_EXECUTION = "skill_execution"


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def verify_password(self, password: str) -> bool:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, self.hashed_password)


class ApiKey(Base):
    """API密钥模型"""
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"

    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON)
    model_id: Mapped[Optional[str]] = mapped_column(String(100))
    result: Mapped[Optional[dict]] = mapped_column(JSON)
    error: Mapped[Optional[str]] = mapped_column(Text)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        Index("idx_task_status_type", "status", "task_type"),
        Index("idx_task_user_status", "user_id", "status"),
    )


class PromptTemplate(Base):
    """提示词模板模型"""
    __tablename__ = "prompt_templates"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    style: Mapped[Optional[str]] = mapped_column(String(50))
    tags: Mapped[Optional[dict]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Skill(Base):
    """技能模型"""
    __tablename__ = "skills"

    skill_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    skill_type: Mapped[str] = mapped_column(String(50), default="local", nullable=False)
    path: Mapped[Optional[str]] = mapped_column(String(255))
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Plugin(Base):
    """插件模型"""
    __tablename__ = "plugins"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接"""
    await async_engine.dispose()


@contextlib.asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的上下文管理器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise