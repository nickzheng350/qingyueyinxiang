"""HydraFlow AI - 九头蛇生成式工作流平台"""

__version__ = "1.1.0"

# 导出核心模块
from .core import get_config, get_stability_manager
from .intent_parser import IntentParserFactory
from .model_dispatcher import ModelDispatcher, get_type_manager
from .prompt_engine import PromptEngine
from .skills import SkillManager
from .task_engine import get_task_executor
from .persistence import get_storage
from .cache import get_cache_manager
from .monitoring import get_monitor

__all__ = [
    "__version__",
    "get_config",
    "get_stability_manager",
    "IntentParserFactory",
    "ModelDispatcher",
    "get_type_manager",
    "PromptEngine",
    "SkillManager",
    "get_task_executor",
    "get_storage",
    "get_cache_manager",
    "get_monitor",
]
