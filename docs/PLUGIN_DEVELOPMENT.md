# 插件开发指南

欢迎加入 HydraFlow AI 开发者社区！本指南将帮助您创建自己的插件模块。

## 目录
- [快速开始](#快速开始)
- [插件系统架构](#插件系统架构)
- [插件开发步骤](#插件开发步骤)
- [API 参考](#api-参考)
- [示例代码](#示例代码)
- [最佳实践](#最佳实践)

## 快速开始

### 1. 创建插件目录结构

在 `plugins/` 目录下创建您的插件文件夹：

```
plugins/
└── your_plugin_name/
    ├── __init__.py
    ├── plugin.py
    └── README.md
```

### 2. 最小化插件模板

创建 `plugin.py`：

```python
from src.plugins.base import BasePlugin
from src.plugins.manager import plugin

@plugin
class YourPluginName(BasePlugin):

    def get_name(self) -> str:
        return "YourPluginName"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "您的插件描述"

    def get_author(self) -> str:
        return "您的名字"

    def execute(self, *args, **kwargs):
        # 插件主逻辑
        return {"result": "Hello from my plugin!"}
```

### 3. 加载和测试插件

启动服务后，通过 API 加载插件：

```bash
# 查看可用插件
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/plugins

# 加载插件
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/plugins/load/YourPluginName
```

## 插件系统架构

### 核心组件

| 组件 | 描述 |
|------|------|
| `BasePlugin` | 所有插件的基类，定义接口规范 |
| `PluginRegistry` | 插件注册表，管理已注册的插件类 |
| `PluginManager` | 插件管理器，负责加载、卸载、发现插件 |
| `@plugin` | 装饰器，简化插件注册 |

### 插件生命周期

```
发现 → 注册 → 加载 → 初始化 → 执行 → 卸载
```

## 插件开发步骤

### 步骤 1: 继承 BasePlugin

所有插件必须继承 `BasePlugin` 并实现抽象方法：

```python
from src.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    def get_name(self) -> str:
        return "MyPlugin"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "描述信息"

    def get_author(self) -> str:
        return "作者名"
```

### 步骤 2: 使用 @plugin 装饰器注册

```python
from src.plugins.manager import plugin

@plugin
class MyPlugin(BasePlugin):
    # ...
```

### 步骤 3: 实现生命周期回调

```python
class MyPlugin(BasePlugin):
    # ...

    def on_load(self) -> None:
        """插件加载时调用"""
        print("插件已加载")

    def on_unload(self) -> None:
        """插件卸载时调用"""
        print("插件已卸载")
```

### 步骤 4: 添加 API 端点

```python
from fastapi import APIRouter

class MyPlugin(BasePlugin):
    # ...

    def get_endpoints(self):
        router = APIRouter()

        @router.get("/myplugin/action")
        async def action():
            return {"result": "执行成功"}

        return [
            {
                "path": "/api/v1/plugin/myplugin",
                "router": router,
                "tags": ["MyPlugin"]
            }
        ]
```

### 步骤 5: 添加 CLI 命令

```python
class MyPlugin(BasePlugin):
    # ...

    def get_commands(self):
        def my_command(arg1: str, arg2: int = 0):
            result = self.execute(arg1, arg2)
            print(result)

        return [
            {
                "name": "mycmd",
                "handler": my_command,
                "help": "命令说明",
                "args": [
                    {"name": "arg1", "help": "参数1说明"},
                    {"name": "arg2", "help": "参数2说明", "default": 0}
                ]
            }
        ]
```

### 步骤 6: 声明依赖

```python
class MyPlugin(BasePlugin):
    # ...

    def get_dependencies(self):
        return ["OtherPlugin1", "OtherPlugin2"]
```

## API 参考

### BasePlugin 方法

| 方法 | 必需 | 描述 |
|------|------|------|
| `get_name()` | ✅ | 返回插件名称 |
| `get_version()` | ✅ | 返回版本号（语义化版本） |
| `get_description()` | ✅ | 返回插件描述 |
| `get_author()` | ✅ | 返回作者信息 |
| `get_priority()` | ❌ | 返回优先级，数值越大越先加载 |
| `get_dependencies()` | ❌ | 返回依赖的插件列表 |
| `on_load()` | ❌ | 加载时回调 |
| `on_unload()` | ❌ | 卸载时回调 |
| `execute()` | ❌ | 主执行逻辑 |
| `get_endpoints()` | ❌ | 返回 API 端点定义 |
| `get_commands()` | ❌ | 返回 CLI 命令定义 |
| `get_skills()` | ❌ | 返回技能定义 |

### PluginManager API

```python
from src.plugins.manager import PluginManager

manager = PluginManager()

# 发现插件
manager.discover_plugins()

# 加载插件
plugin = manager.load_plugin("PluginName", config={"key": "value"})

# 加载所有插件
manager.load_all_plugins()

# 获取插件实例
plugin = manager.get_plugin("PluginName")

# 卸载插件
manager.unload_plugin("PluginName")

# 获取所有已加载插件
loaded = manager.get_all_loaded_plugins()
```

## 示例代码

### 完整示例: 数据处理插件

```python
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.plugins.base import BasePlugin
from src.plugins.manager import plugin


class DataRequest(BaseModel):
    input_data: str
    options: Dict[str, Any] = {}


@plugin
class DataProcessorPlugin(BasePlugin):

    def get_name(self) -> str:
        return "DataProcessor"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "数据处理插件 - 支持多种数据转换操作"

    def get_author(self) -> str:
        return "Your Name"

    def get_priority(self) -> int:
        return 50

    def on_load(self) -> None:
        print(f"📊 {self.get_name()} v{self.get_version()} 已加载")

    def execute(self, input_data: str, operation: str = "uppercase", **kwargs) -> Dict[str, Any]:
        operations = {
            "uppercase": input_data.upper(),
            "lowercase": input_data.lower(),
            "reverse": input_data[::-1],
            "length": len(input_data)
        }

        result = operations.get(operation, input_data)
        return {
            "status": "success",
            "operation": operation,
            "input": input_data,
            "output": result,
            "plugin": self.get_name()
        }

    def get_endpoints(self) -> List[Dict[str, Any]]:
        router = APIRouter()

        @router.post("/process")
        async def process(request: DataRequest):
            operation = request.options.get("operation", "uppercase")
            return self.execute(request.input_data, operation)

        @router.get("/operations")
        async def list_operations():
            return {
                "supported_operations": ["uppercase", "lowercase", "reverse", "length"]
            }

        return [
            {
                "path": "/api/v1/plugin/dataprocessor",
                "router": router,
                "tags": ["DataProcessor"]
            }
        ]

    def get_commands(self) -> List[Dict[str, Any]]:
        def process_command(data: str, operation: str = "uppercase"):
            result = self.execute(data, operation)
            print(f"结果: {result['output']}")

        return [
            {
                "name": "process",
                "handler": process_command,
                "help": "处理数据",
                "args": [
                    {"name": "data", "help": "输入数据"},
                    {"name": "--operation", "help": "操作类型", "default": "uppercase"}
                ]
            }
        ]
```

## 最佳实践

### 1. 插件命名

- 使用 PascalCase 命名插件类
- 使用 snake_case 命名插件目录
- 名称应具有描述性

### 2. 版本管理

- 使用语义化版本 (Semantic Versioning)
- 格式: `MAJOR.MINOR.PATCH`
- 更新时记录变更日志

### 3. 错误处理

```python
def execute(self, *args, **kwargs):
    try:
        # 逻辑代码
        return {"status": "success"}
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

### 4. 配置管理

```python
def initialize(self, config: Dict[str, Any]) -> None:
    super().initialize(config)
    self.api_key = config.get("api_key")
    self.timeout = config.get("timeout", 30)
```

### 5. 文档

- 为每个插件创建 README.md
- 说明功能、配置、使用方法
- 提供示例代码

### 6. 测试

```python
# 插件自测试
def on_load(self) -> None:
    if self.get_config() and self.get_config().config.get("test_on_load"):
        self._run_self_test()
```

## 发布您的插件

1. 确保插件完整且测试通过
2. 创建文档
3. 提交到社区仓库（可选）
4. 分享给其他用户！

## 社区支持

- 查看 `plugins/example_hello/` 了解更多示例
- 加入讨论群组
- 提交 Issue 和 PR

---

祝您开发愉快！🚀
