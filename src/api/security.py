"""安全中间件和配置 - 防止常见Web攻击"""

import re
import secrets
import time
from typing import Optional
from collections import OrderedDict
from threading import Lock
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import get_settings

settings = get_settings()

security = HTTPBearer(auto_error=False)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=settings.redis.url if settings.redis.url else "memory://",
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """输入验证中间件 - 防止注入攻击"""

    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|ALTER|CREATE)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bor\b\s+1\s*=\s*1)",
        r"(\band\b\s+1\s*=\s*1)",
        r"(\bxor\b\s+1\s*=\s*1)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
    ]

    def __init__(self, app):
        super().__init__(app)
        self.sql_regex = re.compile("|".join(self.SQL_INJECTION_PATTERNS), re.IGNORECASE)
        self.xss_regex = re.compile("|".join(self.XSS_PATTERNS), re.IGNORECASE)
        self.path_regex = re.compile("|".join(self.PATH_TRAVERSAL_PATTERNS), re.IGNORECASE)

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8", errors="ignore")

                    if self.sql_regex.search(body_str):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="检测到潜在的SQL注入攻击"
                        )

                    if self.xss_regex.search(body_str):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="检测到潜在的XSS攻击"
                        )

                    if self.path_regex.search(body_str):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="检测到潜在的路径遍历攻击"
                        )
            except Exception as e:
                if isinstance(e, HTTPException):
                    raise
                pass

        return await call_next(request)


class LRUTokenStore:
    """LRU令牌存储 - 自动清理过期令牌并限制大小"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store = OrderedDict()
        self._timestamps = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            if key not in self._store:
                return None

            if time.time() - self._timestamps.get(key, 0) > self.ttl_seconds:
                self._remove_key(key)
                return None

            self._store.move_to_end(key)
            return self._store[key]

    def set(self, key: str, value: str) -> None:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            else:
                self._cleanup_expired()
                if len(self._store) >= self.max_size:
                    self._evict_oldest()

            self._store[key] = value
            self._timestamps[key] = time.time()

    def _remove_key(self, key: str) -> None:
        if key in self._store:
            del self._store[key]
        if key in self._timestamps:
            del self._timestamps[key]

    def _evict_oldest(self) -> None:
        """驱逐最老的条目（LRU策略）"""
        oldest_key, _ = self._store.popitem(last=False)
        del self._timestamps[oldest_key]

    def _cleanup_expired(self) -> None:
        """清理过期的令牌"""
        now = time.time()
        expired_keys = [key for key, timestamp in self._timestamps.items()
                       if now - timestamp > self.ttl_seconds]
        for key in expired_keys:
            self._remove_key(key)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._timestamps.clear()


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF保护中间件 - 使用LRU存储防止内存泄漏"""

    def __init__(self, app, max_tokens: int = 1000, token_ttl: int = 3600):
        super().__init__(app)
        self.token_store = LRUTokenStore(max_size=max_tokens, ttl_seconds=token_ttl)

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            csrf_token = request.headers.get("X-CSRF-Token")

            if not csrf_token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="缺少CSRF令牌"
                )

            session_id = request.cookies.get("session_id")
            if not session_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无效的会话"
                )

            stored_token = self.token_store.get(session_id)
            if stored_token != csrf_token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无效的CSRF令牌"
                )

        response = await call_next(request)

        if request.method == "GET":
            session_id = request.cookies.get("session_id") or secrets.token_hex(16)
            csrf_token = secrets.token_hex(32)
            self.token_store.set(session_id, csrf_token)

            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=3600
            )
            response.headers["X-CSRF-Token"] = csrf_token

        return response


async def verify_token(credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    """验证JWT令牌"""
    if not credentials:
        return None

    try:
        from src.auth.manager import decode_token
        payload = decode_token(credentials.credentials)

        if payload.get("type") != "access":
            return None

        return payload.get("sub")
    except Exception:
        return None


def sanitize_filename(filename: str) -> str:
    """清理文件名，防止路径遍历攻击"""
    filename = re.sub(r"[^\w\s.-]", "", filename)
    filename = filename.strip(".")
    return filename


def validate_file_type(filename: str, allowed_types: list[str]) -> bool:
    """验证文件类型"""
    import os
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_types


def validate_file_size(size: int, max_size: int) -> bool:
    """验证文件大小"""
    return size <= max_size


ALLOWED_IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]
ALLOWED_VIDEO_TYPES = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
ALLOWED_AUDIO_TYPES = [".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"]

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
