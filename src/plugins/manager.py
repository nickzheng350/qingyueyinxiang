"""
插件管理器 - 核心插件加载和管理功能
"""

import os
import sys
import importlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from .base import BasePlugin
from .registry import PluginRegistry
import logging

logger = logging.getLogger(__name__)


def plugin(name: Optional[str] = None):
    """
    插件装饰器 - 简化插件注册
    使用方式: @plugin 或 @plugin("my_plugin")
    """
    def decorator(cls):
        if not issubclass(cls, BasePlugin):
            raise TypeError(f"{cls.__name__} 必须继承 BasePlugin")
        PluginRegistry.register(cls)
        return cls
    return decorator


class PluginManager:
    """插件管理器"""

    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """
        初始化插件管理器
        :param plugin_dirs: 插件目录列表
        """
        self.plugin_dirs = plugin_dirs or []
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}

        # 默认插件目录
        default_dirs = [
            os.path.join(os.path.dirname(__file__), '../../plugins'),
            os.path.join(os.path.dirname(__file__), '../../skills/local'),
        ]
        self.plugin_dirs.extend([d for d in default_dirs if d not in self.plugin_dirs])

    def discover_plugins(self) -> List[str]:
        """
        发现所有可用插件
        :return: 插件类名列表
        """
        for plugin_dir in self.plugin_dirs:
            PluginRegistry.load_directory(plugin_dir)

        plugins = list(PluginRegistry.get_all_plugins().keys())
        logger.info(f"发现 {len(plugins)} 个可用插件")
        return plugins

    def load_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BasePlugin]:
        """
        加载指定插件
        :param plugin_name: 插件类名
        :param config: 插件配置
        :return: 插件实例
        """
        plugin_class = PluginRegistry.get_plugin_class(plugin_name)
        if not plugin_class:
            logger.error(f"插件未注册: {plugin_name}")
            return None

        # 检查依赖
        plugin_inst = plugin_class()
        for dep_name in plugin_inst.get_dependencies():
            if dep_name not in self.loaded_plugins:
                logger.warning(f"依赖插件未加载: {dep_name}，尝试自动加载")
                self.load_plugin(dep_name)

        # 初始化插件
        plugin_inst.initialize(config or {})
        self.loaded_plugins[plugin_name] = plugin_inst
        PluginRegistry.set_instance(plugin_name, plugin_inst)

        logger.info(f"插件加载成功: {plugin_name} v{plugin_inst.get_version()}")
        return plugin_inst

    def load_all_plugins(self) -> Dict[str, BasePlugin]:
        """
        加载所有已发现的插件
        :return: 已加载插件字典
        """
        plugin_classes = PluginRegistry.get_all_plugins()

        # 按优先级排序
        sorted_plugins = sorted(
            plugin_classes.items(),
            key=lambda x: (lambda c: c().get_priority())(x[1]),
            reverse=True
        )

        for name, cls in sorted_plugins:
            if name not in self.loaded_plugins:
                self.load_plugin(name)

        return self.loaded_plugins

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        :param plugin_name: 插件名称
        :return: 是否成功
        """
        if plugin_name not in self.loaded_plugins:
            return False

        plugin_inst = self.loaded_plugins[plugin_name]
        plugin_inst.on_unload()
        del self.loaded_plugins[plugin_name]
        logger.info(f"插件已卸载: {plugin_name}")
        return True

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """获取已加载的插件"""
        return self.loaded_plugins.get(name)

    def get_all_loaded_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有已加载的插件"""
        return self.loaded_plugins.copy()

    def get_all_plugin_endpoints(self) -> List[Dict[str, Any]]:
        """获取所有插件提供的 API 端点"""
        endpoints = []
        for plugin_name, plugin_inst in self.loaded_plugins.items():
            endpoints.extend(plugin_inst.get_endpoints())
        return endpoints

    def get_all_plugin_commands(self) -> List[Dict[str, Any]]:
        """获取所有插件提供的 CLI 命令"""
        commands = []
        for plugin_name, plugin_inst in self.loaded_plugins.items():
            commands.extend(plugin_inst.get_commands())
        return commands

    def get_all_plugin_skills(self) -> List[Dict[str, Any]]:
        """获取所有插件提供的技能"""
        skills = []
        for plugin_name, plugin_inst in self.loaded_plugins.items():
            skills.extend(plugin_inst.get_skills())
        return skills

    def install_plugin_from_path(self, path: str) -> bool:
        """
        从路径安装插件
        :param path: 插件目录路径
        :return: 是否成功
        """
        plugin_path = Path(path)
        if not plugin_path.exists():
            logger.error(f"插件路径不存在: {path}")
            return False

        # 添加到插件目录
        if str(plugin_path.parent) not in self.plugin_dirs:
            self.plugin_dirs.append(str(plugin_path.parent))

        # 加载插件
        sys.path.insert(0, str(plugin_path.parent))
        try:
            PluginRegistry.load_directory(str(plugin_path.parent))
            return True
        except Exception as e:
            logger.error(f"安装插件失败: {e}")
            return False
