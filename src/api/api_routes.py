"""API 路由定义"""

import os
import logging
from typing import Optional, get_type_hints

try:
    from fastapi import APIRouter, HTTPException, Header
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

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    class Field:
        def __init__(self, default=None, **kwargs):
            self.default = default
    
    class BaseModel:
        def __init__(self, **kwargs):
            hints = get_type_hints(self.__class__)
            for name, hint_type in hints.items():
                value = kwargs.get(name)
                if value is not None:
                    setattr(self, name, value)
                elif hasattr(self.__class__, name):
                    setattr(self, name, getattr(self.__class__, name))

from src.intent_parser.factory import IntentParserFactory
from src.prompt_engine.engine import PromptEngine
from src.model_dispatcher.dispatcher import ModelDispatcher
from src.skills.skill_manager import SkillManager
from src.core.exceptions import SkillNotFoundError
from src.core.config import get_config
from src.core.stability import get_stability_manager
from src.task_engine import get_task_executor, TaskType
from src.persistence import get_storage
from src.auth import get_auth_manager

# 导入文件管理路由
from src.api.routes.files import router as files_router
# 导入数据库管理路由
from src.api.routes.database import router as database_router
# 导入经验库路由
from src.api.routes.experience import router as experience_router
# 导入记忆路由
from src.api.routes.memory import router as memory_router
# 导入模型配置路由
from src.api.routes.models import router as models_router

api_router = APIRouter()

# 包含文件管理路由
api_router.include_router(files_router)
# 包含数据库管理路由
api_router.include_router(database_router)
# 包含经验库路由
api_router.include_router(experience_router)
# 包含记忆路由
api_router.include_router(memory_router)
# 包含模型配置路由
api_router.include_router(models_router)


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


class SkillInstallUrlRequest(BaseModel):
    url: str = Field(..., description="技能下载URL")
    skill_type: str = Field(default="downloaded", description="技能类型")


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


class RealGenerateRequest(BaseModel):
    prompt: str = Field(..., description="用户输入/提示词")
    model: str = Field(default="", description="模型ID")
    system: str = Field(default="", description="系统提示词")
    max_tokens: int = Field(default=2048, description="最大生成token数")
    temperature: float = Field(default=0.7, description="温度参数")
    stream: bool = Field(default=False, description="是否流式返回")


@api_router.post("/v1/generate")
async def real_generate(request: RealGenerateRequest):
    """真正的 AI 生成接口 - 调用实际模型

    支持:
    - OpenAI GPT 系列
    - Anthropic Claude
    - 通义千问 (Dashscope)
    - 本地 Ollama
    - 本地 LM Studio
    """
    dispatcher = ModelDispatcher()

    # 选择模型
    if request.model:
        try:
            model_info = dispatcher.get_model(request.model)
            selected_model = {"id": request.model, **model_info}
        except (ValueError, KeyError):
            selected_model = dispatcher.select_model("text_generation", None)
    else:
        selected_model = dispatcher.select_model("text_generation", None)

    model_id = selected_model.get("id", "")

    # 调用模型生成
    result = dispatcher.generate_text(
        prompt=request.prompt,
        model_id=model_id,
        intent_type="text_generation",
        model_suggestions=[request.model] if request.model else None,
        system=request.system or None,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )

    if not result.get("success", False):
        error_msg = result.get("error", "生成失败")
        # 检查是否是配置问题
        if "无可用的 AI 客户端" in error_msg or "No model" in error_msg:
            return {
                "status": "error",
                "error": f"AI 客户端未配置或模型 {model_id} 不可用。请检查：\n"
                          f"1. config/api_keys.json 中是否配置了对应的 API key\n"
                          f"2. 本地模型服务（如 Ollama/LM Studio）是否启动",
                "model": selected_model,
                "content": "",
            }
        return {
            "status": "error",
            "error": error_msg,
            "model": selected_model,
            "content": "",
        }

    return {
        "status": "success",
        "content": result.get("content", ""),
        "model": model_id,
        "provider": result.get("provider", "unknown"),
        "usage": result.get("usage", {}),
        "intent": "text_generation",
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


@api_router.get("/skills/market/search")
async def search_market_skills(query: str = "", category: str = "", limit: int = 10):
    manager = SkillManager()
    skills = manager.search_market_skills(query, category, limit)
    return {"skills": skills, "total": len(skills)}


@api_router.get("/skills/market/categories")
async def get_market_categories():
    manager = SkillManager()
    return manager.get_market_categories()


@api_router.get("/skills/market/featured")
async def get_featured_skills(limit: int = 5):
    manager = SkillManager()
    skills = manager.get_featured_skills(limit)
    return {"skills": skills, "total": len(skills)}


@api_router.post("/skills/{skill_id}/toggle")
async def toggle_skill(skill_id: str):
    manager = SkillManager()
    try:
        result = manager.toggle_skill(skill_id)
        return result
    except SkillNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@api_router.post("/skills/install")
async def install_skill(request: SkillInstallRequest):
    manager = SkillManager()
    result = manager.install_skill_from_path(request.path, request.skill_type)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@api_router.post("/skills/install/url")
async def install_skill_from_url(request: SkillInstallUrlRequest):
    manager = SkillManager()
    result = manager.install_skill_from_url(request.url, request.skill_type)
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
        "version": "2.0.0",
        "name": "清悦印象 AI",
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


# ============ 模型统计端点 ============

@api_router.get("/models/stats")
async def get_model_statistics(model_id: str = ""):
    """获取模型使用统计"""
    storage = get_storage()
    stats = storage.get_model_stats(model_id if model_id else None)
    return {"stats": stats, "total": len(stats)}


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


@api_router.get("/skills/{skill_id}/download")
async def download_skill(skill_id: str):
    """下载技能包（返回ZIP文件）"""
    skill_manager = SkillManager()
    config = get_config()
    
    try:
        # 先检查是否已安装
        try:
            skill = skill_manager.get_skill(skill_id)
            # 如果已安装，打包技能目录
            skill_path = Path(skill.get("path"))
            if skill_path.exists() and skill_path.is_dir():
                import zipfile
                import io
                
                # 创建内存中的ZIP文件
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(skill_path):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(skill_path)
                            zipf.write(file_path, arcname)
                
                zip_buffer.seek(0)
                
                from fastapi.responses import StreamingResponse
                return StreamingResponse(
                    iter([zip_buffer.getvalue()]),
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f"attachment; filename={skill_id}.zip",
                        "Content-Type": "application/zip"
                    }
                )
            else:
                raise HTTPException(status_code=404, detail=f"技能文件不存在")
        except SkillNotFoundError:
            # 技能未安装，从市场搜索
            market_skills = skill_manager.search_market_skills(query=skill_id)
            if not market_skills:
                raise HTTPException(status_code=404, detail=f"技能 {skill_id} 未找到")
            
            market_skill = market_skills[0]
            if market_skill.get("url"):
                # 从URL下载
                import httpx
                response = httpx.get(market_skill["url"], follow_redirects=True, timeout=60)
                response.raise_for_status()
                
                from fastapi.responses import StreamingResponse
                return StreamingResponse(
                    iter([response.content]),
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f"attachment; filename={skill_id}.zip",
                        "Content-Type": "application/zip"
                    }
                )
            else:
                raise HTTPException(status_code=400, detail=f"技能 {skill_id} 没有下载URL")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@api_router.post("/skills/{skill_id}/install")
async def install_skill_from_market(skill_id: str):
    """从市场安装技能"""
    logger = logging.getLogger("hydraflow.api")
    logger.info(f"=== API: 开始安装技能 ===")
    logger.info(f"技能ID: {skill_id}")
    
    skill_manager = SkillManager()
    
    try:
        # 检查是否已安装
        logger.info(f"检查技能是否已安装...")
        try:
            skill = skill_manager.get_skill(skill_id)
            logger.info(f"技能 {skill_id} 已安装，跳过安装")
            return {"status": "success", "message": f"技能 {skill_id} 已安装"}
        except SkillNotFoundError:
            logger.info(f"技能 {skill_id} 未安装，继续安装流程")
        
        # 从市场搜索技能
        logger.info(f"从市场搜索技能: {skill_id}")
        market_skills = skill_manager.search_market_skills(query=skill_id)
        if not market_skills:
            logger.error(f"技能 {skill_id} 在市场中未找到")
            raise HTTPException(status_code=404, detail=f"技能 {skill_id} 在市场中未找到")
        
        market_skill = market_skills[0]
        logger.info(f"找到市场技能: {market_skill.get('name')}")
        
        if not market_skill.get("url"):
            logger.error(f"技能 {skill_id} 没有下载URL")
            raise HTTPException(status_code=400, detail=f"技能 {skill_id} 没有下载URL")
        
        logger.info(f"下载URL: {market_skill.get('url')}")
        
        # 使用 URL 安装
        logger.info(f"开始从URL安装...")
        result = skill_manager.install_skill_from_url(market_skill["url"], "downloaded")
        
        if result["status"] == "error":
            logger.error(f"安装失败: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        
        logger.info(f"安装成功: {result}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"安装异常: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"安装失败: {str(e)}")


# ============ 用户认证端点 ============

class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class RegisterRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    email: Optional[str] = Field(None, description="邮箱")
    role: str = Field(default="user", description="角色")


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
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    token = token[7:]
    auth_manager = get_auth_manager()
    username = auth_manager.verify_token(token)
    
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
async def list_users(token: str = Header(None, alias="Authorization")):
    """列出所有用户（管理员）"""
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    token = token[7:]
    auth_manager = get_auth_manager()
    username = auth_manager.verify_token(token)
    
    if not username:
        raise HTTPException(status_code=401, detail="无效的令牌")
    
    user = auth_manager.get_user(username)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
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
async def update_user(
    username: str,
    request: UpdateUserRequest,
    token: str = Header(None, alias="Authorization")
):
    """更新用户信息（管理员）"""
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    token = token[7:]
    auth_manager = get_auth_manager()
    current_username = auth_manager.verify_token(token)
    
    if not current_username:
        raise HTTPException(status_code=401, detail="无效的令牌")
    
    current_user = auth_manager.get_user(current_username)
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
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
async def delete_user(
    username: str,
    token: str = Header(None, alias="Authorization")
):
    """删除用户（管理员）"""
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    token = token[7:]
    auth_manager = get_auth_manager()
    current_username = auth_manager.verify_token(token)
    
    if not current_username:
        raise HTTPException(status_code=401, detail="无效的令牌")
    
    current_user = auth_manager.get_user(current_username)
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    
    if auth_manager.delete_user(username):
        return {"success": True, "message": "用户已删除"}
    else:
        raise HTTPException(status_code=404, detail="用户未找到")
