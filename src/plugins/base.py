"""
插件基类 - 定义插件接口规范
所有自定义插件必须继承此类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, get_type_hints

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    class BaseModel:
        def __init__(self, **kwargs):
            hints = get_type_hints(self.__class__)
            for name, hint_type in hints.items():
                value = kwargs.get(name)
                if value is not None:
                    setattr(self, name, value)
                elif hasattr(self.__class__, name):
                    setattr(self, name, getattr(self.__class__, name))


class PluginConfig(BaseModel):
    """插件配置模型"""
    name: str
    version: str
    description: str
    author: str
    enabled: bool = True
    priority: int = 0
    config: Dict[str, Any] = {}


class BasePlugin(ABC):
    """插件基类 - 所有插件必须继承此类"""

    def __init__(self):
        self._config: Optional[PluginConfig] = None
        self._initialized: bool = False

    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """获取插件版本"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass

    @abstractmethod
    def get_author(self) -> str:
        """获取插件作者"""
        pass

    def get_priority(self) -> int:
        """获取插件优先级，数值越大越先加载"""
        return 0

    def get_dependencies(self) -> List[str]:
        """获取依赖的其他插件名称"""
        return []

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化插件
        插件被加载时调用此方法
        """
        self._config = PluginConfig(
            name=self.get_name(),
            version=self.get_version(),
            description=self.get_description(),
            author=self.get_author(),
            config=config
        )
        self._initialized = True
        self.on_load()

    def is_initialized(self) -> bool:
        """检查插件是否已初始化"""
        return self._initialized

    def get_config(self) -> Optional[PluginConfig]:
        """获取插件配置"""
        return self._config

    def on_load(self) -> None:
        """插件加载时的回调 - 子类可覆盖"""
        pass

    def on_unload(self) -> None:
        """插件卸载时的回调 - 子类可覆盖"""
        pass

    def execute(self, *args, **kwargs) -> Any:
        """执行插件主逻辑 - 子类可覆盖"""
        raise NotImplementedError("插件未实现 execute 方法")

    def get_endpoints(self) -> List[Dict[str, Any]]:
        """
        提供 API 端点定义
        返回格式: [{"path": "/api/v1/xxx", "method": "GET", "handler": func}]
        """
        return []

    def get_commands(self) -> List[Dict[str, Any]]:
        """
        提供 CLI 命令定义
        返回格式: [{"name": "xxx", "handler": func, "help": "说明"}]
        """
        return []

    def get_skills(self) -> List[Dict[str, Any]]:
        """
        提供技能定义
        返回格式: [{"name": "xxx", "manifest": {...}}]
        """
        return []

    def __repr__(self) -> str:
        return f"<Plugin {self.get_name()} v{self.get_version()}>"
