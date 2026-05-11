"""HydraFlow AI 文件存储模块 - 支持本地存储、MinIO 和 S3"""

import io
import os
import uuid
import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
from datetime import datetime, timedelta

from src.core.config import get_settings, StorageType

settings = get_settings()


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def save(self, file_data: bytes | BinaryIO, file_path: str) -> str:
        """保存文件，返回文件路径或 URL"""
        pass

    @abstractmethod
    async def load(self, file_path: str) -> bytes:
        """加载文件，返回文件内容"""
        pass

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        """获取文件访问 URL"""
        pass

    @abstractmethod
    async def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        pass


class LocalStorageBackend(StorageBackend):
    """本地文件系统存储"""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or settings.storage.local_path
        self.base_path = Path(self.base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, file_path: str) -> Path:
        """获取完整文件路径"""
        full_path = (self.base_path / file_path).resolve()
        if not full_path.is_relative_to(self.base_path):
            raise ValueError(f"非法文件路径: {file_path}")
        return full_path

    async def save(self, file_data: bytes | BinaryIO, file_path: str) -> str:
        full_path = self._get_full_path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(file_data, bytes):
            full_path.write_bytes(file_data)
        else:
            with open(full_path, "wb") as f:
                f.write(file_data.read())

        return file_path

    async def load(self, file_path: str) -> bytes:
        full_path = self._get_full_path(file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        return full_path.read_bytes()

    async def exists(self, file_path: str) -> bool:
        full_path = self._get_full_path(file_path)
        return full_path.exists()

    async def delete(self, file_path: str) -> bool:
        full_path = self._get_full_path(file_path)
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        return f"/api/v1/files/{file_path}"

    async def get_file_info(self, file_path: str) -> dict:
        full_path = self._get_full_path(file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        stat = full_path.stat()
        mime_type, _ = mimetypes.guess_type(full_path.name)

        return {
            "path": file_path,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "modified_at": datetime.fromtimestamp(stat.st_mtime),
            "mime_type": mime_type or "application/octet-stream",
        }


class MinIOStorageBackend(StorageBackend):
    """MinIO 对象存储"""

    def __init__(self):
        try:
            from minio import Minio
            from minio.error import S3Error
        except ImportError:
            raise ImportError("请安装 minio: pip install minio")

        if not settings.storage.minio_endpoint:
            raise ValueError("MinIO 端点未配置")
        if not settings.storage.minio_access_key:
            raise ValueError("MinIO 访问密钥未配置")
        if not settings.storage.minio_secret_key:
            raise ValueError("MinIO 秘密密钥未配置")

        self.client = Minio(
            settings.storage.minio_endpoint,
            access_key=settings.storage.minio_access_key,
            secret_key=settings.storage.minio_secret_key,
            secure=settings.storage.minio_secure,
        )
        self.bucket = settings.storage.minio_bucket

        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保 bucket 存在"""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    async def save(self, file_data: bytes | BinaryIO, file_path: str) -> str:
        from minio.error import S3Error

        if isinstance(file_data, bytes):
            file_data = io.BytesIO(file_data)
            length = len(file_data.getvalue())
        else:
            file_data.seek(0, os.SEEK_END)
            length = file_data.tell()
            file_data.seek(0)

        mime_type, _ = mimetypes.guess_type(file_path)
        content_type = mime_type or "application/octet-stream"

        self.client.put_object(
            self.bucket,
            file_path,
            file_data,
            length=length,
            content_type=content_type,
        )

        return file_path

    async def load(self, file_path: str) -> bytes:
        from minio.error import S3Error

        try:
            response = self.client.get_object(self.bucket, file_path)
            return response.read()
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"文件不存在: {file_path}") from e
            raise

    async def exists(self, file_path: str) -> bool:
        from minio.error import S3Error

        try:
            self.client.stat_object(self.bucket, file_path)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise

    async def delete(self, file_path: str) -> bool:
        from minio.error import S3Error

        try:
            self.client.remove_object(self.bucket, file_path)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise

    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        return self.client.presigned_get_object(
            self.bucket,
            file_path,
            expires=timedelta(seconds=expires_in),
        )

    async def get_file_info(self, file_path: str) -> dict:
        from minio.error import S3Error

        try:
            stat = self.client.stat_object(self.bucket, file_path)
            return {
                "path": file_path,
                "size": stat.size,
                "created_at": stat.last_modified,
                "mime_type": stat.content_type,
                "etag": stat.etag,
            }
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"文件不存在: {file_path}") from e
            raise


class S3StorageBackend(StorageBackend):
    """AWS S3 存储"""

    def __init__(self):
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError("请安装 boto3: pip install boto3")

        if not settings.storage.s3_access_key_id:
            raise ValueError("S3 访问密钥 ID 未配置")
        if not settings.storage.s3_secret_access_key:
            raise ValueError("S3 秘密访问密钥未配置")

        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.storage.s3_access_key_id,
            aws_secret_access_key=settings.storage.s3_secret_access_key,
            region_name=settings.storage.s3_region,
        )
        self.bucket = settings.storage.s3_bucket

    async def save(self, file_data: bytes | BinaryIO, file_path: str) -> str:
        from botocore.exceptions import ClientError

        if isinstance(file_data, bytes):
            body = file_data
        else:
            body = file_data

        mime_type, _ = mimetypes.guess_type(file_path)
        content_type = mime_type or "application/octet-stream"

        self.client.put_object(
            Bucket=self.bucket,
            Key=file_path,
            Body=body,
            ContentType=content_type,
        )

        return file_path

    async def load(self, file_path: str) -> bytes:
        from botocore.exceptions import ClientError

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=file_path)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"文件不存在: {file_path}") from e
            raise

    async def exists(self, file_path: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=file_path)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    async def delete(self, file_path: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.delete_object(Bucket=self.bucket, Key=file_path)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return False
            raise

    async def get_url(self, file_path: str, expires_in: int = 3600) -> str:
        from botocore.exceptions import ClientError

        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": file_path},
            ExpiresIn=expires_in,
        )

    async def get_file_info(self, file_path: str) -> dict:
        from botocore.exceptions import ClientError

        try:
            response = self.client.head_object(Bucket=self.bucket, Key=file_path)
            return {
                "path": file_path,
                "size": response["ContentLength"],
                "created_at": response["LastModified"],
                "mime_type": response["ContentType"],
                "etag": response["ETag"],
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"文件不存在: {file_path}") from e
            raise


class StorageManager:
    """存储管理器 - 统一接口"""

    _instance: Optional["StorageManager"] = None

    def __new__(cls) -> "StorageManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.backend = self._create_backend()

    def _create_backend(self) -> StorageBackend:
        """创建存储后端"""
        if settings.storage.type == StorageType.LOCAL:
            return LocalStorageBackend()
        elif settings.storage.type == StorageType.MINIO:
            return MinIOStorageBackend()
        elif settings.storage.type == StorageType.S3:
            return S3StorageBackend()
        else:
            raise ValueError(f"不支持的存储类型: {settings.storage.type}")

    def generate_path(self, prefix: str = "", extension: str = "") -> str:
        """生成唯一文件路径"""
        unique_id = str(uuid.uuid4())
        date_path = datetime.utcnow().strftime("%Y/%m/%d")

        if prefix:
            prefix = prefix.strip("/")
            path_parts = [prefix, date_path, unique_id]
        else:
            path_parts = [date_path, unique_id]

        if extension:
            if not extension.startswith("."):
                extension = f".{extension}"
            path_parts[-1] += extension

        return "/".join(path_parts)

    async def save_file(
        self,
        file_data: bytes | BinaryIO,
        prefix: str = "",
        extension: str = "",
        file_path: Optional[str] = None,
    ) -> str:
        """保存文件，返回文件路径"""
        if not file_path:
            file_path = self.generate_path(prefix, extension)
        return await self.backend.save(file_data, file_path)

    async def load_file(self, file_path: str) -> bytes:
        """加载文件"""
        return await self.backend.load(file_path)

    async def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        return await self.backend.exists(file_path)

    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        return await self.backend.delete(file_path)

    async def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """获取文件访问 URL"""
        return await self.backend.get_url(file_path, expires_in)

    async def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        return await self.backend.get_file_info(file_path)


def get_storage_manager() -> StorageManager:
    """获取存储管理器单例"""
    return StorageManager()


class SQLiteStorage:
    """SQLite 兼容层 - 保留旧接口"""

    def __init__(self):
        from src.core.config import get_settings
        self.settings = get_settings()
        self._tasks: dict[str, dict] = {}

    def save_task(self, task_info: dict) -> None:
        """保存任务信息（兼容旧接口）"""
        task_id = task_info.get("id") or task_info.get("task_id")
        if task_id:
            self._tasks[task_id] = task_info

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取任务信息（兼容旧接口）"""
        return self._tasks.get(task_id)

    def save_result(self, task_id: str, result: dict) -> None:
        """保存任务结果（兼容旧接口）"""
        if task_id in self._tasks:
            self._tasks[task_id]["result"] = result

    def get_result(self, task_id: str) -> Optional[dict]:
        """获取任务结果（兼容旧接口）"""
        task = self._tasks.get(task_id)
        return task.get("result") if task else None

    def delete_task(self, task_id: str) -> bool:
        """删除任务（兼容旧接口）"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """列出任务（兼容旧接口）"""
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        if task_type:
            tasks = [t for t in tasks if t.get("type") == task_type]

        return tasks[offset:offset + limit]


_storage_instance: Optional[SQLiteStorage] = None


def get_storage() -> SQLiteStorage:
    """获取存储实例（兼容旧接口）"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = SQLiteStorage()
    return _storage_instance
