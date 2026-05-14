"""模型配置 API 路由"""

from typing import Optional, get_type_hints

try:
    from fastapi import APIRouter, HTTPException
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = object

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
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

router = APIRouter() if FASTAPI_AVAILABLE else object()


class ModelConfig(BaseModel):
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="Base URL")
    group_id: Optional[str] = Field(None, description="Group ID")


class ModelCreate(BaseModel):
    id: str = Field(..., description="模型ID")
    name: str = Field(..., description="模型名称")
    provider: str = Field(..., description="提供商")
    category: str = Field("text", description="类别")
    function_type: str = Field("text", description="功能类型")
    config: dict = Field(default_factory=dict, description="配置")
    status: str = Field("offline", description="状态")


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    enabled: Optional[bool] = None
    status: Optional[str] = None


PROVIDERS_DB = [
    {"id": "openai", "name": "OpenAI", "name_en": "OpenAI", "logo": "🤖", "category": "official"},
    {"id": "anthropic", "name": "Anthropic", "name_en": "Anthropic", "logo": "🧠", "category": "official"},
    {"id": "minimax", "name": "MiniMax", "name_en": "MiniMax", "logo": "🔷", "category": "official"},
    {"id": "ali", "name": "阿里云", "name_en": "Alibaba Cloud", "logo": "🔶", "category": "official"},
    {"id": "google", "name": "Google", "name_en": "Google", "logo": "🔵", "category": "official"},
    {"id": "ollama", "name": "Ollama", "name_en": "Ollama", "logo": "🦙", "category": "local"},
    {"id": "lmstudio", "name": "LM Studio", "name_en": "LM Studio", "logo": "💜", "category": "local"},
    {"id": "custom", "name": "自定义", "name_en": "Custom Endpoint", "logo": "⚙️", "category": "local"},
]

MODELS_DB = [
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai", "category": "text", "function_type": "text", "enabled": True, "status": "online", "config": {"api_key": "****"}},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai", "category": "text", "function_type": "text", "enabled": True, "status": "online", "config": {"api_key": "****"}},
    {"id": "claude-3-5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "anthropic", "category": "text", "function_type": "text", "enabled": True, "status": "online", "config": {"api_key": "****"}},
    {"id": "minimax-m2", "name": "MiniMax-M2", "provider": "minimax", "category": "text", "function_type": "text", "enabled": True, "status": "online", "config": {"api_key": "****", "group_id": "****"}},
    {"id": "qwen2.5", "name": "通义千问2.5", "provider": "ali", "category": "text", "function_type": "text", "enabled": False, "status": "offline", "config": {"api_key": "****"}},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "google", "category": "text", "function_type": "text", "enabled": False, "status": "offline", "config": {"api_key": "****"}},
    {"id": "llama3.1", "name": "Llama 3.1", "provider": "ollama", "category": "text", "function_type": "text", "enabled": True, "status": "online", "config": {"base_url": "http://localhost:11434"}},
    {"id": "dall-e-3", "name": "DALL-E 3", "provider": "openai", "category": "image", "function_type": "image", "enabled": True, "status": "online", "config": {"api_key": "****"}},
    {"id": "sdxl", "name": "SDXL", "provider": "custom", "category": "image", "function_type": "image", "enabled": False, "status": "offline", "config": {"base_url": "http://localhost:7860"}},
]


@router.get("/models/providers")
async def list_providers():
    """获取模型提供商列表"""
    return {"providers": PROVIDERS_DB, "total": len(PROVIDERS_DB)}


@router.get("/models")
async def list_models(
    category: str = "",
    source: str = "",
    function_type: str = "",
    provider: str = ""
):
    """获取模型列表"""
    models = MODELS_DB
    if category:
        models = [m for m in models if m.get("category") == category]
    if source:
        providers = [p["id"] for p in PROVIDERS_DB if p["category"] == source]
        models = [m for m in models if m.get("provider") in providers]
    if function_type and function_type != "all":
        models = [m for m in models if m.get("function_type") == function_type]
    if provider:
        models = [m for m in models if m.get("provider") == provider]
    return {"models": models, "total": len(models)}


@router.post("/models")
async def create_model(request: ModelCreate):
    """添加模型"""
    # 检查是否已存在
    for m in MODELS_DB:
        if m["id"] == request.id:
            if FASTAPI_AVAILABLE:
                raise HTTPException(status_code=400, detail="模型ID已存在")
            return {"status": "error", "message": "Model ID already exists"}

    new_model = {
        "id": request.id,
        "name": request.name,
        "provider": request.provider,
        "category": request.category,
        "function_type": request.function_type,
        "enabled": True,
        "status": request.status,
        "config": request.config,
    }
    MODELS_DB.append(new_model)
    return {"status": "success", "model": new_model}


@router.get("/models/{model_id}")
async def get_model(model_id: str):
    """获取模型详情"""
    for m in MODELS_DB:
        if m["id"] == model_id:
            return m
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="模型未找到")
    return None


@router.put("/models/{model_id}")
async def update_model(model_id: str, request: ModelUpdate):
    """更新模型"""
    for m in MODELS_DB:
        if m["id"] == model_id:
            if request.name is not None:
                m["name"] = request.name
            if request.config is not None:
                m["config"] = {**m["config"], **request.config}
            if request.enabled is not None:
                m["enabled"] = request.enabled
            if request.status is not None:
                m["status"] = request.status
            return {"status": "success", "model": m}
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="模型未找到")
    return {"status": "error"}


@router.post("/models/{model_id}/toggle")
async def toggle_model(model_id: str):
    """切换模型启用状态"""
    for m in MODELS_DB:
        if m["id"] == model_id:
            m["enabled"] = not m["enabled"]
            return {"status": "success", "enabled": m["enabled"]}
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="模型未找到")
    return {"status": "error"}


@router.post("/models/{model_id}/validate")
async def validate_model(model_id: str):
    """验证模型配置"""
    for m in MODELS_DB:
        if m["id"] == model_id:
            config = m.get("config", {})
            has_issues = []

            if m.get("provider") in ["openai", "anthropic", "google", "ali"]:
                if not config.get("api_key"):
                    has_issues.append("缺少API Key")
            if m.get("provider") in ["ollama", "lmstudio", "custom"]:
                if not config.get("base_url"):
                    has_issues.append("缺少Base URL")

            return {
                "status": "valid" if not has_issues else "invalid",
                "model_id": model_id,
                "issues": has_issues,
            }
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="模型未找到")
    return {"status": "error"}


@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """删除模型"""
    global MODELS_DB
    original_len = len(MODELS_DB)
    MODELS_DB = [m for m in MODELS_DB if m["id"] != model_id]
    if len(MODELS_DB) < original_len:
        return {"status": "success"}
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="模型未找到")
    return {"status": "error"}