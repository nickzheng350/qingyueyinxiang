"""HydraFlow AI - 九头蛇生成式工作流平台"""

__version__ = "1.1.0"

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


def get_config():
    """延迟导入配置管理器，避免循环导入"""
    from .core.config import get_config
    return get_config()


def get_stability_manager():
    """延迟导入稳定性管理器，避免循环导入"""
    from .core.stability import get_stability_manager
    return get_stability_manager()


def IntentParserFactory():
    """延迟导入意图解析器工厂，避免循环导入"""
    from .intent_parser.factory import IntentParserFactory
    return IntentParserFactory()


def ModelDispatcher():
    """延迟导入模型调度器，避免循环导入"""
    from .model_dispatcher.dispatcher import ModelDispatcher
    return ModelDispatcher()


def get_type_manager():
    """延迟导入类型管理器，避免循环导入"""
    from .model_dispatcher.type_system import get_type_manager
    return get_type_manager()


def PromptEngine():
    """延迟导入提示词引擎，避免循环导入"""
    from .prompt_engine.engine import PromptEngine
    return PromptEngine()


def SkillManager():
    """延迟导入技能管理器，避免循环导入"""
    from .skills.skill_manager import SkillManager
    return SkillManager()


def get_task_executor():
    """延迟导入任务执行器，避免循环导入"""
    from .task_engine import get_task_executor
    return get_task_executor()


def get_storage():
    """延迟导入存储管理器，避免循环导入"""
    from .persistence import get_storage
    return get_storage()


def get_cache_manager():
    """延迟导入缓存管理器，避免循环导入"""
    from .cache import get_cache_manager
    return get_cache_manager()


def get_monitor():
    """延迟导入监控管理器，避免循环导入"""
    from .monitoring import get_monitor
    return get_monitor()
