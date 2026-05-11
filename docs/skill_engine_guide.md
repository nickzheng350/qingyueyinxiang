# HydraFlow AI 技能引擎使用指南

## 概述

技能引擎是 HydraFlow AI 的核心组件之一，负责加载、管理和执行各种技能。技能可以是：

- **动态技能**：使用 Python 代码实现的技能
- **配置技能**：使用 YAML/JSON 配置定义的技能

## 技能目录结构

```
skills/
├── local/                    # 本地技能
│   ├── example_hello/       # 技能目录
│   │   ├── manifest.json    # 技能清单
│   │   ├── executor.py      # 执行器（动态技能）
│   │   └── config.yaml      # 配置文件（配置技能）
│   └── example_http_fetcher/
│       ├── manifest.json
│       └── config.yaml
└── api/                      # API 技能（未来扩展）
```

## 技能清单 (manifest.json)

```json
{
  "skill_id": "my_skill",
  "name": "我的技能",
  "version": "1.0.0",
  "description": "技能描述",
  "author": "作者名",
  "type": "local",
  "category": "category_name",
  "tags": ["标签 1", "标签 2"],
  "config": {
    "key": "value"
  }
}
```

## 动态技能实现

### 1. 创建执行器类

```python
from src.skills.skill_engine import SkillExecutor, SkillExecutionResult, SkillContext

class MySkillExecutor(SkillExecutor):
    """我的技能执行器"""
    
    async def execute(self, **kwargs) -> SkillExecutionResult:
        """异步执行技能"""
        try:
            # 访问技能配置
            config_value = self.context.config.get('key')
            
            # 访问共享状态
            shared_data = self.context.shared_state.get('data')
            
            # 执行逻辑
            result = self._do_something(**kwargs)
            
            return SkillExecutionResult(
                success=True,
                data=result,
                metadata={"executor": "MySkillExecutor"}
            )
        except Exception as e:
            return SkillExecutionResult(
                success=False,
                error=str(e),
                error_trace=traceback.format_exc()
            )
    
    def execute_sync(self, **kwargs) -> SkillExecutionResult:
        """同步执行技能"""
        import asyncio
        return asyncio.run(self.execute(**kwargs))
```

### 2. 使用上下文信息

```python
class MySkillExecutor(SkillExecutor):
    async def execute(self, **kwargs) -> SkillExecutionResult:
        # 技能基本信息
        skill_id = self.context.skill_id
        skill_name = self.context.skill_name
        skill_version = self.context.skill_version
        
        # 技能配置
        config = self.context.config
        
        # 全局配置
        global_config = self.context.global_config
        
        # 共享状态（跨技能）
        shared_state = self.context.shared_state
        
        # ... 执行逻辑
```

## 配置技能实现

### 1. 创建配置文件 (config.yaml)

```yaml
# 定义技能执行的动作列表
actions:
  # HTTP 请求动作
  - type: http_request
    params:
      url: https://api.example.com/data
      method: GET
      headers:
        Content-Type: application/json
  
  # 数据转换动作
  - type: data_transform
    params:
      type: map
      expression: "item.get('name', 'Unknown')"
  
  # 文件操作动作
  - type: file_operation
    params:
      operation: write
      path: /tmp/result.txt
  
  # Shell 命令动作
  - type: shell_command
    params:
      command: "ls -la"
      timeout: 30
```

### 2. 支持的动作类型

#### HTTP 请求 (http_request)
```yaml
- type: http_request
  params:
    url: https://api.example.com
    method: GET|POST|PUT|DELETE
    headers:
      Content-Type: application/json
    body:
      key: value
```

#### 文件操作 (file_operation)
```yaml
- type: file_operation
  params:
    operation: read|write|delete
    path: /path/to/file
    content: "文件内容"  # write 操作需要
```

#### 数据转换 (data_transform)
```yaml
- type: filter
  params:
    type: filter
    condition: "item.get('age', 0) > 18"
    
- type: map
  params:
    type: map
    expression: "item.get('name')"
    
- type: reduce
  params:
    type: reduce
    initial: 0
    expression: "result + item.get('value', 0)"
```

#### Shell 命令 (shell_command)
```yaml
- type: shell_command
  params:
    command: "echo hello"
    timeout: 30  # 超时时间（秒）
```

## 技能执行方式

### 1. 通过技能管理器执行

```python
from src.skills.skill_manager import SkillManager

skill_manager = SkillManager()

# 执行技能
result = skill_manager.execute_skill(
    "skill_id",
    param1="value1",
    param2="value2"
)

print(result)
# {
#   "status": "success",
#   "skill_id": "skill_id",
#   "data": {...},
#   "error": None,
#   "execution_time": 0.123,
#   "metadata": {...}
# }
```

### 2. 通过技能引擎执行

```python
from src.skills.skill_engine import get_skill_engine

engine = get_skill_engine()

# 注册技能
engine.register_skill(
    skill_id="my_skill",
    skill_name="我的技能",
    skill_version="1.0.0",
    executor_type="dynamic",  # 或 "config_based"
    module_path="/path/to/executor.py",
    config={"key": "value"}
)

# 异步执行
result = await engine.execute_skill("my_skill", param="value")

# 同步执行
result = engine.execute_skill_sync("my_skill", param="value")
```

### 3. 通过 API 执行

```bash
# 执行技能
curl -X POST http://localhost:8002/api/v1/skills/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "my_skill",
    "parameters": {
      "param1": "value1",
      "param2": "value2"
    }
  }'

# 列出所有技能
curl http://localhost:8002/api/v1/skills

# 获取技能详情
curl http://localhost:8002/api/v1/skills/my_skill
```

## 执行结果格式

```python
SkillExecutionResult(
    success=True,           # 是否成功
    data={...},             # 返回数据
    error=None,             # 错误信息（失败时）
    error_trace=None,       # 错误堆栈（失败时）
    execution_time=0.123,   # 执行时间（秒）
    metadata={}             # 元数据
)
```

## 高级功能

### 1. 共享状态

技能之间可以共享状态：

```python
engine = get_skill_engine()

# 设置共享状态
engine.set_shared_state("user_data", {"user_id": 123})

# 在技能中访问共享状态
class MySkillExecutor(SkillExecutor):
    async def execute(self, **kwargs):
        user_data = self.context.shared_state.get("user_data")
        # ...
```

### 2. 技能注销

```python
engine.unregister_skill("skill_id")
```

### 3. 获取技能信息

```python
skill_info = engine.get_skill_info("skill_id")
# {
#   "skill_id": "...",
#   "skill_name": "...",
#   "skill_version": "...",
#   "config": {...},
#   "executor_type": "DynamicSkillExecutor"
# }
```

## 最佳实践

### 1. 错误处理

```python
async def execute(self, **kwargs) -> SkillExecutionResult:
    try:
        # 执行逻辑
        result = await self._do_work(**kwargs)
        return SkillExecutionResult(success=True, data=result)
    except SpecificError as e:
        return SkillExecutionResult(
            success=False,
            error=f"具体错误：{e}",
            metadata={"error_type": "SpecificError"}
        )
    except Exception as e:
        return SkillExecutionResult(
            success=False,
            error=str(e),
            error_trace=traceback.format_exc()
        )
```

### 2. 日志记录

```python
import logging

logger = logging.getLogger("hydraflow.skills.my_skill")

class MySkillExecutor(SkillExecutor):
    async def execute(self, **kwargs):
        logger.info(f"执行技能：{self.context.skill_id}")
        logger.debug(f"参数：{kwargs}")
        # ...
```

### 3. 性能优化

```python
async def execute(self, **kwargs):
    import time
    start_time = time.time()
    
    try:
        # 执行逻辑
        result = await self._do_work(**kwargs)
        
        execution_time = time.time() - start_time
        
        return SkillExecutionResult(
            success=True,
            data=result,
            execution_time=execution_time,
            metadata={"performance": {"duration": execution_time}}
        )
    except Exception as e:
        # ...
```

## 示例技能

### 示例 1: Hello World 技能

```python
# skills/local/example_hello/executor.py
from src.skills.skill_engine import SkillExecutor, SkillExecutionResult

class HelloSkillExecutor(SkillExecutor):
    async def execute(self, name: str = "World"):
        greeting = self.context.config.get("default_greeting", "Hello")
        message = f"{greeting}, {name}!"
        
        return SkillExecutionResult(
            success=True,
            data={"message": message}
        )
```

### 示例 2: HTTP API 调用技能

```python
# skills/local/example_http_fetcher/config.yaml
actions:
  - type: http_request
    params:
      url: https://api.github.com/users/octocat
      method: GET
  
  - type: data_transform
    params:
      type: map
      expression: "{'login': item.get('login'), 'name': item.get('name')}"
```

## 故障排查

### 技能未找到

确保技能已正确安装并注册：

```python
skill_manager = SkillManager()
skills = skill_manager.list_skills()
print(skills)  # 检查技能列表
```

### 执行器加载失败

检查 executor.py 或 config.yaml 是否存在且格式正确：

```bash
# 检查文件
ls -la skills/local/my_skill/
cat skills/local/my_skill/manifest.json
```

### 执行超时

对于耗时操作，使用异步执行并设置合理的超时：

```python
result = await asyncio.wait_for(
    engine.execute_skill("skill_id"),
    timeout=30.0
)
```

## 总结

技能引擎提供了灵活、可扩展的技能执行框架：

- ✅ 支持动态 Python 技能和配置技能
- ✅ 提供统一的执行接口和结果格式
- ✅ 支持异步和同步执行
- ✅ 提供共享状态机制
- ✅ 完善的错误处理和日志记录
- ✅ REST API 支持远程调用

通过技能引擎，您可以轻松扩展 HydraFlow AI 的功能，实现各种自定义业务逻辑。
