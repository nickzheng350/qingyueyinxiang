"""经验库 API 路由"""

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


class ExperienceCreate(BaseModel):
    name: str = Field(..., description="经验名称")
    description: str = Field(..., description="经验描述")
    source_dialogue: Optional[str] = Field(None, description="来源对话ID")
    professional_direction: str = Field("coding", description="专业方向")
    tags: list = Field(default_factory=list, description="标签")
    quality: int = Field(80, description="质量评分")


class ExperienceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list] = None
    quality: Optional[int] = None


class SuggestionResponse(BaseModel):
    id: str
    type: str
    message: str
    ids: Optional[list] = None


EXPERIENCES_DB = [
    {
        "id": "exp1",
        "name": "Vue3组件开发模式",
        "description": "总结了一套高效的Vue3组件开发流程，包括组合式API使用、状态管理模式、组件通信技巧等。",
        "source_dialogue": "前端组件开发对话",
        "professional_direction": "coding",
        "tags": ["Vue3", "组件", "最佳实践"],
        "created_at": "2024-01-01T00:00:00Z",
        "usage_count": 24,
        "quality": 92,
    },
    {
        "id": "exp2",
        "name": "技术文档写作框架",
        "description": "一套完整的技术文档写作框架，包含概述、背景、方案设计、代码示例、总结等模块。",
        "source_dialogue": "API文档编写对话",
        "professional_direction": "writing",
        "tags": ["文档", "技术写作", "模板"],
        "created_at": "2023-12-31T00:00:00Z",
        "usage_count": 18,
        "quality": 88,
    },
    {
        "id": "exp3",
        "name": "市场竞品分析方法",
        "description": "通过多维度分析竞品，包括功能对比、用户体验、定价策略、市场定位等。",
        "source_dialogue": "竞品分析对话",
        "professional_direction": "research",
        "tags": ["竞品分析", "市场研究", "方法论"],
        "created_at": "2023-12-30T00:00:00Z",
        "usage_count": 12,
        "quality": 85,
    },
    {
        "id": "exp4",
        "name": "UI设计系统构建",
        "description": "从0到1构建设计系统，包括色彩体系、字体系统、组件库设计规范。",
        "source_dialogue": "设计系统搭建对话",
        "professional_direction": "design",
        "tags": ["设计系统", "UI规范", "组件库"],
        "created_at": "2023-12-29T00:00:00Z",
        "usage_count": 15,
        "quality": 90,
    },
]

SUGGESTIONS_DB = [
    {"id": "s1", "type": "merge", "message": "建议合并: \"Vue组件开发\"和\"React组件开发\"", "ids": ["exp1"]},
    {"id": "s2", "type": "optimize", "message": "建议优化: \"技术文档写作框架\"可以增加更多示例", "id": "exp2"},
]


@router.get("/experiences")
async def list_experiences(direction: str = ""):
    """获取经验列表"""
    if direction and direction != "all":
        experiences = [e for e in EXPERIENCES_DB if e["professional_direction"] == direction]
    else:
        experiences = EXPERIENCES_DB
    return {"experiences": experiences, "total": len(experiences)}


@router.post("/experiences")
async def create_experience(request: ExperienceCreate):
    """创建新经验"""
    import time
    new_exp = {
        "id": f"exp{int(time.time())}",
        "name": request.name,
        "description": request.description,
        "source_dialogue": request.source_dialogue,
        "professional_direction": request.professional_direction,
        "tags": request.tags,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "usage_count": 0,
        "quality": request.quality,
    }
    EXPERIENCES_DB.insert(0, new_exp)
    return {"status": "success", "experience": new_exp}


@router.get("/experiences/suggestions")
async def get_suggestions():
    """获取智能整合建议"""
    return {"suggestions": SUGGESTIONS_DB, "total": len(SUGGESTIONS_DB)}


@router.post("/experiences/generate/{dialogue_id}")
async def generate_from_dialogue(dialogue_id: str):
    """从对话生成经验"""
    import time
    new_exp = {
        "id": f"exp{int(time.time())}",
        "name": "新生成的经验",
        "description": f"从对话 {dialogue_id} 自动生成的经验总结",
        "source_dialogue": dialogue_id,
        "professional_direction": "coding",
        "tags": ["自动生成"],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "usage_count": 0,
        "quality": 75,
    }
    EXPERIENCES_DB.insert(0, new_exp)
    return {"status": "success", "experience": new_exp}


@router.get("/experiences/{exp_id}")
async def get_experience(exp_id: str):
    """获取经验详情"""
    for exp in EXPERIENCES_DB:
        if exp["id"] == exp_id:
            return exp
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="经验未找到")
    return None


@router.put("/experiences/{exp_id}")
async def update_experience(exp_id: str, request: ExperienceUpdate):
    """更新经验"""
    for exp in EXPERIENCES_DB:
        if exp["id"] == exp_id:
            if request.name is not None:
                exp["name"] = request.name
            if request.description is not None:
                exp["description"] = request.description
            if request.tags is not None:
                exp["tags"] = request.tags
            if request.quality is not None:
                exp["quality"] = request.quality
            return {"status": "success", "experience": exp}
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="经验未找到")
    return {"status": "error"}


@router.delete("/experiences/{exp_id}")
async def delete_experience(exp_id: str):
    """删除经验"""
    global EXPERIENCES_DB
    original_len = len(EXPERIENCES_DB)
    EXPERIENCES_DB = [e for e in EXPERIENCES_DB if e["id"] != exp_id]
    if len(EXPERIENCES_DB) < original_len:
        return {"status": "success"}
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="经验未找到")
    return {"status": "error"}