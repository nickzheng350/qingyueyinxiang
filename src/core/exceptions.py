"""清悦印象 AI 异常模块 - 完整的异常层次结构"""

from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class ErrorResponse:
    """标准错误响应格式"""
    error_code: str
    detail: str
    message: str
    status_code: int = 500
    request_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "error": self.error_code,
            "detail": self.detail,
            "message": self.message,
            "status_code": self.status_code,
        }
        if self.request_id:
            result["request_id"] = self.request_id
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class QingYueYinXiangError(Exception):
    """基础异常 - 所有自定义异常的基类"""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    detail: str = "An internal error occurred"
    message: str = ""

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.message = message or self.__class__.__doc__ or ""
        if detail:
            self.detail = detail
        if error_code:
            self.error_code = error_code
        self._metadata = metadata or {}
        super().__init__(self.message)

    def to_error_response(self, request_id: Optional[str] = None) -> ErrorResponse:
        return ErrorResponse(
            error_code=self.error_code,
            detail=self.detail,
            message=self.message,
            status_code=self.status_code,
            request_id=request_id,
            metadata=self._metadata,
        )


class AuthenticationError(QingYueYinXiangError):
    """认证错误 - 用户身份验证失败"""
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"
    detail = "Authentication failed"


class AuthorizationError(QingYueYinXiangError):
    """授权错误 - 用户权限不足"""
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"
    detail = "Insufficient permissions"


class ValidationError(QingYueYinXiangError):
    """验证错误 - 输入数据验证失败"""
    status_code = 422
    error_code = "VALIDATION_ERROR"
    detail = "Request validation failed"


class NotFoundError(QingYueYinXiangError):
    """未找到错误 - 请求的资源不存在"""
    status_code = 404
    error_code = "NOT_FOUND"
    detail = "Resource not found"


class ResourceNotFoundError(NotFoundError):
    """资源未找到错误"""
    pass


class TaskError(QingYueYinXiangError):
    """任务错误 - 任务执行相关错误"""
    status_code = 500
    error_code = "TASK_ERROR"
    detail = "Task execution failed"


class TaskNotFoundError(ResourceNotFoundError):
    """任务未找到错误"""
    error_code = "TASK_NOT_FOUND"
    detail = "Task not found"


class ModelError(QingYueYinXiangError):
    """模型错误 - 模型加载或调用错误"""
    status_code = 500
    error_code = "MODEL_ERROR"
    detail = "Model operation failed"


class ModelNotFoundError(ResourceNotFoundError):
    """模型未找到错误"""
    error_code = "MODEL_NOT_FOUND"
    detail = "Model not found"


class StorageError(QingYueYinXiangError):
    """存储错误 - 文件存储或数据库错误"""
    status_code = 500
    error_code = "STORAGE_ERROR"
    detail = "Storage operation failed"


class ConfigurationError(QingYueYinXiangError):
    """配置错误 - 系统配置问题"""
    status_code = 500
    error_code = "CONFIGURATION_ERROR"
    detail = "Configuration error"


class DependencyError(QingYueYinXiangError):
    """依赖错误 - 依赖服务或模块问题"""
    status_code = 503
    error_code = "DEPENDENCY_ERROR"
    detail = "Dependency service unavailable"


class NetworkError(QingYueYinXiangError):
    """网络错误 - 网络请求失败"""
    status_code = 503
    error_code = "NETWORK_ERROR"
    detail = "Network request failed"


class ConfigError(ConfigurationError):
    """配置错误（兼容旧版）"""
    pass


class SkillNotFoundError(ResourceNotFoundError):
    """技能未找到错误"""
    error_code = "SKILL_NOT_FOUND"
    detail = "Skill not found"


class IntentParseError(QingYueYinXiangError):
    """意图解析错误 - 解析用户意图失败"""
    status_code = 500
    error_code = "INTENT_PARSE_ERROR"
    detail = "Failed to parse intent"


class GenerationError(QingYueYinXiangError):
    """生成错误 - 内容生成失败"""
    status_code = 500
    error_code = "GENERATION_ERROR"
    detail = "Content generation failed"


class RateLimitError(QingYueYinXiangError):
    """限流错误 - 请求频率超限"""
    status_code = 429
    error_code = "RATE_LIMIT_ERROR"
    detail = "Rate limit exceeded"


class ParserNotFoundError(ResourceNotFoundError):
    """解析器未找到错误"""
    error_code = "PARSER_NOT_FOUND"
    detail = "Parser not found"


class StyleNotFoundError(ResourceNotFoundError):
    """风格未找到错误"""
    error_code = "STYLE_NOT_FOUND"
    detail = "Style not found"


class CacheError(QingYueYinXiangError):
    """缓存错误 - 缓存操作失败"""
    status_code = 500
    error_code = "CACHE_ERROR"
    detail = "Cache operation failed"
