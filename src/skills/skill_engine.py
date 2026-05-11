"""技能执行引擎 - 加载和执行技能"""

import importlib.util
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
import asyncio
import traceback

logger = logging.getLogger("hydraflow.skill_engine")


@dataclass
class SkillContext:
    """技能执行上下文"""
    skill_id: str
    skill_name: str
    skill_version: str
    config: Dict[str, Any]
    global_config: Dict[str, Any] = field(default_factory=dict)
    shared_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillExecutionResult:
    """技能执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_trace: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SkillExecutor:
    """技能执行器基类"""
    
    def __init__(self, context: SkillContext):
        self.context = context
    
    async def execute(self, **kwargs) -> SkillExecutionResult:
        """执行技能（异步）"""
        raise NotImplementedError
    
    def execute_sync(self, **kwargs) -> SkillExecutionResult:
        """执行技能（同步）"""
        raise NotImplementedError


class DynamicSkillExecutor(SkillExecutor):
    """动态技能执行器 - 从 Python 文件加载"""
    
    def __init__(self, context: SkillContext, module_path: str):
        super().__init__(context)
        self.module_path = module_path
        self._executor_class = None
        self._load_executor()
    
    def _load_executor(self) -> None:
        """加载技能执行器类"""
        try:
            module_name = Path(self.module_path).stem
            spec = importlib.util.spec_from_file_location(module_name, self.module_path)
            if not spec or not spec.loader:
                raise ImportError(f"无法加载模块：{self.module_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找 SkillExecutor 子类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, SkillExecutor) and 
                    attr is not SkillExecutor):
                    self._executor_class = attr
                    logger.debug(f"加载技能执行器：{attr_name}")
                    return
            
            # 如果没有找到子类，尝试查找 execute 函数
            if hasattr(module, 'execute'):
                self._executor_class = self._create_wrapper_class(module.execute)
                return
            
            raise ImportError("未找到 SkillExecutor 子类或 execute 函数")

        except (ImportError, FileNotFoundError) as e:
            logger.error(f"加载技能模块失败：{e}")
            raise
    
    def _create_wrapper_class(self, execute_func: Callable) -> type:
        """为函数创建包装器类"""
        class FunctionWrapper(SkillExecutor):
            def execute_sync(self, **kwargs):
                try:
                    result = execute_func(**kwargs)
                    return SkillExecutionResult(
                        success=True,
                        data=result,
                        metadata={"executor": "function"}
                    )
                except Exception as e:
                    return SkillExecutionResult(
                        success=False,
                        error=str(e),
                        error_trace=traceback.format_exc(),
                        metadata={"executor": "function"}
                    )
            
            async def execute(self, **kwargs):
                return self.execute_sync(**kwargs)
        
        return FunctionWrapper
    
    async def execute(self, **kwargs) -> SkillExecutionResult:
        """异步执行技能"""
        import time
        start_time = time.time()
        
        try:
            if not self._executor_class:
                raise RuntimeError("技能执行器未加载")
            
            executor = self._executor_class(self.context)
            result = await executor.execute(**kwargs)
            result.execution_time = time.time() - start_time
            return result
            
        except (RuntimeError, AttributeError) as e:
            execution_time = time.time() - start_time
            logger.error(f"技能执行失败：{e}")
            return SkillExecutionResult(
                success=False,
                error=str(e),
                error_trace=traceback.format_exc(),
                execution_time=execution_time,
                metadata={"executor": "dynamic"}
            )

    def execute_sync(self, **kwargs) -> SkillExecutionResult:
        """同步执行技能"""
        import time
        start_time = time.time()
        
        try:
            if not self._executor_class:
                raise RuntimeError("技能执行器未加载")
            
            executor = self._executor_class(self.context)
            result = executor.execute_sync(**kwargs)
            result.execution_time = time.time() - start_time
            return result

        except (RuntimeError, AttributeError) as e:
            execution_time = time.time() - start_time
            logger.error(f"技能执行失败：{e}")
            return SkillExecutionResult(
                success=False,
                error=str(e),
                error_trace=traceback.format_exc(),
                execution_time=execution_time,
                metadata={"executor": "dynamic"}
            )


class ConfigBasedSkillExecutor(SkillExecutor):
    """基于配置的技能执行器 - 使用 YAML/JSON 配置"""
    
    def __init__(self, context: SkillContext, config_path: str):
        super().__init__(context)
        self.config_path = config_path
        self._skill_config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载技能配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.json'):
                    return json.load(f)
                elif self.config_path.endswith(('.yaml', '.yml')):
                    import yaml
                    return yaml.safe_load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式：{self.config_path}")
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"加载技能配置失败：{e}")
            raise
    
    async def execute(self, **kwargs) -> SkillExecutionResult:
        """执行基于配置的技能"""
        import time
        start_time = time.time()
        
        try:
            # 模拟执行配置定义的操作
            actions = self._skill_config.get('actions', [])
            results = []
            
            for action in actions:
                action_type = action.get('type')
                action_params = action.get('params', {})
                
                # 合并传入的参数
                merged_params = {**action_params, **kwargs}
                
                # 执行动作
                result = await self._execute_action(action_type, merged_params)
                results.append(result)
            
            execution_time = time.time() - start_time
            return SkillExecutionResult(
                success=True,
                data={"results": results},
                execution_time=execution_time,
                metadata={"executor": "config_based", "actions_count": len(actions)}
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"技能执行失败：{e}")
            return SkillExecutionResult(
                success=False,
                error=str(e),
                error_trace=traceback.format_exc(),
                execution_time=execution_time,
                metadata={"executor": "config_based"}
            )
    
    def execute_sync(self, **kwargs) -> SkillExecutionResult:
        """同步执行"""
        return asyncio.run(self.execute(**kwargs))
    
    async def _execute_action(self, action_type: str, params: Dict[str, Any]) -> Any:
        """执行单个动作"""
        # 这里可以实现各种预定义的动作类型
        if action_type == 'http_request':
            return await self._http_request(params)
        elif action_type == 'file_operation':
            return self._file_operation(params)
        elif action_type == 'data_transform':
            return self._data_transform(params)
        elif action_type == 'shell_command':
            return await self._shell_command(params)
        else:
            logger.warning(f"未知的动作类型：{action_type}")
            return None
    
    async def _http_request(self, params: Dict[str, Any]) -> Any:
        """HTTP 请求动作"""
        import httpx
        url = params.get('url')
        method = params.get('method', 'GET')
        headers = params.get('headers', {})
        body = params.get('body')

        try:
            async with httpx.AsyncClient() as client:
                if method == 'GET':
                    resp = await client.get(url, headers=headers)
                elif method == 'POST':
                    resp = await client.post(url, json=body, headers=headers)
                elif method == 'PUT':
                    resp = await client.put(url, json=body, headers=headers)
                elif method == 'DELETE':
                    resp = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"不支持的 HTTP 方法：{method}")

                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPError, asyncio.TimeoutError, ValueError) as e:
            logger.error(f"HTTP 请求失败：{e}")
            raise
    
    def _file_operation(self, params: Dict[str, Any]) -> Any:
        """文件操作动作"""
        operation = params.get('operation')
        path = params.get('path')
        
        if operation == 'read':
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        elif operation == 'write':
            content = params.get('content')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        elif operation == 'delete':
            Path(path).unlink()
            return True
        else:
            raise ValueError(f"未知的文件操作：{operation}")
    
    def _data_transform(self, params: Dict[str, Any]) -> Any:
        """数据转换动作"""
        transform_type = params.get('type')
        data = params.get('data')
        
        if transform_type == 'filter':
            condition = params.get('condition')
            return [item for item in data if eval(condition, {}, {'item': item})]
        elif transform_type == 'map':
            expression = params.get('expression')
            return [eval(expression, {}, {'item': item}) for item in data]
        elif transform_type == 'reduce':
            initial = params.get('initial')
            expression = params.get('expression')
            result = initial
            for item in data:
                result = eval(expression, {}, {'result': result, 'item': item})
            return result
        else:
            raise ValueError(f"未知的转换类型：{transform_type}")
    
    async def _shell_command(self, params: Dict[str, Any]) -> Any:
        """Shell 命令动作"""
        import subprocess
        command = params.get('command')
        timeout = params.get('timeout', 30)
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8'),
                'stderr': stderr.decode('utf-8'),
            }
        except asyncio.TimeoutError:
            process.kill()
            raise TimeoutError(f"命令执行超时：{command}")


class SkillEngine:
    """技能引擎 - 统一管理技能执行"""
    
    def __init__(self):
        self._executors: Dict[str, SkillExecutor] = {}
        self._contexts: Dict[str, SkillContext] = {}
        self._shared_state: Dict[str, Any] = {}
    
    def register_skill(
        self,
        skill_id: str,
        skill_name: str,
        skill_version: str = "1.0.0",
        executor_type: str = "dynamic",
        **kwargs
    ) -> None:
        """注册技能"""
        config = kwargs.get('config', {})
        
        context = SkillContext(
            skill_id=skill_id,
            skill_name=skill_name,
            skill_version=skill_version,
            config=config,
            shared_state=self._shared_state
        )
        
        if executor_type == "dynamic":
            module_path = kwargs.get('module_path')
            if not module_path:
                raise ValueError("动态执行器需要 module_path 参数")
            executor = DynamicSkillExecutor(context, module_path)
        elif executor_type == "config_based":
            config_path = kwargs.get('config_path')
            if not config_path:
                raise ValueError("配置执行器需要 config_path 参数")
            executor = ConfigBasedSkillExecutor(context, config_path)
        else:
            raise ValueError(f"不支持的执行器类型：{executor_type}")
        
        self._executors[skill_id] = executor
        self._contexts[skill_id] = context
        logger.info(f"技能已注册：{skill_id} ({skill_name})")
    
    def unregister_skill(self, skill_id: str) -> None:
        """注销技能"""
        if skill_id in self._executors:
            del self._executors[skill_id]
        if skill_id in self._contexts:
            del self._contexts[skill_id]
        logger.info(f"技能已注销：{skill_id}")
    
    async def execute_skill(
        self,
        skill_id: str,
        **kwargs
    ) -> SkillExecutionResult:
        """执行技能"""
        if skill_id not in self._executors:
            return SkillExecutionResult(
                success=False,
                error=f"技能未找到：{skill_id}",
                metadata={"skill_id": skill_id}
            )
        
        executor = self._executors[skill_id]
        logger.info(f"执行技能：{skill_id}")
        
        return await executor.execute(**kwargs)
    
    def execute_skill_sync(
        self,
        skill_id: str,
        **kwargs
    ) -> SkillExecutionResult:
        """同步执行技能"""
        if skill_id not in self._executors:
            return SkillExecutionResult(
                success=False,
                error=f"技能未找到：{skill_id}",
                metadata={"skill_id": skill_id}
            )
        
        executor = self._executors[skill_id]
        logger.info(f"执行技能（同步）：{skill_id}")
        
        return executor.execute_sync(**kwargs)
    
    def get_skill_info(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能信息"""
        if skill_id not in self._contexts:
            return None
        
        context = self._contexts[skill_id]
        return {
            "skill_id": context.skill_id,
            "skill_name": context.skill_name,
            "skill_version": context.skill_version,
            "config": context.config,
            "executor_type": type(self._executors[skill_id]).__name__,
        }
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """列出所有技能"""
        return [self.get_skill_info(skill_id) for skill_id in self._executors]
    
    def get_shared_state(self, key: Optional[str] = None) -> Any:
        """获取共享状态"""
        if key:
            return self._shared_state.get(key)
        return self._shared_state
    
    def set_shared_state(self, key: str, value: Any) -> None:
        """设置共享状态"""
        self._shared_state[key] = value
    
    def clear_shared_state(self) -> None:
        """清空共享状态"""
        self._shared_state.clear()


# 全局单例
_skill_engine = None

def get_skill_engine() -> SkillEngine:
    """获取技能引擎实例"""
    global _skill_engine
    if _skill_engine is None:
        _skill_engine = SkillEngine()
    return _skill_engine
