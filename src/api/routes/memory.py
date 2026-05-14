"""记忆 API 路由"""

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


class MemoryEntryCreate(BaseModel):
    title: str = Field(..., description="记忆标题")
    content: str = Field(..., description="记忆内容")
    category: str = Field("未分类", description="分类")
    tags: list = Field(default_factory=list, description="标签")
    source: Optional[str] = Field(None, description="来源")
    professional_direction: Optional[str] = Field(None, description="专业方向")


MEMORY_DB = [
    {
        "id": "mem1",
        "title": "项目架构设计原则",
        "content": "在设计项目架构时，应该遵循以下原则：模块化、可扩展性、可维护性...",
        "category": "架构设计",
        "tags": ["架构", "设计模式", "最佳实践"],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "source": "项目需求分析对话",
        "professional_direction": "coding",
    },
    {
        "id": "mem2",
        "title": "文案写作技巧",
        "content": "好的文案应该具备以下特点：清晰、简洁、有说服力、能引起共鸣...",
        "category": "写作技巧",
        "tags": ["文案", "写作", "营销"],
        "created_at": "2023-12-31T00:00:00Z",
        "updated_at": "2023-12-31T00:00:00Z",
        "source": "内容创作对话",
        "professional_direction": "writing",
    },
    {
        "id": "mem3",
        "title": "市场调研方法论",
        "content": "进行市场调研时，可以采用以下方法：问卷调查、深度访谈、竞品分析...",
        "category": "市场研究",
        "tags": ["调研", "市场", "数据分析"],
        "created_at": "2023-12-30T00:00:00Z",
        "updated_at": "2023-12-30T00:00:00Z",
        "source": "市场分析对话",
        "professional_direction": "research",
    },
]

CATEGORIES_DB = [
    {"id": "cat1", "name": "架构设计", "description": "系统架构相关知识", "type": "coding", "count": 12},
    {"id": "cat2", "name": "写作技巧", "description": "文案写作方法", "type": "writing", "count": 8},
    {"id": "cat3", "name": "市场研究", "description": "市场调研方法", "type": "research", "count": 6},
    {"id": "cat4", "name": "设计规范", "description": "UI/UX设计规范", "type": "design", "count": 10},
]


@router.get("/memory/entries")
async def list_memory_entries(
    direction: str = "",
    category: str = "",
    keyword: str = ""
):
    """获取记忆列表"""
    entries = MEMORY_DB
    if direction and direction != "all":
        entries = [e for e in entries if e.get("professional_direction") == direction]
    if category:
        entries = [e for e in entries if e.get("category") == category]
    if keyword:
        entries = [e for e in entries if keyword.lower() in e["title"].lower() or keyword.lower() in e["content"].lower()]
    return {"entries": entries, "total": len(entries)}


@router.get("/memory/categories")
async def list_categories():
    """获取知识分类"""
    return {"categories": CATEGORIES_DB, "total": len(CATEGORIES_DB)}


@router.get("/memory/tags")
async def list_tags():
    """获取所有标签"""
    all_tags = set()
    for entry in MEMORY_DB:
        all_tags.update(entry.get("tags", []))
    return {"tags": list(all_tags), "total": len(all_tags)}


@router.post("/memory/entries")
async def create_memory_entry(request: MemoryEntryCreate):
    """创建记忆条目"""
    import time
    new_entry = {
        "id": f"mem{int(time.time())}",
        "title": request.title,
        "content": request.content,
        "category": request.category,
        "tags": request.tags,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": request.source,
        "professional_direction": request.professional_direction,
    }
    MEMORY_DB.insert(0, new_entry)
    return {"status": "success", "entry": new_entry}


@router.get("/memory/entries/{entry_id}")
async def get_memory_entry(entry_id: str):
    """获取记忆详情"""
    for entry in MEMORY_DB:
        if entry["id"] == entry_id:
            return entry
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="记忆未找到")
    return None


@router.put("/memory/entries/{entry_id}")
async def update_memory_entry(entry_id: str, request: MemoryEntryCreate):
    """更新记忆"""
    import time
    for entry in MEMORY_DB:
        if entry["id"] == entry_id:
            entry["title"] = request.title
            entry["content"] = request.content
            entry["category"] = request.category
            entry["tags"] = request.tags
            entry["source"] = request.source
            entry["professional_direction"] = request.professional_direction
            entry["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            return {"status": "success", "entry": entry}
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="记忆未找到")
    return {"status": "error"}


@router.delete("/memory/entries/{entry_id}")
async def delete_memory_entry(entry_id: str):
    """删除记忆"""
    global MEMORY_DB
    original_len = len(MEMORY_DB)
    MEMORY_DB = [e for e in MEMORY_DB if e["id"] != entry_id]
    if len(MEMORY_DB) < original_len:
        return {"status": "success"}
    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="记忆未找到")
    return {"status": "error"}