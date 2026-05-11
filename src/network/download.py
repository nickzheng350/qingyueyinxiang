"""HydraFlow AI 网络下载管理器"""

import asyncio
import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Callable, Optional
import ssl
import certifi

import httpx

from src.core.config import get_settings
from src.core.exceptions import StorageError

settings = get_settings()


class DownloadStatus(str, Enum):
    """下载状态"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class DownloadError(Exception):
    """下载错误"""
    pass


@dataclass
class DownloadProgress:
    """下载进度"""
    url: str
    total_size: int
    downloaded_size: int
    status: DownloadStatus
    speed: float
    error: Optional[str] = None

    @property
    def progress(self) -> float:
        """获取进度百分比"""
        if self.total_size == 0:
            return 0.0
        return (self.downloaded_size / self.total_size) * 100

    @property
    def progress_str(self) -> str:
        """获取进度字符串"""
        downloaded_mb = self.downloaded_size / (1024 * 1024)
        total_mb = self.total_size / (1024 * 1024)
        speed_mb = self.speed / (1024 * 1024)
        return f"{downloaded_mb:.2f}/{total_mb:.2f} MB ({self.progress:.1f}%) - {speed_mb:.2f} MB/s"


class DownloadTask:
    """下载任务"""

    def __init__(
        self,
        url: str,
        destination: str | Path,
        filename: Optional[str] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        timeout: int = 300,
        chunk_size: int = 8192,
        max_retries: int = 3,
        retry_delay: int = 5,
        resume: bool = True,
        verify_ssl: bool = True,
        expected_hash: Optional[str] = None,
        hash_algorithm: str = "sha256",
    ):
        self.url = url
        self.destination = Path(destination)
        self.filename = filename
        self.headers = headers or {}
        self.cookies = cookies
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.resume = resume
        self.verify_ssl = verify_ssl
        self.expected_hash = expected_hash
        self.hash_algorithm = hash_algorithm

        self.status = DownloadStatus.PENDING
        self.progress = DownloadProgress(
            url=url,
            total_size=0,
            downloaded_size=0,
            status=DownloadStatus.PENDING,
            speed=0.0,
        )
        self._cancel_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()


class DownloadManager:
    """下载管理器"""

    _instance: Optional["DownloadManager"] = None

    def __new__(cls) -> "DownloadManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tasks: dict[str, DownloadTask] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._download_dir = settings.storage.local_path / "downloads"
        self._download_dir.mkdir(parents=True, exist_ok=True)
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

    def _get_lock(self, task_id: str) -> asyncio.Lock:
        """获取任务锁"""
        if task_id not in self._locks:
            self._locks[task_id] = asyncio.Lock()
        return self._locks[task_id]

    async def _do_download(
        self,
        task: DownloadTask,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """执行下载"""
        task_id = hashlib.md5(task.url.encode()).hexdigest()
        lock = self._get_lock(task_id)

        async with lock:
            if task.resume and (task.destination / task.filename).exists():
                existing_size = (task.destination / task.filename).stat().st_size
                task.headers["Range"] = f"bytes={existing_size}-"
                task.progress.downloaded_size = existing_size

            timeout = httpx.Timeout(task.timeout, connect=30)
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

            async with httpx.AsyncClient(
                timeout=timeout,
                limits=limits,
                verify=self._ssl_context if task.verify_ssl else False,
            ) as client:
                headers = task.headers.copy()
                if task.cookies:
                    client.cookies.update(task.cookies)

                async with client.stream("GET", task.url, headers=headers) as response:
                    if response.status_code not in (200, 206):
                        raise DownloadError(
                            f"HTTP {response.status_code}: {response.reason_phrase}"
                        )

                    content_length = response.headers.get("content-length")
                    if content_length:
                        task.progress.total_size = int(content_length)
                        if task.headers.get("Range"):
                            task.progress.total_size += task.progress.downloaded_size

                    task.status = DownloadStatus.DOWNLOADING
                    task.progress.status = DownloadStatus.DOWNLOADING

                    task.destination.mkdir(parents=True, exist_ok=True)
                    file_path = task.destination / task.filename

                    with open(file_path, "ab" if task.resume else "wb") as f:
                        downloaded = task.progress.downloaded_size
                        last_update = datetime.now()
                        bytes_per_second = 0

                        async for chunk in response.aiter_bytes(task.chunk_size):
                            await task._pause_event.wait()

                            if task._cancel_event.is_set():
                                task.status = DownloadStatus.CANCELLED
                                task.progress.status = DownloadStatus.CANCELLED
                                raise asyncio.CancelledError("下载已取消")

                            f.write(chunk)
                            downloaded += len(chunk)
                            task.progress.downloaded_size = downloaded

                            now = datetime.now()
                            time_diff = (now - last_update).total_seconds()
                            if time_diff >= 1.0:
                                bytes_per_second = (downloaded - task.progress.downloaded_size) / time_diff
                                task.progress.speed = bytes_per_second
                                last_update = now

                            if progress_callback:
                                progress_callback(task.progress)

                    if task.expected_hash:
                        await self._verify_hash(file_path, task.expected_hash, task.hash_algorithm)

                    task.status = DownloadStatus.COMPLETED
                    task.progress.status = DownloadStatus.COMPLETED
                    return file_path

    async def _verify_hash(self, file_path: Path, expected_hash: str, algorithm: str) -> None:
        """验证文件哈希"""
        hash_obj = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)

        actual_hash = hash_obj.hexdigest()
        if actual_hash != expected_hash:
            raise DownloadError(
                f"文件哈希验证失败: 期望 {expected_hash}, 实际 {actual_hash}"
            )

    async def download(
        self,
        url: str,
        destination: Optional[str | Path] = None,
        filename: Optional[str] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        timeout: int = 300,
        chunk_size: int = 8192,
        max_retries: int = 3,
        retry_delay: int = 5,
        resume: bool = True,
        verify_ssl: bool = True,
        expected_hash: Optional[str] = None,
        hash_algorithm: str = "sha256",
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """下载文件"""
        if destination is None:
            destination = self._download_dir
        else:
            destination = Path(destination)

        if filename is None:
            filename = self._extract_filename(url, headers)

        task = DownloadTask(
            url=url,
            destination=destination,
            filename=filename,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            chunk_size=chunk_size,
            max_retries=max_retries,
            retry_delay=retry_delay,
            resume=resume,
            verify_ssl=verify_ssl,
            expected_hash=expected_hash,
            hash_algorithm=hash_algorithm,
        )

        task_id = hashlib.md5(url.encode()).hexdigest()
        self._tasks[task_id] = task

        try:
            for attempt in range(task.max_retries):
                try:
                    return await self._do_download(task, progress_callback)
                except (asyncio.CancelledError, DownloadError):
                    raise
                except Exception as e:
                    if attempt < task.max_retries - 1:
                        await asyncio.sleep(task.retry_delay)
                        task.status = DownloadStatus.PENDING
                        task.progress.status = DownloadStatus.PENDING
                        task.progress.error = str(e)
                    else:
                        task.status = DownloadStatus.FAILED
                        task.progress.status = DownloadStatus.FAILED
                        task.progress.error = str(e)
                        raise DownloadError(f"下载失败（已重试 {attempt + 1} 次）: {e}")
        finally:
            if task_id in self._tasks:
                del self._tasks[task_id]

    def _extract_filename(self, url: str, headers: Optional[dict] = None) -> str:
        """提取文件名"""
        if headers and "content-disposition" in headers:
            import re
            match = re.search(r'filename[^;=\n]*=((["\']).*?\2|[^;\n]*)', headers["content-disposition"])
            if match:
                return match.group(1).strip('"').strip("'")

        parsed = httpx.URL(url)
        path_segments = parsed.path.split("/")
        if path_segments and path_segments[-1]:
            return path_segments[-1].split("?")[0]

        return "download_" + hashlib.md5(url.encode()).hexdigest()[:8]

    async def cancel(self, url: str) -> bool:
        """取消下载"""
        task_id = hashlib.md5(url.encode()).hexdigest()
        if task_id in self._tasks:
            self._tasks[task_id]._cancel_event.set()
            return True
        return False

    async def pause(self, url: str) -> bool:
        """暂停下载"""
        task_id = hashlib.md5(url.encode()).hexdigest()
        if task_id in self._tasks:
            self._tasks[task_id]._pause_event.clear()
            self._tasks[task_id].status = DownloadStatus.PAUSED
            self._tasks[task_id].progress.status = DownloadStatus.PAUSED
            return True
        return False

    async def resume_download(self, url: str) -> bool:
        """恢复下载"""
        task_id = hashlib.md5(url.encode()).hexdigest()
        if task_id in self._tasks:
            self._tasks[task_id]._pause_event.set()
            self._tasks[task_id].status = DownloadStatus.DOWNLOADING
            self._tasks[task_id].progress.status = DownloadStatus.DOWNLOADING
            return True
        return False

    def get_progress(self, url: str) -> Optional[DownloadProgress]:
        """获取下载进度"""
        task_id = hashlib.md5(url.encode()).hexdigest()
        if task_id in self._tasks:
            return self._tasks[task_id].progress
        return None

    def get_status(self, url: str) -> Optional[DownloadStatus]:
        """获取下载状态"""
        task_id = hashlib.md5(url.encode()).hexdigest()
        if task_id in self._tasks:
            return self._tasks[task_id].status
        return None


class ModelDownloader:
    """模型下载器"""

    MODEL_MIRRORS = {
        "huggingface": "https://huggingface.co",
        "modelscope": "https://www.modelscope.cn",
        "local": "http://localhost:8000",
    }

    def __init__(self):
        self.manager = get_download_manager()

    async def download_model(
        self,
        model_id: str,
        source: str = "huggingface",
        destination: Optional[Path] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """下载模型"""
        if source not in self.MODEL_MIRRORS:
            raise ValueError(f"不支持的模型源: {source}")

        if source == "huggingface":
            url = f"https://huggingface.co/{model_id}/resolve/main/model.safetensors"
        elif source == "modelscope":
            url = f"https://www.modelscope.cn/{model_id}/resolve/master/model.safetensors"
        else:
            url = f"http://localhost:8000/models/{model_id}/download"

        if destination is None:
            destination = settings.storage.local_path / "models" / source / model_id

        filename = f"{model_id.split('/')[-1]}.safetensors"

        return await self.manager.download(
            url=url,
            destination=destination,
            filename=filename,
            timeout=3600,
            chunk_size=1024 * 1024,
            max_retries=5,
            retry_delay=10,
            progress_callback=progress_callback,
        )

    async def download_checkpoint(
        self,
        checkpoint_url: str,
        destination: Optional[Path] = None,
        expected_hash: Optional[str] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """下载检查点/权重文件"""
        if destination is None:
            destination = settings.storage.local_path / "checkpoints"

        filename = self.manager._extract_filename(checkpoint_url)

        return await self.manager.download(
            url=checkpoint_url,
            destination=destination,
            filename=filename,
            expected_hash=expected_hash,
            timeout=3600,
            chunk_size=1024 * 1024,
            max_retries=3,
            progress_callback=progress_callback,
        )


class SkillDownloader:
    """技能包下载器"""

    SKILL_MARKET_URL = "https://hydraflow-ai.org/market/api/v1"

    def __init__(self):
        self.manager = get_download_manager()

    async def download_skill(
        self,
        skill_id: str,
        version: Optional[str] = None,
        destination: Optional[Path] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """下载技能包"""
        if destination is None:
            destination = settings.storage.local_path / "skills"

        version_part = f"/versions/{version}" if version else "/latest"
        url = f"{self.SKILL_MARKET_URL}/skills/{skill_id}{version_part}/download"

        filename = f"{skill_id}{version_part.lstrip('/')}.zip"

        return await self.manager.download(
            url=url,
            destination=destination,
            filename=filename,
            timeout=600,
            chunk_size=512 * 1024,
            max_retries=3,
            progress_callback=progress_callback,
        )

    async def list_market_skills(
        self,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """列出市场技能"""
        url = f"{self.SKILL_MARKET_URL}/skills"
        params = {"page": page, "page_size": page_size}
        if category:
            params["category"] = category

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()


_download_manager_instance: Optional[DownloadManager] = None


def get_download_manager() -> DownloadManager:
    """获取下载管理器单例"""
    global _download_manager_instance
    if _download_manager_instance is None:
        _download_manager_instance = DownloadManager()
    return _download_manager_instance


def get_model_downloader() -> ModelDownloader:
    """获取模型下载器"""
    return ModelDownloader()


def get_skill_downloader() -> SkillDownloader:
    """获取技能下载器"""
    return SkillDownloader()
