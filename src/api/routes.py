"""API 路由定义"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.intent_parser.factory import IntentParserFactory
from src.prompt_engine.engine import PromptEngine
from src.model_dispatcher.dispatcher import ModelDispatcher
from src.skills.skill_manager import SkillManager
from src.core.config import get_config
from src.core.stability import get_stability_manager

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
    factory = IntentParserFactory()
    result = factory.parse(request.text, parser_name=request.parser)
    return {
        "intent": result.intent.value,
        "style": result.style,
        "prompt": result.prompt,
        "negative_prompt": result.negative_prompt,
        "parameters": result.parameters,
        "model_suggestions": result.model_suggestions,
        "confidence": result.confidence,
        "metadata": result.metadata,
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
        except Exception:
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
async def list_models(category: str = "", source: str = ""):
    dispatcher = ModelDispatcher()
    models = dispatcher.list_models(
        category=category or None,
        source=source or None,
    )
    return {"models": models, "total": len(models)}


@api_router.get("/models/{model_id}")
async def get_model(model_id: str):
    dispatcher = ModelDispatcher()
    try:
        model = dispatcher.get_model(model_id)
        return {"id": model_id, **model}
    except Exception as e:
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
    except Exception as e:
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
