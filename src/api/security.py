"""安全中间件和配置 - 防止常见Web攻击"""

import re
import secrets
from typing import Optional
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


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF保护中间件"""

    def __init__(self, app):
        super().__init__(app)
        self.csrf_tokens = {}

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
            
            if self.csrf_tokens.get(session_id) != csrf_token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无效的CSRF令牌"
                )
        
        response = await call_next(request)
        
        if request.method == "GET":
            session_id = request.cookies.get("session_id") or secrets.token_hex(16)
            csrf_token = secrets.token_hex(32)
            self.csrf_tokens[session_id] = csrf_token
            
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