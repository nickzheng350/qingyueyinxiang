"""HydraFlow AI 连接池管理器 - 数据库和 HTTP 连接复用"""

import asyncio
import weakref
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Optional
from collections.abc import AsyncIterator
from abc import ABC, abstractmethod

import httpx

from src.core.config import get_settings

settings = get_settings()


@dataclass
class PoolConfig:
    """连接池配置"""
    min_size: int = 5
    max_size: int = 20
    max_overflow: int = 10
    timeout: float = 30.0
    recycle_time: int = 3600


class ConnectionPool(ABC):
    """连接池抽象基类"""

    @abstractmethod
    async def acquire(self) -> Any:
        """获取连接"""
        pass

    @abstractmethod
    async def release(self, connection: Any) -> None:
        """释放连接"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭连接池"""
        pass


class HTTPConnectionPool(ConnectionPool):
    """HTTP 连接池"""

    def __init__(self, base_url: str, config: Optional[PoolConfig] = None):
        self.base_url = base_url.rstrip("/")
        self.config = config or PoolConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        self._size = 0

    async def _create_client(self) -> httpx.AsyncClient:
        """创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(
                max_keepalive_connections=self.config.min_size,
                max_connections=self.config.max_size,
            )
            timeout = httpx.Timeout(self.config.timeout)
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                limits=limits,
                timeout=timeout,
                follow_redirects=True,
            )
        return self._client

    async def acquire(self) -> httpx.AsyncClient:
        """获取客户端"""
        async with self._lock:
            self._size += 1
            return await self._create_client()

    async def release(self, connection: httpx.AsyncClient) -> None:
        """释放客户端（不关闭，保持复用）"""
        pass

    async def close(self) -> None:
        """关闭连接池"""
        async with self._lock:
            if self._client and not self._client.is_closed:
                await self._client.aclose()
                self._client = None

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[httpx.AsyncClient]:
        """上下文管理器获取连接"""
        client = await self.acquire()
        try:
            yield client
        finally:
            await self.release(client)


class DatabaseConnectionPool(ConnectionPool):
    """数据库连接池"""

    def __init__(self, database_url: str, config: Optional[PoolConfig] = None):
        self.database_url = database_url
        self.config = config or PoolConfig()
        self._engine = None
        self._session_factory = None
        self._lock = asyncio.Lock()
        self._initialized = False

    async def _create_engine(self):
        """创建数据库引擎"""
        if self._engine is None:
            async with self._lock:
                if self._engine is None:
                    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

                    self._engine = create_async_engine(
                        self.database_url,
                        pool_size=self.config.min_size,
                        max_overflow=self.config.max_overflow,
                        pool_recycle=self.config.recycle_time,
                        pool_timeout=self.config.timeout,
                        echo=False,
                    )
                    self._session_factory = async_sessionmaker(
                        self._engine,
                        class_=AsyncSession,
                        expire_on_commit=False,
                    )
                    self._initialized = True

    async def acquire(self) -> Any:
        """获取会话"""
        if not self._initialized:
            await self._create_engine()
        return self._session_factory()

    async def release(self, connection: Any) -> None:
        """释放会话"""
        try:
            await connection.close()
        except Exception:
            pass

    async def close(self) -> None:
        """关闭连接池"""
        async with self._lock:
            if self._engine:
                await self._engine.dispose()
                self._engine = None
                self._session_factory = None
                self._initialized = False

    @asynccontextmanager
    async def session(self) -> AsyncIterator[Any]:
        """上下文管理器获取会话"""
        session = await self.acquire()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class PoolManager:
    """连接池管理器 - 统一管理多个连接池"""

    _instance: Optional["PoolManager"] = None

    def __new__(cls) -> "PoolManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._http_pools: dict[str, HTTPConnectionPool] = {}
        self._db_pools: dict[str, DatabaseConnectionPool] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, name: str) -> asyncio.Lock:
        """获取锁"""
        if name not in self._locks:
            self._locks[name] = asyncio.Lock()
        return self._locks[name]

    async def get_http_pool(
        self,
        base_url: str,
        config: Optional[PoolConfig] = None,
    ) -> HTTPConnectionPool:
        """获取 HTTP 连接池"""
        async with self._get_lock(base_url):
            if base_url not in self._http_pools:
                self._http_pools[base_url] = HTTPConnectionPool(base_url, config)
            return self._http_pools[base_url]

    async def get_db_pool(
        self,
        database_url: str,
        config: Optional[PoolConfig] = None,
    ) -> DatabaseConnectionPool:
        """获取数据库连接池"""
        async with self._get_lock(database_url):
            if database_url not in self._db_pools:
                self._db_pools[database_url] = DatabaseConnectionPool(database_url, config)
            return self._db_pools[database_url]

    async def close_all(self) -> None:
        """关闭所有连接池"""
        for pool in self._http_pools.values():
            await pool.close()
        for pool in self._db_pools.values():
            await pool.close()
        self._http_pools.clear()
        self._db_pools.clear()

    def get_stats(self) -> dict:
        """获取连接池统计"""
        return {
            "http_pools": len(self._http_pools),
            "db_pools": len(self._db_pools),
            "http_pool_urls": list(self._http_pools.keys()),
        }


_pool_manager_instance: Optional[PoolManager] = None


def get_pool_manager() -> PoolManager:
    """获取连接池管理器单例"""
    global _pool_manager_instance
    if _pool_manager_instance is None:
        _pool_manager_instance = PoolManager()
    return _pool_manager_instance
