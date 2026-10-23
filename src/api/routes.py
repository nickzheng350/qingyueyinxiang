"""API 路由定义"""

from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from src.intent_parser.factory import IntentParserFactory
from src.prompt_engine.engine import PromptEngine
from src.model_dispatcher.dispatcher import ModelDispatcher
from src.skills.skill_manager import SkillManager
from src.core.config import get_config, get_settings
from src.core.exceptions import ModelNotFoundError, NetworkError
from src.core.stability import get_stability_manager
from src.task_engine import get_task_executor, TaskType
from src.persistence import get_storage
from src.auth import AuthUser, get_auth_manager
from src.rag import get_default_rag_engine
from src.network import get_http_client

api_router = APIRouter()


class ParseRequest(BaseModel):
    text: str = Field(..., description="用户输入文本")
    parser: str = Field(default="qwen2.5", description="解析器名称")


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="生成提示词")
    parser: str = Field(default="qwen2.5", description="解析器名称")
    style: str = Field(default="", description="风格名称")
    negative_prompt: str = Field(default="", description="负面提示词")
    model: str = Field(default="", description="指定模型ID")
    parameters: dict = Field(default_factory=dict, description="生成参数")


class SkillInstallRequest(BaseModel):
    path: str = Field(..., description="技能路径")
    skill_type: str = Field(default="local", description="技能类型")


@api_router.post("/intent/parse")
async def parse_intent(request: ParseRequest):
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
async def generate(request: GenerateRequest):
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
async def list_models(category: str = "", source: str = "", function_type: str = "", by_intent: str = ""):
    dispatcher = ModelDispatcher()
    models = dispatcher.list_models(
        category=category or None,
        source=source or None,
        function_type=function_type or None,
        by_intent=by_intent or None,
    )
    return {"models": models, "total": len(models)}


@api_router.get("/models/validate")
async def validate_all_models():
    """验证所有模型配置完整性"""
    dispatcher = ModelDispatcher()
    return dispatcher.validate_models()


@api_router.get("/models/stats")
async def get_model_statistics(model_id: str = ""):
    """获取模型统计信息。

    必须注册在 /models/{model_id} 之前，否则 "stats" 会被当成 model_id 吞掉。
    model_id 为空返回整体统计，否则返回该模型详情。
    """
    dispatcher = ModelDispatcher()
    if model_id:
        try:
            model = dispatcher.get_model(model_id)
        except ModelNotFoundError:
            raise HTTPException(status_code=404, detail="模型未找到")
        return {"stats": model, "total": 1}
    stats = dispatcher.get_statistics()
    return {"stats": stats, "total": stats.get("total_models", 0)}


@api_router.get("/models/{model_id}")
async def get_model(model_id: str):
    dispatcher = ModelDispatcher()
    try:
        model = dispatcher.get_model(model_id)
        return {"id": model_id, **model}
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@api_router.get("/styles")
async def list_styles():
    engine = PromptEngine()
    styles = engine.list_styles()
    return {"styles": styles, "total": len(styles)}


@api_router.get("/parsers")
async def list_parsers():
    factory = IntentParserFactory()
    parsers = factory.list_parsers()
    return {"parsers": parsers, "total": len(parsers)}


@api_router.get("/skills")
async def list_skills(skill_type: str = ""):
    manager = SkillManager()
    if skill_type:
        skills = manager.list_skills_by_type(skill_type)
    else:
        skills = manager.list_skills()
    return {"skills": skills, "total": len(skills)}


@api_router.post("/skills/install")
async def install_skill(request: SkillInstallRequest):
    manager = SkillManager()
    result = manager.install_skill_from_path(request.path, request.skill_type)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@api_router.delete("/skills/{skill_id}")
async def uninstall_skill(skill_id: str):
    manager = SkillManager()
    try:
        result = manager.uninstall_skill(skill_id)
        return result
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@api_router.get("/system/info")
async def system_info():
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
async def system_health():
    stability = get_stability_manager()
    return {
        "health_score": stability.get_health_score(),
        "error_statistics": stability.get_error_statistics(),
    }


@api_router.get("/types")
async def get_type_hierarchy():
    """获取类型系统层次结构"""
    dispatcher = ModelDispatcher()
    return dispatcher.get_type_info()


@api_router.post("/types/validate")
async def validate_intent_model(request: dict):
    """验证意图与模型的兼容性"""
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


# ============ 任务相关端点 ============

class TaskSubmitRequest(BaseModel):
    prompt: str = Field(..., description="生成提示词")
    task_type: str = Field(..., description="任务类型")
    model_id: str = Field(..., description="模型ID")
    parameters: dict = Field(default_factory=dict, description="生成参数")


@api_router.post("/tasks")
async def submit_task(request: TaskSubmitRequest):
    """提交生成任务"""
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
    
    # 保存到持久化存储
    storage = get_storage()
    task_info = executor.get_task_info(task_id)
    if task_info:
        storage.save_task(task_info)
    
    return {"task_id": task_id, "status": "pending"}


@api_router.get("/tasks")
async def list_tasks(
    status: str = "",
    task_type: str = "",
    limit: int = 50,
    offset: int = 0
):
    """列出任务"""
    executor = get_task_executor()
    tasks = executor.list_tasks(status=status or None, task_type=task_type or None, limit=limit, offset=offset)
    return {"tasks": tasks, "total": len(tasks)}


@api_router.get("/tasks/statistics")
async def get_task_statistics():
    """获取任务统计"""
    executor = get_task_executor()
    return executor.get_task_statistics()


@api_router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """获取任务状态"""
    executor = get_task_executor()
    task_info = executor.get_task_info(task_id)
    
    if not task_info:
        # 尝试从持久化存储恢复
        storage = get_storage()
        task_info = storage.get_task(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    return task_info


@api_router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """取消或删除任务"""
    executor = get_task_executor()
    storage = get_storage()
    
    # 先尝试取消运行中的任务
    cancelled = await executor.cancel_task(task_id)
    
    # 删除任务记录
    deleted = storage.delete_task(task_id)
    
    if not cancelled and not deleted:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    return {"success": True, "cancelled": cancelled, "deleted": deleted}


# ============ 技能执行端点 ============

class SkillExecuteRequest(BaseModel):
    skill_id: str = Field(..., description="技能 ID")
    parameters: dict = Field(default_factory=dict, description="执行参数")


@api_router.post("/skills/execute")
async def execute_skill(request: SkillExecuteRequest):
    """执行技能"""
    skill_manager = SkillManager()
    result = skill_manager.execute_skill(
        request.skill_id,
        **request.parameters
    )
    return result


@api_router.get("/skills/{skill_id}")
async def get_skill(skill_id: str):
    """获取技能详情"""
    skill_manager = SkillManager()
    try:
        skill = skill_manager.get_skill(skill_id)
        return skill
    except (ValueError, FileNotFoundError, KeyError) as e:
        raise HTTPException(status_code=404, detail=f"技能未找到：{skill_id}")


# ============ 用户认证端点 ============

class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class RegisterRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    email: Optional[str] = Field(None, description="邮箱")
    role: str = Field(default="user", description="角色")


def resolve_token(header: Optional[str]) -> str:
    """校验 Authorization 头并返回令牌，缺失或格式错误抛 401"""
    if not header or not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    return header[7:]


def current_user(token: str) -> AuthUser:
    """由令牌解析用户。

    令牌无效或用户已被删除时抛 401——这里必须判空，
    否则会出现「令牌有效但用户不存在」导致的 500。
    """
    auth_manager = get_auth_manager()
    username = auth_manager.verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效的令牌")
    user = auth_manager.get_user(username)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def require_admin(token: str) -> AuthUser:
    """校验令牌并要求管理员角色"""
    user = current_user(token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    return user


class UpdateUserRequest(BaseModel):
    email: Optional[str] = Field(None, description="邮箱")
    role: Optional[str] = Field(None, description="角色")
    enabled: Optional[bool] = Field(None, description="是否启用")


@api_router.post("/auth/login")
async def login(request: LoginRequest):
    """用户登录"""
    auth_manager = get_auth_manager()
    token = auth_manager.authenticate(request.username, request.password)
    
    if not token:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    user = auth_manager.get_user(request.username)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
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
async def logout(token: str = Header(None, alias="Authorization")):
    """用户登出"""
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    token = token[7:]  # 移除 "Bearer " 前缀
    auth_manager = get_auth_manager()
    
    if auth_manager.logout(token):
        return {"success": True, "message": "登出成功"}
    else:
        raise HTTPException(status_code=401, detail="无效的令牌")


@api_router.post("/auth/register")
async def register(request: RegisterRequest):
    """注册新用户"""
    auth_manager = get_auth_manager()
    
    # 检查用户是否已存在
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
async def get_current_user(token: str = Header(None, alias="Authorization")):
    """获取当前用户信息"""
    user = current_user(resolve_token(token))
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
async def list_users(token: str = Header(None, alias="Authorization")):
    """列出所有用户（管理员）"""
    require_admin(resolve_token(token))
    users = get_auth_manager().list_users()
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
async def update_user(
    username: str,
    request: UpdateUserRequest,
    token: str = Header(None, alias="Authorization")
):
    """更新用户信息（管理员）"""
    require_admin(resolve_token(token))
    auth_manager = get_auth_manager()

    update_data: dict[str, Any] = {}
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
async def delete_user(
    username: str,
    token: str = Header(None, alias="Authorization")
):
    """删除用户（管理员）"""
    require_admin(resolve_token(token))
    auth_manager = get_auth_manager()

    if auth_manager.delete_user(username):
        return {"success": True, "message": "用户已删除"}
    else:
        raise HTTPException(status_code=404, detail="用户未找到")


# ==================== RAG 知识库 ====================


class RagDocumentsRequest(BaseModel):
    documents: list[str] = Field(..., description="文档内容列表")
    metadata: Optional[dict] = Field(None, description="共享元数据")


class RagQueryRequest(BaseModel):
    question: str = Field(..., description="查询问题")
    top_k: int = Field(5, ge=1, le=50, description="返回条数")


@api_router.post("/rag/documents")
async def add_rag_documents(request: RagDocumentsRequest):
    """向知识库添加文档"""
    engine = get_default_rag_engine()
    added = await engine.add_documents(request.documents, metadata=request.metadata)
    return {"success": True, "added": added, "total": await engine.document_count()}


@api_router.get("/rag/documents/count")
async def rag_document_count():
    """知识库文档数量"""
    engine = get_default_rag_engine()
    return {"count": await engine.document_count()}


@api_router.post("/rag/query")
async def query_rag(request: RagQueryRequest):
    """检索知识库，返回来源与拼接好的上下文"""
    engine = get_default_rag_engine()
    result = await engine.query(request.question, top_k=request.top_k)
    return result


@api_router.delete("/rag/documents/{doc_id}")
async def delete_rag_document(doc_id: str):
    """删除知识库文档"""
    engine = get_default_rag_engine()
    if not await engine.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="文档未找到")
    return {"success": True, "message": "文档已删除"}


# ==================== 本地推理服务探测 ====================


@api_router.get("/system/providers")
async def list_providers():
    """探测本地推理服务（LM Studio / Ollama）是否可用"""
    settings = get_settings()
    targets = {
        "lm_studio": f"{settings.lm_studio_api_base}/models",
        "ollama": f"{settings.ollama_api_base}/models",
    }

    client = get_http_client()
    providers = []
    for name, url in targets.items():
        try:
            response = await client.get(url)
            providers.append({"name": name, "url": url, "available": response.ok})
        except (NetworkError, OSError, httpx.HTTPError) as exc:
            providers.append({
                "name": name,
                "url": url,
                "available": False,
                "error": str(exc),
            })
    return {"providers": providers}
