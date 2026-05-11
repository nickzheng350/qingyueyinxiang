"""HydraFlow AI 认证模块 - OAuth2 + JWT"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from functools import lru_cache

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.persistence.database import User, get_db_session
from src.core.exceptions import AuthenticationError, AuthorizationError

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.auth.jwt_access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.auth.jwt_secret_key,
        algorithm=settings.auth.jwt_algorithm,
    )
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.auth.jwt_refresh_token_expire_days
        )
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.auth.jwt_secret_key,
        algorithm=settings.auth.jwt_algorithm,
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """解码令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.auth.jwt_secret_key,
            algorithms=[settings.auth.jwt_algorithm],
        )
        return payload
    except JWTError:
        raise AuthenticationError("无效的令牌")


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """根据 ID 获取用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_provider(
    db: AsyncSession, provider: str, provider_id: str
) -> Optional[User]:
    """根据 OAuth 提供商获取用户"""
    result = await db.execute(
        select(User).where(and_(User.provider == provider, User.provider_id == provider_id))
    )
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """认证用户"""
    user = await get_user_by_username(db, username)
    if not user:
        user = await get_user_by_email(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password or ""):
        return None
    if not user.is_active:
        raise AuthenticationError("用户已被禁用")
    return user


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: Optional[str] = None,
    provider: Optional[str] = None,
    provider_id: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> User:
    """创建用户"""
    existing_user = await get_user_by_username(db, username)
    if existing_user:
        raise AuthorizationError("用户名已存在")

    existing_email = await get_user_by_email(db, email)
    if existing_email:
        raise AuthorizationError("邮箱已被注册")

    hashed_password = get_password_hash(password) if password else None

    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        provider=provider,
        provider_id=provider_id,
        avatar_url=avatar_url,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(db: AsyncSession, token: str) -> User:
    """获取当前用户"""
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise AuthenticationError("无效的令牌类型")

    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("无效的令牌")

    user = await get_user(db, user_id)
    if user is None:
        raise AuthenticationError("用户不存在")

    if not user.is_active:
        raise AuthenticationError("用户已被禁用")

    return user


class ApiKeyManager:
    """API 密钥管理器"""

    _instance: Optional["ApiKeyManager"] = None

    def __new__(cls) -> "ApiKeyManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def generate_api_key(self) -> tuple[str, str, str]:
        """生成 API 密钥，返回 (完整密钥, 密钥前缀, 密钥哈希)"""
        raw_key = f"hf_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:16]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, prefix, key_hash

    def hash_key(self, key: str) -> str:
        """哈希密钥"""
        return hashlib.sha256(key.encode()).hexdigest()

    def verify_key(self, key: str, key_hash: str) -> bool:
        """验证密钥"""
        return self.hash_key(key) == key_hash


def get_api_key_manager() -> ApiKeyManager:
    """获取 API 密钥管理器"""
    return ApiKeyManager()


class OAuthService:
    """OAuth 服务"""

    async def authenticate_google(self, code: str) -> tuple[str, str]:
        """Google OAuth 认证 - 占位实现"""
        raise NotImplementedError("Google OAuth 未实现")

    async def authenticate_github(self, code: str) -> tuple[str, str]:
        """GitHub OAuth 认证 - 占位实现"""
        raise NotImplementedError("GitHub OAuth 未实现")


def get_oauth_service() -> OAuthService:
    """获取 OAuth 服务"""
    return OAuthService()
