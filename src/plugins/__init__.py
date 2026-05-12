"""
插件系统 - HydraFlow AI 扩展架构
提供灵活的模块添加机制，支持第三方开发者扩展功能
"""

from .manager import PluginManager, plugin
from .base import BasePlugin
from .registry import PluginRegistry

__all__ = [
    'PluginManager',
    'PluginRegistry',
    'BasePlugin',
    'plugin'
]
