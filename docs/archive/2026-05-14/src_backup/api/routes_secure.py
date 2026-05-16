"""安全 API 路由 - 带认证、授权和速率限制"""

from typing import Optional, get_type_hints

try:
    from fastapi import APIRouter, HTTPException, Header, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    class APIRouter:
        def include_router(self, router):
            pass
    
    class HTTPException(Exception):
        pass
    
    def Header(default=None):
        return default
    
    def Depends(func=None):
        return func
    
    class HTTPBearer:
        def __init__(self, auto_error=False):
            pass
        
        def __call__(self, *args, **kwargs):
            return None
    
    class HTTPAuthorizationCredentials:
        pass
    
    status = type('status', (), {'HTTP_401_UNAUTHORIZED': 401, 'HTTP_403_FORBIDDEN': 403})

try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    class Field:
        def __init__(self, default=None, **kwargs):
            self.default = default
    
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class BaseModel:
        def __init__(self, **kwargs):
            hints = get_type_hints(self.__class__)
            for name, hint_type in hints.items():
                value = kwargs.get(name)
                if value is not None:
                    setattr(self, name, value)
                elif hasattr(self.__class__, name):
                    setattr(self, name, getattr(self.__class__, name))

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except ImportError:
    class Limiter:
        def __init__(self, key_func):
            pass
        
        def __call__(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    
    def get_remote_address(request):
        return "127.0.0.1"

from src.intent_parser.factory import IntentParserFactory
from src.prompt_engine.engine import PromptEngine
from src.model_dispatcher.dispatcher import ModelDispatcher
from src.skills.skill_manager import SkillManager
from src.core.config import get_config
from src.core.stability import get_stability_manager
from src.task_engine import get_task_executor, TaskType
from src.persistence import get_storage
from src.auth import get_auth_manager
from src.api.security import limiter

security = HTTPBearer(auto_error=False)

api_router = APIRouter()


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """获取当前认证用户"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_manager = get_auth_manager()
    username = auth_manager.verify_token(credentials.credentials)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_manager.get_user(username)
    if not user or not user.enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    
    return user


async def require_admin(current_user = Depends(get_current_user)):
    """要求管理员权限"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="用户输入文本")
    parser: str = Field(default="qwen2.5", max_length=100, description="解析器名称")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('文本不能为空')
        return v.strip()


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000, description="生成提示词")
    parser: str = Field(default="qwen2.5", max_length=100, description="解析器名称")
    style: str = Field(default="", max_length=200, description="风格名称")
    negative_prompt: str = Field(default="", max_length=2000, description="负面提示词")
    model: str = Field(default="", max_length=100, description="指定模型ID")
    parameters: dict = Field(default_factory=dict, description="生成参数")


class SkillInstallRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=500, description="技能路径")
    skill_type: str = Field(default="local", max_length=50, description="技能类型")


@api_router.post("/intent/parse")
@limiter.limit("60/minute")
async def parse_intent(request: ParseRequest, current_user = Depends(get_current_user)):
    """解析用户意图（需要认证）"""
    config = get_config()
    intent_config = config.get("intent_parser", {})

    factory = IntentParserFactory()
    factory.enable_cache(intent_config.get("enable_cache", True))

    result = factory.parse(request.text, parser_name=request.parser, use_cache=intent_config.get("enable_cache", True))

    return {
        "intent": result.intent.value,
        "style": result.style,
        "prompt": result.prompt,
        "negative_prompt": result.negative_prompt,
        "parameters": result.parameters,
        "model_suggestions": result.model_suggestions,
        "confidence": result.confidence,
        "metadata": result.metadata,
        "parsing_info": {
            "llm_used": result.metadata.get("llm_parsed", False),
            "skip_llm_reason": result.metadata.get("skip_llm_reason", None),
            "fallback": result.metadata.get("fallback", False),
        },
        "cache_stats": factory.get_cache_stats() if intent_config.get("enable_cache", True) else None,
    }


@api_router.post("/generate")
@limiter.limit("30/minute")
async def generate(request: GenerateRequest, current_user = Depends(get_current_user)):
    """生成内容（需要认证）"""
    factory = IntentParserFactory()
    parse_result = factory.parse(request.prompt, parser_name=request.parser)

    style = request.style or parse_result.style
    prompt = parse_result.prompt or request.prompt
    negative = request.negative_prompt or parse_result.negative_prompt

    engine = PromptEngine()
    enhanced = engine.build_prompt(
        text=prompt,
        style=style,
        negative_prompt=negative,
    )

    dispatcher = ModelDispatcher()
    if request.model:
        try:
            model_info = dispatcher.get_model(request.model)
            selected_model = {"id": request.model, **model_info}
        except (ValueError, KeyError):
            selected_model = dispatcher.select_model(
                parse_result.intent.value,
                parse_result.model_suggestions,
            )
    else:
        selected_model = dispatcher.select_model(
            parse_result.intent.value,
            parse_result.model_suggestions,
        )

    return {
        "status": "ready",
        "intent": parse_result.intent.value,
        "style": style,
        "prompt": enhanced["prompt"],
        "negative_prompt": enhanced["negative_prompt"],
        "model": selected_model,
        "parameters": {**parse_result.parameters, **request.parameters},
        "confidence": parse_result.confidence,
    }


@api_router.get("/models")
@limiter.limit("100/minute")
async def list_models(
    category: str = "",
    source: str = "",
    function_type: str = "",
    by_intent: str = "",
    current_user = Depends(get_current_user)
):
    """列出模型（需要认证）"""
    dispatcher = ModelDispatcher()
    models = dispatcher.list_models(
        category=category or None,
        source=source or None,
        function_type=function_type or None,
        by_intent=by_intent or None,
    )
    return {"models": models, "total": len(models)}


@api_router.get("/models/validate")
@limiter.limit("10/minute")
async def validate_all_models(current_user = Depends(require_admin)):
    """验证所有模型配置完整性（仅管理员）"""
    dispatcher = ModelDispatcher()
    return dispatcher.validate_models()


@api_router.get("/models/{model_id}")
@limiter.limit("100/minute")
async def get_model(model_id: str, current_user = Depends(get_current_user)):
    """获取模型详情（需要认证）"""
    dispatcher = ModelDispatcher()
    try:
        model = dispatcher.get_model(model_id)
        return {"id": model_id, **model}
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=404, detail="模型未找到")


@api_router.get("/styles")
@limiter.limit("100/minute")
async def list_styles(current_user = Depends(get_current_user)):
    """列出风格（需要认证）"""
    engine = PromptEngine()
    styles = engine.list_styles()
    return {"styles": styles, "total": len(styles)}


@api_router.get("/parsers")
@limiter.limit("100/minute")
async def list_parsers(current_user = Depends(get_current_user)):
    """列出解析器（需要认证）"""
    factory = IntentParserFactory()
    parsers = factory.list_parsers()
    return {"parsers": parsers, "total": len(parsers)}


@api_router.get("/skills")
@limiter.limit("100/minute")
async def list_skills(
    skill_type: str = "",
    current_user = Depends(get_current_user)
):
    """列出技能（需要认证）"""
    manager = SkillManager()
    if skill_type:
        skills = manager.list_skills_by_type(skill_type)
    else:
        skills = manager.list_skills()
    return {"skills": skills, "total": len(skills)}


@api_router.post("/skills/install")
@limiter.limit("10/minute")
async def install_skill(
    request: SkillInstallRequest,
    current_user = Depends(require_admin)
):
    """安装技能（仅管理员）"""
    manager = SkillManager()
    result = manager.install_skill_from_path(request.path, request.skill_type)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@api_router.delete("/skills/{skill_id}")
@limiter.limit("10/minute")
async def uninstall_skill(
    skill_id: str,
    current_user = Depends(require_admin)
):
    """卸载技能（仅管理员）"""
    manager = SkillManager()
    try:
        result = manager.uninstall_skill(skill_id)
        return result
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@api_router.get("/system/info")
@limiter.limit("10/minute")
async def system_info(current_user = Depends(require_admin)):
    """系统信息（仅管理员）"""
    config = get_config()
    stability = get_stability_manager()
    dispatcher = ModelDispatcher()
    skill_manager = SkillManager()
    return {
        "version": "1.1.0",
        "name": "HydraFlow AI",
        "health_score": stability.get_health_score(),
        "error_statistics": stability.get_error_statistics(),
        "models": dispatcher.get_statistics(),
        "skills": skill_manager.get_statistics(),
    }


@api_router.get("/system/health")
@limiter.limit("30/minute")
async def system_health(current_user = Depends(get_current_user)):
    """系统健康检查（需要认证）"""
    stability = get_stability_manager()
    return {
        "health_score": stability.get_health_score(),
        "error_statistics": stability.get_error_statistics(),
    }


@api_router.get("/types")
@limiter.limit("100/minute")
async def get_type_hierarchy(current_user = Depends(get_current_user)):
    """获取类型系统层次结构（需要认证）"""
    dispatcher = ModelDispatcher()
    return dispatcher.get_type_info()


@api_router.post("/types/validate")
@limiter.limit("30/minute")
async def validate_intent_model(
    request: dict,
    current_user = Depends(get_current_user)
):
    """验证意图与模型的兼容性（需要认证）"""
    intent = request.get("intent")
    model_id = request.get("model_id")
    
    if not intent or not model_id:
        raise HTTPException(status_code=400, detail="缺少参数: intent 和 model_id")
    
    dispatcher = ModelDispatcher()
    try:
        model = dispatcher.get_model(model_id)
        return {
            "valid": True,
            "intent": intent,
            "model_id": model_id,
            "model_category": model.get("category"),
            "model_function": model.get("function_type"),
        }
    except (ValueError, KeyError) as e:
        return {
            "valid": False,
            "intent": intent,
            "model_id": model_id,
            "error": str(e),
        }


class TaskSubmitRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000, description="生成提示词")
    task_type: str = Field(..., max_length=50, description="任务类型")
    model_id: str = Field(..., max_length=100, description="模型ID")
    parameters: dict = Field(default_factory=dict, description="生成参数")


@api_router.post("/tasks")
@limiter.limit("20/minute")
async def submit_task(
    request: TaskSubmitRequest,
    current_user = Depends(get_current_user)
):
    """提交生成任务（需要认证）"""
    try:
        task_type = TaskType(request.task_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的任务类型: {request.task_type}")
    
    executor = get_task_executor()
    task_id = await executor.submit_task(
        task_type=task_type,
        prompt=request.prompt,
        parameters=request.parameters,
        model_id=request.model_id,
    )
    
    storage = get_storage()
    task_info = executor.get_task_info(task_id)
    if task_info:
        storage.save_task(task_info)
    
    return {"task_id": task_id, "status": "pending"}


@api_router.get("/tasks")
@limiter.limit("100/minute")
async def list_tasks(
    status: str = "",
    task_type: str = "",
    limit: int = 50,
    offset: int = 0,
    current_user = Depends(get_current_user)
):
    """列出任务（需要认证）"""
    executor = get_task_executor()
    tasks = executor.list_tasks(status=status or None, task_type=task_type or None, limit=limit, offset=offset)
    return {"tasks": tasks, "total": len(tasks)}


@api_router.get("/tasks/statistics")
@limiter.limit("30/minute")
async def get_task_statistics(current_user = Depends(get_current_user)):
    """获取任务统计（需要认证）"""
    executor = get_task_executor()
    return executor.get_task_statistics()


@api_router.get("/tasks/{task_id}")
@limiter.limit("100/minute")
async def get_task(task_id: str, current_user = Depends(get_current_user)):
    """获取任务状态（需要认证）"""
    executor = get_task_executor()
    task_info = executor.get_task_info(task_id)
    
    if not task_info:
        storage = get_storage()
        task_info = storage.get_task(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    return task_info


@api_router.delete("/tasks/{task_id}")
@limiter.limit("20/minute")
async def cancel_task(task_id: str, current_user = Depends(get_current_user)):
    """取消或删除任务（需要认证）"""
    executor = get_task_executor()
    storage = get_storage()
    
    cancelled = await executor.cancel_task(task_id)
    deleted = storage.delete_task(task_id)
    
    if not cancelled and not deleted:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    return {"success": True, "cancelled": cancelled, "deleted": deleted}


@api_router.get("/models/stats")
@limiter.limit("30/minute")
async def get_model_statistics(
    model_id: str = "",
    current_user = Depends(get_current_user)
):
    """获取模型使用统计（需要认证）"""
    storage = get_storage()
    stats = storage.get_model_stats(model_id if model_id else None)
    return {"stats": stats, "total": len(stats)}


class SkillExecuteRequest(BaseModel):
    skill_id: str = Field(..., min_length=1, max_length=100, description="技能 ID")
    parameters: dict = Field(default_factory=dict, description="执行参数")


@api_router.post("/skills/execute")
@limiter.limit("30/minute")
async def execute_skill(
    request: SkillExecuteRequest,
    current_user = Depends(get_current_user)
):
    """执行技能（需要认证）"""
    skill_manager = SkillManager()
    result = skill_manager.execute_skill(
        request.skill_id,
        **request.parameters
    )
    return result


@api_router.get("/skills/{skill_id}")
@limiter.limit("100/minute")
async def get_skill(skill_id: str, current_user = Depends(get_current_user)):
    """获取技能详情（需要认证）"""
    skill_manager = SkillManager()
    try:
        skill = skill_manager.get_skill(skill_id)
        return skill
    except (ValueError, FileNotFoundError, KeyError) as e:
        raise HTTPException(status_code=404, detail=f"技能未找到：{skill_id}")


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: Optional[str] = Field(None, max_length=255, description="邮箱")
    role: str = Field(default="user", max_length=50, description="角色")


class UpdateUserRequest(BaseModel):
    email: Optional[str] = Field(None, max_length=255, description="邮箱")
    role: Optional[str] = Field(None, max_length=50, description="角色")
    enabled: Optional[bool] = Field(None, description="是否启用")


@api_router.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: LoginRequest):
    """用户登录（公开端点，有速率限制）"""
    auth_manager = get_auth_manager()
    token = auth_manager.authenticate(request.username, request.password)
    
    if not token:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    user = auth_manager.get_user(request.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    }


@api_router.post("/auth/logout")
@limiter.limit("30/minute")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """用户登出（需要认证）"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    auth_manager = get_auth_manager()
    
    if auth_manager.logout(credentials.credentials):
        return {"success": True, "message": "登出成功"}
    else:
        raise HTTPException(status_code=401, detail="无效的令牌")


@api_router.post("/auth/register")
@limiter.limit("5/minute")
async def register(request: RegisterRequest):
    """注册新用户（公开端点，严格速率限制）"""
    auth_manager = get_auth_manager()
    
    if auth_manager.get_user(request.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user = auth_manager.create_user(
        username=request.username,
        password=request.password,
        email=request.email,
        role=request.role
    )
    
    if user:
        return {
            "success": True,
            "message": "用户注册成功",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
    else:
        raise HTTPException(status_code=500, detail="用户注册失败")


@api_router.get("/auth/me")
@limiter.limit("60/minute")
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户信息（需要认证）"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    auth_manager = get_auth_manager()
    username = auth_manager.verify_token(credentials.credentials)
    
    if not username:
        raise HTTPException(status_code=401, detail="无效的令牌")
    
    user = auth_manager.get_user(username)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "enabled": user.enabled,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None
    }


@api_router.get("/auth/users")
@limiter.limit("30/minute")
async def list_users(current_user = Depends(require_admin)):
    """列出所有用户（仅管理员）"""
    auth_manager = get_auth_manager()
    users = auth_manager.list_users()
    return {
        "users": [{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "enabled": u.enabled,
            "created_at": u.created_at.isoformat(),
            "last_login": u.last_login.isoformat() if u.last_login else None
        } for u in users],
        "total": len(users)
    }


@api_router.put("/auth/users/{username}")
@limiter.limit("20/minute")
async def update_user(
    username: str,
    request: UpdateUserRequest,
    current_user = Depends(require_admin)
):
    """更新用户信息（仅管理员）"""
    auth_manager = get_auth_manager()
    
    update_data = {}
    if request.email is not None:
        update_data["email"] = request.email
    if request.role is not None:
        update_data["role"] = request.role
    if request.enabled is not None:
        update_data["enabled"] = request.enabled
    
    if auth_manager.update_user(username, **update_data):
        return {"success": True, "message": "用户信息更新成功"}
    else:
        raise HTTPException(status_code=404, detail="用户未找到")


@api_router.delete("/auth/users/{username}")
@limiter.limit("10/minute")
async def delete_user(
    username: str,
    current_user = Depends(require_admin)
):
    """删除用户（仅管理员）"""
    auth_manager = get_auth_manager()
    
    if auth_manager.delete_user(username):
        return {"success": True, "message": "用户已删除"}
    else:
        raise HTTPException(status_code=404, detail="用户未找到")
