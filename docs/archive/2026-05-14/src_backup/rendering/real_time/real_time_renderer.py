"""实时渲染引擎 - 支持实时预览"""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger("hydraflow.real_time_renderer")


class RenderQuality(Enum):
    """渲染质量"""
    DRAFT = "draft"       # 草稿级
    PREVIEW = "preview"   # 预览级
    STANDARD = "standard" # 标准级
    HIGH = "high"         # 高质量


class RenderStatus(Enum):
    """渲染状态"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RENDERING = "rendering"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RenderFrame:
    """渲染帧"""
    frame_id: str
    timestamp: float
    quality: RenderQuality
    data: Any = None
    width: int = 0
    height: int = 0


@dataclass
class RenderTask:
    """渲染任务"""
    task_id: str
    project_id: str
    scene_data: Any
    quality: RenderQuality
    total_frames: int
    current_frame: int = 0
    status: RenderStatus = RenderStatus.IDLE
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class RenderPipeline(ABC):
    """渲染管线基类"""

    @abstractmethod
    async def initialize(self, project_data: Any) -> bool:
        """初始化渲染管线"""
        pass

    @abstractmethod
    async def render_frame(self, scene_data: Any) -> RenderFrame:
        """渲染单帧"""
        pass

    @abstractmethod
    async def cleanup(self):
        """清理资源"""
        pass


class SoftwareRenderPipeline(RenderPipeline):
    """软件渲染管线"""

    def __init__(self):
        self.initialized = False

    async def initialize(self, project_data: Any) -> bool:
        """初始化"""
        await asyncio.sleep(0.5)
        self.initialized = True
        return True

    async def render_frame(self, scene_data: Any) -> RenderFrame:
        """渲染帧（模拟）"""
        await asyncio.sleep(0.05)
        return RenderFrame(
            frame_id=str(uuid.uuid4()),
            timestamp=time.time(),
            quality=RenderQuality.PREVIEW,
            width=1920,
            height=1080,
        )

    async def cleanup(self):
        """清理"""
        self.initialized = False


class RealTimeRenderer:
    """实时渲染器"""

    def __init__(
        self,
        pipeline: RenderPipeline = None,
        max_buffer_size: int = 30,
        target_fps: int = 30
    ):
        self.pipeline = pipeline or SoftwareRenderPipeline()
        self.max_buffer_size = max_buffer_size
        self.target_fps = target_fps

        self.active_tasks: Dict[str, RenderTask] = {}
        self.frame_buffers: Dict[str, asyncio.Queue] = {}
        self.render_workers: Dict[str, asyncio.Task] = {}

        self._running = False

        logger.info(f"RealTimeRenderer initialized (target_fps={target_fps})")

    async def start_render(
        self,
        project_id: str,
        scene_data: Any,
        quality: RenderQuality = RenderQuality.PREVIEW,
        total_frames: int = -1
    ) -> str:
        """开始渲染"""
        task_id = str(uuid.uuid4())

        task = RenderTask(
            task_id=task_id,
            project_id=project_id,
            scene_data=scene_data,
            quality=quality,
            total_frames=total_frames,
            status=RenderStatus.INITIALIZING,
        )

        self.active_tasks[task_id] = task
        self.frame_buffers[task_id] = asyncio.Queue(maxsize=self.max_buffer_size)

        await self.pipeline.initialize(scene_data)

        task.status = RenderStatus.RENDERING
        task.started_at = time.time()

        worker = asyncio.create_task(self._render_loop(task))
        self.render_workers[task_id] = worker

        self._running = True

        logger.info(f"Started render task: {task_id}")
        return task_id

    async def _render_loop(self, task: RenderTask):
        """渲染循环"""
        buffer = self.frame_buffers[task.task_id]
        frame_interval = 1.0 / self.target_fps

        while self._running and task.status == RenderStatus.RENDERING:
            if task.total_frames > 0 and task.current_frame >= task.total_frames:
                break

            try:
                frame = await self.pipeline.render_frame(task.scene_data)
                frame.frame_id = f"{task.task_id}_frame_{task.current_frame}"

                await asyncio.wait_for(buffer.put(frame), timeout=frame_interval)
                task.current_frame += 1

            except asyncio.TimeoutError:
                logger.warning(f"Frame render timeout for task {task.task_id}")
            except Exception as e:
                logger.error(f"Render error for task {task.task_id}: {e}")
                task.status = RenderStatus.FAILED
                break

        if task.status == RenderStatus.RENDERING:
            task.status = RenderStatus.COMPLETED
            task.completed_at = time.time()

        await buffer.put(None)

        logger.info(f"Render task {task.task_id} completed: {task.current_frame} frames")

    async def get_frame(self, task_id: str) -> Optional[RenderFrame]:
        """获取帧"""
        if task_id not in self.frame_buffers:
            return None

        buffer = self.frame_buffers[task_id]

        try:
            frame = await asyncio.wait_for(buffer.get(), timeout=1.0)
            return frame
        except asyncio.TimeoutError:
            return None

    async def pause_render(self, task_id: str):
        """暂停渲染"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].status = RenderStatus.PAUSED
            logger.info(f"Paused render task: {task_id}")

    async def resume_render(self, task_id: str):
        """恢复渲染"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].status = RenderStatus.RENDERING
            logger.info(f"Resumed render task: {task_id}")

    async def stop_render(self, task_id: str):
        """停止渲染"""
        if task_id in self.render_workers:
            self.render_workers[task_id].cancel()

        if task_id in self.active_tasks:
            self.active_tasks[task_id].status = RenderStatus.FAILED

        logger.info(f"Stopped render task: {task_id}")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id not in self.active_tasks:
            return None

        task = self.active_tasks[task_id]
        buffer_size = 0

        if task_id in self.frame_buffers:
            buffer_size = self.frame_buffers[task_id].qsize()

        return {
            "task_id": task.task_id,
            "project_id": task.project_id,
            "status": task.status.value,
            "quality": task.quality.value,
            "current_frame": task.current_frame,
            "total_frames": task.total_frames,
            "buffer_size": buffer_size,
            "progress": task.current_frame / task.total_frames if task.total_frames > 0 else 0,
            "fps": self.target_fps,
        }

    async def shutdown(self):
        """关闭渲染器"""
        self._running = False

        for worker in self.render_workers.values():
            worker.cancel()

        await asyncio.gather(*self.render_workers.values(), return_exceptions=True)

        await self.pipeline.cleanup()

        self.active_tasks.clear()
        self.frame_buffers.clear()
        self.render_workers.clear()

        logger.info("RealTimeRenderer shutdown")


# 全局单例
_renderer_instance: Optional[RealTimeRenderer] = None


def get_real_time_renderer() -> RealTimeRenderer:
    """获取实时渲染器"""
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = RealTimeRenderer()
    return _renderer_instance
