"""HydraFlow AI 数据库模块 - SQLAlchemy ORM"""

import contextlib
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

from src.core.config import get_settings

settings = get_settings()

async_engine = create_async_engine(
    settings.database.url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    echo=settings.database.echo,
)

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

    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    provider: Mapped[Optional[str]] = mapped_column(String(50))
    provider_id: Mapped[Optional[str]] = mapped_column(String(255))

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_user_provider", "provider", "provider_id"),
    )


class Task(Base):
    """任务模型"""

    __tablename__ = "tasks"

    task_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    type: Mapped[TaskType] = mapped_column(String(50), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=lambda: {})
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(String(50), nullable=False, default=TaskStatus.PENDING)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    task_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=lambda: {}, name="metadata")
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="tasks")
    task_files: Mapped[list["TaskFile"]] = relationship("TaskFile", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_task_status", "status"),
        Index("idx_task_type", "type"),
        Index("idx_task_user", "user_id"),
        Index("idx_task_created", "created_at"),
    )


class TaskFile(Base):
    """任务文件模型"""

    __tablename__ = "task_files"

    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    is_output: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    task: Mapped["Task"] = relationship("Task", back_populates="task_files")

    __table_args__ = (
        Index("idx_task_file_task", "task_id"),
    )


class ApiKey(Base):
    """API 密钥模型"""

    __tablename__ = "api_keys"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    permissions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=lambda: {})

    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index("idx_api_key_user", "user_id"),
        UniqueConstraint("key_prefix", name="uq_api_key_prefix"),
    )


class ModelStat(Base):
    """模型统计模型"""

    __tablename__ = "model_stats"

    model_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_execution_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_execution_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    __table_args__ = (
        UniqueConstraint("model_id", name="uq_model_stat_model_id"),
    )


class Skill(Base):
    """技能模型"""

    __tablename__ = "skills"

    skill_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    author: Mapped[Optional[str]] = mapped_column(String(100))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=lambda: {})
    task_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=lambda: {}, name="metadata")

    __table_args__ = (
        Index("idx_skill_category", "category"),
        Index("idx_skill_enabled", "is_enabled"),
    )


class Config(Base):
    """配置模型"""

    __tablename__ = "configs"

    key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("key", name="uq_config_key"),
    )


class WebSocketConnection(Base):
    """WebSocket 连接模型（用于连接追踪）"""

    __tablename__ = "websocket_connections"

    connection_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(100))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    disconnected_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    subscriptions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=lambda: [])

    __table_args__ = (
        Index("idx_ws_active", "is_active"),
        Index("idx_ws_connected", "connected_at"),
    )


@contextlib.asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话上下文管理器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """初始化数据库 - 创建所有表"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """删除所有表 - 仅用于开发/测试"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
