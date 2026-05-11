"""HydraFlow AI 自定义异常体系"""


class HydraFlowError(Exception):
    """HydraFlow AI 基础异常"""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ConfigError(HydraFlowError):
    """配置相关错误"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="CONFIG_ERROR", details=details)


class ModelNotFoundError(HydraFlowError):
    """模型未找到错误"""

    def __init__(self, model_name: str, details: dict | None = None):
        super().__init__(
            f"模型未找到: {model_name}",
            code="MODEL_NOT_FOUND",
            details=details or {"model_name": model_name},
        )


class SkillNotFoundError(HydraFlowError):
    """技能未找到错误"""

    def __init__(self, skill_id: str, details: dict | None = None):
        super().__init__(
            f"技能未找到: {skill_id}",
            code="SKILL_NOT_FOUND",
            details=details or {"skill_id": skill_id},
        )


class IntentParseError(HydraFlowError):
    """意图解析错误"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="INTENT_PARSE_ERROR", details=details)


class GenerationError(HydraFlowError):
    """生成错误"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="GENERATION_ERROR", details=details)


class APIKeyError(HydraFlowError):
    """API 密钥错误"""

    def __init__(self, provider: str, details: dict | None = None):
        super().__init__(
            f"API 密钥未配置: {provider}",
            code="API_KEY_ERROR",
            details=details or {"provider": provider},
        )


class WorkflowError(HydraFlowError):
    """工作流错误"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, code="WORKFLOW_ERROR", details=details)
