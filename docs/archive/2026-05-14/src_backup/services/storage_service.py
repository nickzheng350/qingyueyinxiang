"""文件存储服务 - 支持多后端存储、智能缓存、加密压缩"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple, List, BinaryIO
from datetime import datetime
from abc import ABC, abstractmethod

from src.core.config import get_settings, StorageBackend, StorageTier
from src.core.exceptions import StorageError


class BaseStorageBackend(ABC):
    """存储后端基类"""

    @abstractmethod
    def upload_file(self, file: BinaryIO, filename: str, destination: str = "") -> str:
        """上传文件"""
        pass

    @abstractmethod
    def download_file(self, file_id: str) -> Tuple[BinaryIO, str]:
        """下载文件"""
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> List[dict]:
        """列出文件"""
        pass

    @abstractmethod
    def get_file_info(self, file_id: str) -> Optional[dict]:
        """获取文件信息"""
        pass

    @abstractmethod
    def exists(self, file_id: str) -> bool:
        """检查文件是否存在"""
        pass


class LocalStorageBackend(BaseStorageBackend):
    """本地文件存储后端"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload_file(self, file: BinaryIO, filename: str, destination: str = "") -> str:
        try:
            file_id = str(uuid.uuid4())
            ext = Path(filename).suffix
            full_filename = f"{file_id}{ext}"
            
            if destination:
                target_dir = self.base_path / destination
                target_dir.mkdir(parents=True, exist_ok=True)
            else:
                target_dir = self.base_path
            
            file_path = target_dir / full_filename
            
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file, f)
            
            return f"{destination}/{full_filename}" if destination else full_filename
        except Exception as e:
            raise StorageError(f"文件上传失败: {str(e)}")

    def download_file(self, file_id: str) -> Tuple[BinaryIO, str]:
        file_path = self.base_path / file_id
        if not file_path.exists():
            raise StorageError(f"文件不存在: {file_id}")
        
        try:
            f = open(file_path, 'rb')
            return f, file_path.name
        except Exception as e:
            raise StorageError(f"文件下载失败: {str(e)}")

    def delete_file(self, file_id: str) -> bool:
        file_path = self.base_path / file_id
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            raise StorageError(f"文件删除失败: {str(e)}")

    def list_files(self, prefix: str = "") -> List[dict]:
        try:
            target_dir = self.base_path / prefix if prefix else self.base_path
            files = []
            
            if not target_dir.exists():
                return files
            
            for item in target_dir.iterdir():
                if item.is_file():
                    stat = item.stat()
                    files.append({
                        'file_id': str(item.relative_to(self.base_path)),
                        'name': item.name,
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return sorted(files, key=lambda x: x['modified_at'], reverse=True)
        except Exception as e:
            raise StorageError(f"文件列表获取失败: {str(e)}")

    def get_file_info(self, file_id: str) -> Optional[dict]:
        file_path = self.base_path / file_id
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            return {
                'file_id': file_id,
                'name': file_path.name,
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            raise StorageError(f"文件信息获取失败: {str(e)}")

    def exists(self, file_id: str) -> bool:
        return (self.base_path / file_id).exists()


class StorageService:
    """统一存储服务"""

    _instance: "StorageService | None" = None

    def __new__(cls) -> "StorageService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.settings = get_settings().storage
        self.backend = self._create_backend()
        
        # 初始化存储目录
        if self.settings.backend == StorageBackend.LOCAL:
            self.settings.local_path.mkdir(parents=True, exist_ok=True)
            self.settings.local_backup_path.mkdir(parents=True, exist_ok=True)

    def _create_backend(self) -> BaseStorageBackend:
        """根据配置创建存储后端"""
        backend = self.settings.backend
        
        if backend == StorageBackend.LOCAL:
            return LocalStorageBackend(self.settings.local_path)
        elif backend == StorageBackend.MINIO:
            return self._create_minio_backend()
        elif backend == StorageBackend.S3:
            return self._create_s3_backend()
        elif backend in [StorageBackend.NAS, StorageBackend.SAN]:
            return LocalStorageBackend(Path(self.settings.nas_path or self.settings.local_path))
        else:
            return LocalStorageBackend(self.settings.local_path)

    def _create_minio_backend(self) -> BaseStorageBackend:
        """创建 MinIO 后端（占位）"""
        try:
            from minio import Minio
            from minio.error import S3Error
            
            class MinIOStorageBackend(BaseStorageBackend):
                def __init__(self, settings):
                    self.client = Minio(
                        settings.minio_endpoint,
                        access_key=settings.minio_access_key,
                        secret_key=settings.minio_secret_key,
                        secure=settings.minio_secure
                    )
                    self.bucket = settings.minio_bucket
                    
                    # 确保桶存在
                    if not self.client.bucket_exists(self.bucket):
                        self.client.make_bucket(self.bucket)

                def upload_file(self, file: BinaryIO, filename: str, destination: str = "") -> str:
                    object_name = f"{destination}/{filename}" if destination else filename
                    self.client.put_object(self.bucket, object_name, file, length=-1, part_size=10*1024*1024)
                    return object_name

                def download_file(self, file_id: str) -> Tuple[BinaryIO, str]:
                    response = self.client.get_object(self.bucket, file_id)
                    return response, file_id.split('/')[-1]

                def delete_file(self, file_id: str) -> bool:
                    self.client.remove_object(self.bucket, file_id)
                    return True

                def list_files(self, prefix: str = "") -> List[dict]:
                    files = []
                    for obj in self.client.list_objects(self.bucket, prefix=prefix, recursive=True):
                        files.append({
                            'file_id': obj.object_name,
                            'name': obj.object_name.split('/')[-1],
                            'size': obj.size,
                            'created_at': obj.last_modified.isoformat(),
                            'modified_at': obj.last_modified.isoformat()
                        })
                    return files

                def get_file_info(self, file_id: str) -> Optional[dict]:
                    try:
                        stat = self.client.stat_object(self.bucket, file_id)
                        return {
                            'file_id': file_id,
                            'name': file_id.split('/')[-1],
                            'size': stat.size,
                            'created_at': stat.last_modified.isoformat(),
                            'modified_at': stat.last_modified.isoformat()
                        }
                    except S3Error:
                        return None

                def exists(self, file_id: str) -> bool:
                    try:
                        self.client.stat_object(self.bucket, file_id)
                        return True
                    except S3Error:
                        return False
            
            return MinIOStorageBackend(self.settings)
        except ImportError:
            raise StorageError("MinIO SDK 未安装，请安装 minio")

    def _create_s3_backend(self) -> BaseStorageBackend:
        """创建 S3 后端（占位）"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            class S3StorageBackend(BaseStorageBackend):
                def __init__(self, settings):
                    self.client = boto3.client(
                        's3',
                        aws_access_key_id=settings.s3_access_key_id,
                        aws_secret_access_key=settings.s3_secret_access_key,
                        region_name=settings.s3_region,
                        endpoint_url=settings.s3_endpoint_url
                    )
                    self.bucket = settings.s3_bucket

                def upload_file(self, file: BinaryIO, filename: str, destination: str = "") -> str:
                    object_name = f"{destination}/{filename}" if destination else filename
                    self.client.upload_fileobj(file, self.bucket, object_name)
                    return object_name

                def download_file(self, file_id: str) -> Tuple[BinaryIO, str]:
                    from io import BytesIO
                    buffer = BytesIO()
                    self.client.download_fileobj(self.bucket, file_id, buffer)
                    buffer.seek(0)
                    return buffer, file_id.split('/')[-1]

                def delete_file(self, file_id: str) -> bool:
                    self.client.delete_object(Bucket=self.bucket, Key=file_id)
                    return True

                def list_files(self, prefix: str = "") -> List[dict]:
                    files = []
                    response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
                    if 'Contents' in response:
                        for obj in response['Contents']:
                            files.append({
                                'file_id': obj['Key'],
                                'name': obj['Key'].split('/')[-1],
                                'size': obj['Size'],
                                'created_at': obj['LastModified'].isoformat(),
                                'modified_at': obj['LastModified'].isoformat()
                            })
                    return files

                def get_file_info(self, file_id: str) -> Optional[dict]:
                    try:
                        response = self.client.head_object(Bucket=self.bucket, Key=file_id)
                        return {
                            'file_id': file_id,
                            'name': file_id.split('/')[-1],
                            'size': response['ContentLength'],
                            'created_at': response['LastModified'].isoformat(),
                            'modified_at': response['LastModified'].isoformat()
                        }
                    except ClientError:
                        return None

                def exists(self, file_id: str) -> bool:
                    try:
                        self.client.head_object(Bucket=self.bucket, Key=file_id)
                        return True
                    except ClientError:
                        return False
            
            return S3StorageBackend(self.settings)
        except ImportError:
            raise StorageError("boto3 未安装，请安装 boto3")

    def upload_file(self, file: BinaryIO, filename: str, destination: str = "") -> str:
        """上传文件"""
        return self.backend.upload_file(file, filename, destination)

    def download_file(self, file_id: str) -> Tuple[BinaryIO, str]:
        """下载文件"""
        return self.backend.download_file(file_id)

    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        return self.backend.delete_file(file_id)

    def list_files(self, prefix: str = "") -> List[dict]:
        """列出文件"""
        return self.backend.list_files(prefix)

    def get_file_info(self, file_id: str) -> Optional[dict]:
        """获取文件信息"""
        return self.backend.get_file_info(file_id)

    def exists(self, file_id: str) -> bool:
        """检查文件是否存在"""
        return self.backend.exists(file_id)

    def get_storage_usage(self) -> dict:
        """获取存储使用情况"""
        if self.settings.backend == StorageBackend.LOCAL:
            total = sum(f.stat().st_size for f in self.settings.local_path.rglob('*') if f.is_file())
            return {
                'used_bytes': total,
                'used_gb': round(total / (1024 ** 3), 2),
                'quota_gb': self.settings.quota_gb if self.settings.quota_enabled else None,
                'files_count': len(list(self.settings.local_path.rglob('*')))
            }
        return {}

    def get_tier_features(self) -> List[str]:
        """获取当前存储级别的特性列表"""
        return self.settings.features_summary

    def get_tier_score(self) -> float:
        """获取存储级别评分"""
        return self.settings.storage_capacity_score


def get_storage_service() -> StorageService:
    """获取存储服务单例"""
    return StorageService()
