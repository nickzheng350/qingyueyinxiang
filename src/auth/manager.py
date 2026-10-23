"""HydraFlow AI 认证模块 - OAuth2 + JWT"""

import secrets
import hashlib
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from functools import lru_cache

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.persistence.database import User
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
        raise AuthenticationError("无效的令牌") from None


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
    """OAuth 服务。

    Google / GitHub 登录尚未实现。这里不抛 NotImplementedError，
    而是抛出业务异常 AuthenticationError：调用方拿到的是标准化的错误响应，
    而不是会让接口返回 500 的编程错误。
    """

    def _require_credentials(self, provider: str, client_id: str | None, client_secret: str | None) -> None:
        if not client_id or not client_secret:
            raise AuthenticationError(
                f"{provider} OAuth 未配置：缺少 client_id / client_secret"
            )

    async def authenticate_google(self, code: str) -> tuple[str, str]:
        """Google OAuth 认证 - 尚未实现"""
        auth_settings = get_settings().auth
        self._require_credentials(
            "Google",
            auth_settings.oauth_google_client_id,
            auth_settings.oauth_google_client_secret,
        )
        raise AuthenticationError("Google OAuth 尚未实现")

    async def authenticate_github(self, code: str) -> tuple[str, str]:
        """GitHub OAuth 认证 - 尚未实现"""
        auth_settings = get_settings().auth
        self._require_credentials(
            "GitHub",
            auth_settings.oauth_github_client_id,
            auth_settings.oauth_github_client_secret,
        )
        raise AuthenticationError("GitHub OAuth 尚未实现")


def get_oauth_service() -> OAuthService:
    """获取 OAuth 服务"""
    return OAuthService()


@dataclass
class AuthUser:
    """API 层使用的用户对象。

    ORM 的 User 模型依赖数据库初始化，且缺少 role / last_login 字段，
    而 API 路由依赖这些属性，因此定义这个与持久化解耦的用户对象。
    """

    id: int
    username: str
    email: str
    role: str = "user"
    hashed_password: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    @property
    def enabled(self) -> bool:
        """is_active 的别名，与 API 路由中的字段命名保持一致"""
        return self.is_active


class AuthManager:
    """用户管理器（内存存储）。

    API 路由在 async 处理函数中以同步方式调用本类，无法 await 异步 ORM 会话，
    因此这里使用内存存储；令牌签发与校验复用本模块的 JWT 工具函数。
    接入数据库时只需替换 _users 的读写实现，保持对外方法签名不变。
    """

    def __init__(self) -> None:
        self._users: dict[str, AuthUser] = {}
        self._revoked_tokens: set[str] = set()
        self._next_id = 1
        self._lock = threading.Lock()

    # ---------- 用户管理 ----------

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        role: str = "user",
    ) -> Optional[AuthUser]:
        """创建用户，用户名已存在时返回 None"""
        with self._lock:
            if username in self._users:
                return None
            user = AuthUser(
                id=self._next_id,
                username=username,
                email=email or f"{username}@example.com",
                role=role or "user",
                hashed_password=get_password_hash(password) if password else None,
            )
            self._next_id += 1
            self._users[username] = user
            return user

    def get_user(self, username: str) -> Optional[AuthUser]:
        """按用户名获取用户"""
        return self._users.get(username)

    def list_users(self) -> list[AuthUser]:
        """列出全部用户"""
        return list(self._users.values())

    def update_user(self, username: str, **kwargs: object) -> bool:
        """更新用户字段，支持 email / role / enabled"""
        user = self._users.get(username)
        if user is None:
            return False
        if kwargs.get("email") is not None:
            user.email = str(kwargs["email"])
        if kwargs.get("role") is not None:
            user.role = str(kwargs["role"])
        if kwargs.get("enabled") is not None:
            user.is_active = bool(kwargs["enabled"])
        return True

    def delete_user(self, username: str) -> bool:
        """删除用户"""
        with self._lock:
            return self._users.pop(username, None) is not None

    # ---------- 认证 ----------

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """校验凭据并返回访问令牌，失败返回 None"""
        user = self._users.get(username)
        if user is None or not user.is_active:
            return None
        if not user.hashed_password or not verify_password(password, user.hashed_password):
            return None
        user.last_login = datetime.utcnow()
        return create_access_token({"sub": user.username, "role": user.role})

    def verify_token(self, token: str) -> Optional[str]:
        """校验令牌并返回用户名，失败返回 None"""
        if token in self._revoked_tokens:
            return None
        try:
            payload = decode_token(token)
        except (JWTError, AuthenticationError):
            return None
        return payload.get("sub")

    def logout(self, token: str) -> bool:
        """吊销令牌，令牌无效返回 False"""
        if self.verify_token(token) is None:
            return False
        self._revoked_tokens.add(token)
        return True


@lru_cache()
def get_auth_manager() -> AuthManager:
    """获取用户管理器单例"""
    return AuthManager()
