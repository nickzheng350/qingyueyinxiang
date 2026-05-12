"""
示例插件 - Hello World
演示插件开发的基本结构和方法
"""

from typing import Dict, Any, List
from fastapi import APIRouter
from src.plugins.base import BasePlugin
from src.plugins.manager import plugin


@plugin
class HelloWorldPlugin(BasePlugin):
    """Hello World 示例插件"""

    def get_name(self) -> str:
        return "HelloWorld"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "一个简单的示例插件，演示如何扩展 HydraFlow AI"

    def get_author(self) -> str:
        return "HydraFlow Community"

    def get_priority(self) -> int:
        return 10

    def on_load(self) -> None:
        """插件加载时的回调"""
        print(f"✅ HelloWorld 插件已加载！版本: {self.get_version()}")

    def on_unload(self) -> None:
        """插件卸载时的回调"""
        print("👋 HelloWorld 插件已卸载")

    def execute(self, name: str = "World", **kwargs) -> Dict[str, Any]:
        """
        执行插件主逻辑
        :param name: 问候的名字
        :return: 问候消息
        """
        return {
            "message": f"Hello, {name}!",
            "plugin": self.get_name(),
            "version": self.get_version(),
            "timestamp": "now"
        }

    def get_endpoints(self) -> List[Dict[str, Any]]:
        """
        提供 API 端点
        :return: 端点定义列表
        """
        router = APIRouter()

        @router.get("/hello")
        async def hello(name: str = "World"):
            return self.execute(name)

        @router.get("/hello/info")
        async def hello_info():
            return {
                "name": self.get_name(),
                "version": self.get_version(),
                "description": self.get_description(),
                "author": self.get_author()
            }

        return [
            {"path": "/api/v1/plugin/hello", "router": router, "tags": ["HelloWorld"]}
        ]

    def get_commands(self) -> List[Dict[str, Any]]:
        """
        提供 CLI 命令
        :return: 命令定义列表
        """
        def hello_command(name: str = "World"):
            result = self.execute(name)
            print(result["message"])

        return [
            {
                "name": "hello",
                "handler": hello_command,
                "help": "输出 Hello 问候信息",
                "args": [{"name": "name", "help": "问候的名字", "default": "World"}]
            }
        ]
