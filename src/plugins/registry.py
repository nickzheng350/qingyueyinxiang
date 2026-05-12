"""
插件注册表 - 管理所有已注册的插件
"""

import importlib
import os
from pathlib import Path
from typing import Dict, List, Type, Optional
from .base import BasePlugin
import logging

logger = logging.getLogger(__name__)


class PluginRegistry:
    """插件注册表"""

    _instance: Optional['PluginRegistry'] = None
    _plugins: Dict[str, Type[BasePlugin]] = {}
    _instances: Dict[str, BasePlugin] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, plugin_class: Type[BasePlugin]) -> Type[BasePlugin]:
        """
        注册插件类
        可作为装饰器使用: @PluginRegistry.register
        """
        plugin_name = plugin_class.__name__
        cls._plugins[plugin_name] = plugin_class
        logger.info(f"插件已注册: {plugin_name}")
        return plugin_class

    @classmethod
    def get_plugin_class(cls, name: str) -> Optional[Type[BasePlugin]]:
        """获取插件类"""
        return cls._plugins.get(name)

    @classmethod
    def get_all_plugins(cls) -> Dict[str, Type[BasePlugin]]:
        """获取所有已注册的插件类"""
        return cls._plugins.copy()

    @classmethod
    def get_instance(cls, name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return cls._instances.get(name)

    @classmethod
    def set_instance(cls, name: str, instance: BasePlugin) -> None:
        """设置插件实例"""
        cls._instances[name] = instance

    @classmethod
    def clear(cls) -> None:
        """清空注册表"""
        cls._plugins.clear()
        cls._instances.clear()

    @classmethod
    def load_directory(cls, directory: str) -> None:
        """从目录加载所有插件"""
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"插件目录不存在: {directory}")
            return

        for item in dir_path.iterdir():
            if item.is_dir() and (item / '__init__.py').exists():
                module_name = item.name
                try:
                    importlib.import_module(f"{dir_path.name}.{module_name}")
                    logger.info(f"已加载插件模块: {module_name}")
                except Exception as e:
                    logger.error(f"加载插件模块失败 {module_name}: {e}")
