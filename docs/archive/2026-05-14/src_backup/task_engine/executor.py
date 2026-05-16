"""任务执行引擎 - 管理异步任务和结果"""

import asyncio
import uuid
from enum import Enum
from datetime import datetime
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("hydraflow.task_engine")


# 延迟导入避免循环依赖
def _get_ws_manager():
    from src.ws.manager import get_ws_manager
    return get_ws_manager()


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO_GENERATION = "audio_generation"
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    IMAGE_UPSCALE = "image_upscale"
    IMAGE_EDIT = "image_edit"
    SKILL_EXECUTION = "skill_execution"


@dataclass
class Task:
    id: str
    type: TaskType
    prompt: str
    parameters: Dict[str, Any]
    model_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskStorage:
    """任务存储抽象层"""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._task_index: Dict[str, List[str]] = {}

    def create_task(self, task: Task) -> None:
        """创建任务"""
        self._tasks[task.id] = task
        task_type = task.type.value
        if task_type not in self._task_index:
            self._task_index[task_type] = []
        self._task_index[task_type].append(task.id)
        logger.debug(f"创建任务: {task.id} ({task.type})")

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self._tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务"""
        if task_id not in self._tasks:
            return False
        task = self._tasks[task_id]

        # 记录之前的状态用于比较
        old_status = task.status
        old_progress = task.progress

        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        # 如果状态或进度发生变化，发送WebSocket通知
        new_status = task.status
        new_progress = task.progress

        if old_status != new_status or old_progress != new_progress:
            asyncio.create_task(
                self._notify_task_update(task_id, new_status, new_progress)
            )

        return True

    async def _notify_task_update(
        self, task_id: str, status: TaskStatus, progress: float
    ) -> None:
        """通知任务更新到WebSocket订阅者"""
        try:
            ws_manager = _get_ws_manager()
            await ws_manager.send_task_update(task_id, status.value, progress)
        except Exception as e:
            logger.error(f"发送任务更新通知失败: {e}")

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Task]:
        """列出任务"""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        if task_type:
            tasks = [t for t in tasks if t.type == task_type]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[offset:offset + limit]

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id not in self._tasks:
            return False
        task = self._tasks[task_id]
        task_type = task.type.value
        if task_type in self._task_index:
            self._task_index[task_type].remove(task_id)
        del self._tasks[task_id]
        return True

    def get_task_count(self, status: Optional[TaskStatus] = None) -> int:
        """获取任务数量"""
        if status:
            return sum(1 for t in self._tasks.values() if t.status == status)
        return len(self._tasks)


class TaskExecutor:
    """任务执行器基类"""

    def __init__(self):
        self._storage = TaskStorage()
        self._executor_lock = asyncio.Lock()
        self._running_tasks: Dict[str, asyncio.Task] = {}

    async def submit_task(
        self,
        task_type: TaskType,
        prompt: str,
        parameters: Dict[str, Any],
        model_id: str,
        **kwargs
    ) -> str:
        """提交任务"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            type=task_type,
            prompt=prompt,
            parameters=parameters,
            model_id=model_id,
            metadata=kwargs
        )
        self._storage.create_task(task)
        await self._schedule_task(task_id)
        return task_id

    async def _schedule_task(self, task_id: str) -> None:
        """调度任务执行"""
        async with self._executor_lock:
            if task_id in self._running_tasks:
                return
            task = self._storage.get_task(task_id)
            if not task or task.status != TaskStatus.PENDING:
                return

            # 标记为运行中
            self._storage.update_task(
                task_id,
                status=TaskStatus.RUNNING,
                started_at=datetime.now()
            )

            # 创建异步任务
            self._running_tasks[task_id] = asyncio.create_task(
                self._execute_task(task_id)
            )

    async def _execute_task(self, task_id: str) -> None:
        """执行任务（模板方法）"""
        try:
            task = self._storage.get_task(task_id)
            if not task:
                return

            logger.info(f"开始执行任务: {task_id}")

            # 模拟执行过程（实际实现中会调用模型）
            for i in range(10):
                progress = (i + 1) * 10
                await asyncio.sleep(0.2)  # 模拟处理时间
                self._storage.update_task(task_id, progress=progress)

            # 生成模拟结果
            result = await self._generate_result(task)

            self._storage.update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                progress=100.0,
                result=result,
                completed_at=datetime.now()
            )
            logger.info(f"任务完成: {task_id}")

        except Exception as e:
            logger.error(f"任务失败 {task_id}: {e}")
            self._storage.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                completed_at=datetime.now()
            )
        finally:
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

    async def _generate_result(self, task: Task) -> Dict[str, Any]:
        """生成模拟结果"""
        result_types = {
            TaskType.IMAGE_GENERATION: {
                "type": "image",
                "url": f"/api/v1/tasks/{task.id}/result/image",
                "width": task.parameters.get("width", 1024),
                "height": task.parameters.get("height", 768),
                "seed": task.parameters.get("seed", 42),
            },
            TaskType.VIDEO_GENERATION: {
                "type": "video",
                "url": f"/api/v1/tasks/{task.id}/result/video",
                "duration": 5.0,
                "fps": 24,
            },
            TaskType.AUDIO_GENERATION: {
                "type": "audio",
                "url": f"/api/v1/tasks/{task.id}/result/audio",
                "duration": 10.0,
                "sample_rate": 24000,
            },
            TaskType.TEXT_GENERATION: {
                "type": "text",
                "content": (
                    f"根据您的提示 '{task.prompt}'，这是生成的文本响应。"
                    "实际实现中将包含真实的LLM输出。"
                ),
                "tokens": 128,
            },
            TaskType.CODE_GENERATION: {
                "type": "code",
                "language": "python",
                "content": "# 生成的代码\nprint('Hello, World!')",
                "lines": 15,
            },
        }
        return result_types.get(task.type, {"type": "unknown"})

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self._storage.get_task(task_id)
        if not task:
            return False

        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]

        self._storage.update_task(
            task_id,
            status=TaskStatus.CANCELLED,
            completed_at=datetime.now()
        )
        return True

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        task = self._storage.get_task(task_id)
        if not task:
            return None
        return {
            "id": task.id,
            "type": task.type.value,
            "prompt": task.prompt,
            "parameters": task.parameters,
            "status": task.status.value,
            "progress": task.progress,
            "model_id": task.model_id,
            "result": task.result,
            "error": task.error,
            "created_at": task.created_at.isoformat(),
            "started_at": (
                task.started_at.isoformat()
                if task.started_at
                else None
            ),
            "completed_at": (
                task.completed_at.isoformat()
                if task.completed_at
                else None
            ),
            "metadata": task.metadata,
        }

    def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出任务"""
        status_enum = TaskStatus(status) if status else None
        type_enum = TaskType(task_type) if task_type else None

        tasks = self._storage.list_tasks(status_enum, type_enum, limit, offset)
        return [
            self.get_task_info(t.id)
            for t in tasks
            if self.get_task_info(t.id)
        ]

    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计"""
        return {
            "total": self._storage.get_task_count(),
            "pending": self._storage.get_task_count(TaskStatus.PENDING),
            "running": self._storage.get_task_count(TaskStatus.RUNNING),
            "completed": self._storage.get_task_count(TaskStatus.COMPLETED),
            "failed": self._storage.get_task_count(TaskStatus.FAILED),
            "cancelled": self._storage.get_task_count(TaskStatus.CANCELLED),
            "active_workers": len(self._running_tasks),
        }


# 全局单例
_task_executor = None


def get_task_executor() -> TaskExecutor:
    """获取任务执行器实例"""
    global _task_executor
    if _task_executor is None:
        _task_executor = TaskExecutor()
    return _task_executor
