"""HydraFlow AI 配置管理器 - 使用 pydantic-settings"""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Optional, get_type_hints
from functools import lru_cache

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    load_dotenv = lambda: None

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # 创建简化的模拟类
    class Field:
        def __init__(self, default=None, **kwargs):
            self.default = default
            self.kwargs = kwargs
    
    def field_validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class SettingsConfigDict(dict):
        pass
    
    class BaseSettings:
        model_config = SettingsConfigDict(env_file='.env')
        
        def __init__(self, **kwargs):
            hints = get_type_hints(self.__class__)
            for name, hint_type in hints.items():
                if hasattr(self, name):
                    continue
                # 从环境变量获取值
                env_value = os.environ.get(f"{self.__class__.__name__}_{name}".upper())
                if env_value is not None:
                    # 尝试转换类型
                    try:
                        if hint_type == int:
                            setattr(self, name, int(env_value))
                        elif hint_type == float:
                            setattr(self, name, float(env_value))
                        elif hint_type == bool:
                            setattr(self, name, env_value.lower() == 'true')
                        else:
                            setattr(self, name, env_value)
                    except:
                        setattr(self, name, env_value)

from src.core.exceptions import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class StorageBackend(str, Enum):
    """存储后端类型"""
    LOCAL = "local"
    MINIO = "minio"
    S3 = "s3"
    NAS = "nas"
    SAN = "san"
    CLOUD = "cloud"


class StorageTier(str, Enum):
    """存储智能级别"""
    BASIC = "basic"           # 基础存储：本地文件系统
    STANDARD = "standard"     # 标准存储：带缓存和压缩
    ADVANCED = "advanced"     # 高级存储：带版本控制和备份
    ENTERPRISE = "enterprise" # 企业级存储：分布式、高可用、灾备
    CLOUD_NATIVE = "cloud_native" # 云原生存储：对象存储+CDN


class DatabaseTier(str, Enum):
    """数据库级别"""
    DEVELOPMENT = "development"       # 开发环境：SQLite
    STANDARD = "standard"             # 标准：PostgreSQL单节点
    HIGH_AVAILABILITY = "high_availability" # 高可用：主从复制
    CLUSTER = "cluster"               # 集群：分布式数据库
    ENTERPRISE = "enterprise"         # 企业级：多数据中心、自动故障转移


class DatabaseSettings(BaseSettings):
    tier: DatabaseTier = Field(default=DatabaseTier.DEVELOPMENT, description="数据库级别")
    url: str = Field(default="sqlite+aiosqlite:///./data/hydraflow.db", description="数据库连接 URL")
    pool_size: int = Field(default=20, ge=1, description="连接池大小")
    max_overflow: int = Field(default=10, ge=0, description="最大溢出连接数")
    echo: bool = Field(default=False, description="是否打印 SQL")
    
    # SQLite 配置
    sqlite_path: str = Field(default="./data/hydraflow.db", description="SQLite 数据库文件路径")
    
    # PostgreSQL 配置
    postgresql_host: str = Field(default="localhost", description="PostgreSQL 主机")
    postgresql_port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL 端口")
    postgresql_db: str = Field(default="hydraflow", description="PostgreSQL 数据库名")
    postgresql_user: str = Field(default="postgres", description="PostgreSQL 用户名")
    postgresql_password: str = Field(default="postgres", description="PostgreSQL 密码")
    
    # 企业级特性
    read_replica_urls: list[str] = Field(default=[], description="只读副本连接URL列表")
    connection_timeout: int = Field(default=30, ge=1, description="连接超时时间（秒）")
    statement_timeout: int = Field(default=300, ge=10, description="语句超时时间（秒）")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    retry_delay: int = Field(default=5, ge=1, description="重试延迟（秒）")
    
    # 连接池配置
    pool_timeout: int = Field(default=30, ge=1, description="连接池超时时间（秒）")
    pool_recycle: int = Field(default=3600, ge=60, description="连接回收时间（秒）")
    
    # 读写分离
    read_write_split: bool = Field(default=False, description="是否启用读写分离")
    read_only_mode: bool = Field(default=False, description="只读模式")
    
    # 分布式配置
    sharding_enabled: bool = Field(default=False, description="是否启用分片")
    shard_count: int = Field(default=1, ge=1, description="分片数量")
    
    # 备份配置
    backup_enabled: bool = Field(default=True, description="是否启用备份")
    backup_interval_hours: int = Field(default=24, ge=1, description="备份间隔（小时）")
    backup_retention_days: int = Field(default=7, ge=1, description="备份保留天数")
    
    # 监控配置
    metrics_enabled: bool = Field(default=True, description="是否启用指标收集")
    slow_query_threshold_ms: int = Field(default=1000, ge=100, description="慢查询阈值（毫秒）")

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    @property
    def recommended_pool_size(self) -> int:
        """根据数据库级别推荐连接池大小"""
        pool_sizes = {
            DatabaseTier.DEVELOPMENT: 5,
            DatabaseTier.STANDARD: 20,
            DatabaseTier.HIGH_AVAILABILITY: 50,
            DatabaseTier.CLUSTER: 100,
            DatabaseTier.ENTERPRISE: 200
        }
        return pool_sizes.get(self.tier, 20)
    
    @property
    def database_capacity_score(self) -> float:
        """数据库容量评分"""
        scores = {
            DatabaseTier.DEVELOPMENT: 10,
            DatabaseTier.STANDARD: 30,
            DatabaseTier.HIGH_AVAILABILITY: 50,
            DatabaseTier.CLUSTER: 80,
            DatabaseTier.ENTERPRISE: 100
        }
        return scores.get(self.tier, 30)


class RedisSettings(BaseSettings):
    url: str = Field(default="redis://localhost:6379/0", description="Redis 连接 URL")
    pool_size: int = Field(default=10, ge=1, description="连接池大小")
    max_connections: int = Field(default=50, ge=1, description="最大连接数")

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class CelerySettings(BaseSettings):
    broker_url: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    result_backend: str = Field(default="redis://localhost:6379/2", description="Celery result backend URL")
    task_serializer: str = Field(default="json", description="任务序列化方式")
    result_serializer: str = Field(default="json", description="结果序列化方式")
    accept_content: list[str] = Field(default=["json"], description="接受的内容类型")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    task_track_started: bool = Field(default=True, description="是否跟踪任务开始")
    task_time_limit: int = Field(default=3600, ge=60, description="任务硬超时（秒）")
    task_soft_time_limit: int = Field(default=3000, ge=60, description="任务软超时（秒）")

    model_config = SettingsConfigDict(env_prefix="CELERY_")


class StorageSettings(BaseSettings):
    tier: StorageTier = Field(default=StorageTier.BASIC, description="存储智能级别")
    backend: StorageBackend = Field(default=StorageBackend.LOCAL, description="存储后端类型")
    
    # 本地存储配置
    local_path: Path = Field(default=Path("./data/storage"), description="本地存储路径")
    local_backup_path: Path = Field(default=Path("./data/storage_backup"), description="本地备份路径")
    
    # MinIO 配置
    minio_endpoint: Optional[str] = Field(default=None, description="MinIO 端点")
    minio_access_key: Optional[str] = Field(default=None, description="MinIO 访问密钥")
    minio_secret_key: Optional[str] = Field(default=None, description="MinIO 秘密密钥")
    minio_bucket: str = Field(default="hydraflow", description="MinIO 桶名")
    minio_secure: bool = Field(default=False, description="MinIO 是否使用 HTTPS")
    minio_region: str = Field(default="us-east-1", description="MinIO 区域")
    
    # S3 配置
    s3_access_key_id: Optional[str] = Field(default=None, description="S3 访问密钥 ID")
    s3_secret_access_key: Optional[str] = Field(default=None, description="S3 秘密访问密钥")
    s3_region: str = Field(default="us-east-1", description="S3 区域")
    s3_bucket: str = Field(default="hydraflow", description="S3 桶名")
    s3_endpoint_url: Optional[str] = Field(default=None, description="S3 自定义端点")
    s3_signature_version: str = Field(default="s3v4", description="S3 签名版本")
    
    # NAS/SAN 配置
    nas_path: Optional[str] = Field(default=None, description="NAS 挂载路径")
    san_lun: Optional[str] = Field(default=None, description="SAN LUN 路径")
    
    # 智能存储特性
    cache_enabled: bool = Field(default=True, description="是否启用缓存")
    cache_size_gb: int = Field(default=10, ge=1, description="缓存大小(GB)")
    cache_ttl_hours: int = Field(default=24, ge=1, description="缓存过期时间(小时)")
    
    compression_enabled: bool = Field(default=True, description="是否启用压缩")
    compression_algorithm: str = Field(default="zstd", description="压缩算法")
    compression_level: int = Field(default=3, ge=1, le=9, description="压缩级别")
    
    encryption_enabled: bool = Field(default=True, description="是否启用加密")
    encryption_key: Optional[str] = Field(default=None, description="加密密钥")
    encryption_algorithm: str = Field(default="AES-256", description="加密算法")
    
    # 版本控制
    versioning_enabled: bool = Field(default=False, description="是否启用版本控制")
    version_retention_days: int = Field(default=30, ge=1, description="版本保留天数")
    
    # 备份配置
    backup_enabled: bool = Field(default=True, description="是否启用自动备份")
    backup_interval_hours: int = Field(default=24, ge=1, description="备份间隔(小时)")
    backup_retention_days: int = Field(default=7, ge=1, description="备份保留天数")
    backup_to_cloud: bool = Field(default=False, description="是否备份到云")
    
    # 访问控制
    access_control_enabled: bool = Field(default=True, description="是否启用访问控制")
    public_read: bool = Field(default=False, description="是否允许公共读取")
    
    # CDN 配置
    cdn_enabled: bool = Field(default=False, description="是否启用 CDN")
    cdn_url: Optional[str] = Field(default=None, description="CDN 基础 URL")
    cdn_cache_ttl_hours: int = Field(default=72, ge=1, description="CDN 缓存时间(小时)")
    
    # 文件限制
    max_file_size_mb: int = Field(default=500, ge=1, description="最大文件大小(MB)")
    allowed_extensions: list[str] = Field(default=[], description="允许的文件扩展名列表")
    denied_extensions: list[str] = Field(default=[".exe", ".dll", ".js"], description="禁止的文件扩展名列表")
    
    # 性能优化
    multipart_upload_threshold_mb: int = Field(default=10, ge=1, description="分片上传阈值(MB)")
    multipart_chunk_size_mb: int = Field(default=5, ge=1, description="分片大小(MB)")
    concurrent_uploads: int = Field(default=5, ge=1, description="并发上传数")
    
    # 存储配额
    quota_enabled: bool = Field(default=False, description="是否启用存储配额")
    quota_gb: int = Field(default=1000, ge=1, description="存储配额(GB)")
    
    # 监控指标
    metrics_enabled: bool = Field(default=True, description="是否启用指标收集")
    log_access: bool = Field(default=True, description="是否记录访问日志")

    model_config = SettingsConfigDict(env_prefix="STORAGE_")

    @field_validator("local_path")
    @classmethod
    def validate_local_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

    @field_validator("local_backup_path")
    @classmethod
    def validate_backup_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

    @property
    def storage_capacity_score(self) -> float:
        """存储容量评分"""
        scores = {
            StorageTier.BASIC: 10,
            StorageTier.STANDARD: 30,
            StorageTier.ADVANCED: 50,
            StorageTier.ENTERPRISE: 80,
            StorageTier.CLOUD_NATIVE: 100
        }
        return scores.get(self.tier, 30)

    @property
    def features_summary(self) -> list[str]:
        """存储特性摘要"""
        features = []
        if self.cache_enabled:
            features.append("缓存")
        if self.compression_enabled:
            features.append("压缩")
        if self.encryption_enabled:
            features.append("加密")
        if self.versioning_enabled:
            features.append("版本控制")
        if self.backup_enabled:
            features.append("自动备份")
        if self.cdn_enabled:
            features.append("CDN加速")
        if self.access_control_enabled:
            features.append("访问控制")
        return features


class AuthSettings(BaseSettings):
    jwt_secret_key: str = Field(
        default="your-super-secret-key-here-change-in-production",
        description="JWT 密钥"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT 算法")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=5, description="访问令牌过期时间（分钟）")
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, description="刷新令牌过期时间（天）")
    oauth_google_client_id: Optional[str] = Field(default=None, description="Google OAuth 客户端 ID")
    oauth_google_client_secret: Optional[str] = Field(default=None, description="Google OAuth 客户端密钥")
    oauth_github_client_id: Optional[str] = Field(default=None, description="GitHub OAuth 客户端 ID")
    oauth_github_client_secret: Optional[str] = Field(default=None, description="GitHub OAuth 客户端密钥")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS 允许的源"
    )

    model_config = SettingsConfigDict(env_prefix="")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v):
        if isinstance(v, str) and v:
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return [item.strip() for item in v.split(",") if item.strip()]
        return v


class RateLimitSettings(BaseSettings):
    enabled: bool = Field(default=True, description="是否启用限流")
    default_limit: str = Field(default="100/minute", description="默认限流")
    authenticated_limit: str = Field(default="1000/minute", description="认证用户限流")

    model_config = SettingsConfigDict(env_prefix="RATE_LIMIT_")


class CacheSettings(BaseSettings):
    ttl: int = Field(default=3600, ge=60, description="默认缓存 TTL（秒）")
    max_size: int = Field(default=10000, ge=100, description="缓存最大大小")
    default_namespace: str = Field(default="hydraflow", description="默认命名空间")

    model_config = SettingsConfigDict(env_prefix="CACHE_")


class TaskSettings(BaseSettings):
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    retry_delay: int = Field(default=5, ge=1, description="重试延迟（秒）")
    timeout: int = Field(default=3600, ge=60, description="任务超时（秒）")
    concurrency: int = Field(default=10, ge=1, description="并发数")

    model_config = SettingsConfigDict(env_prefix="TASK_")


class MonitoringSettings(BaseSettings):
    log_level: str = Field(default="INFO", description="日志级别")
    log_dir: Path = Field(default=Path("./logs"), description="日志目录")
    log_format: str = Field(default="json", description="日志格式 (json/text)")
    prometheus_enabled: bool = Field(default=True, description="是否启用 Prometheus")
    prometheus_port: int = Field(default=9090, ge=1024, le=65535, description="Prometheus 端口")

    model_config = SettingsConfigDict(env_prefix="")

    @field_validator("log_dir")
    @classmethod
    def validate_log_dir(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v


class APISettings(BaseSettings):
    host: str = Field(default="0.0.0.0", description="API 主机")
    port: int = Field(default=8000, ge=1, le=65535, description="API 端口")
    workers: int = Field(default=4, ge=1, le=128, description="工作进程数")
    reload: bool = Field(default=True, description="是否启用热重载")
    docs_enabled: bool = Field(default=True, description="是否启用 API 文档")
    proxy_headers: bool = Field(default=True, description="是否信任代理头部")
    forwarded_allow_ips: str = Field(default="*", description="允许的转发IP")
    timeout_keep_alive: int = Field(default=5, ge=1, le=60, description="保持连接超时（秒）")
    timeout_request: int = Field(default=60, ge=1, le=3600, description="请求超时（秒）")

    model_config = SettingsConfigDict(env_prefix="API_")


class HardwareTier(str, Enum):
    """硬件层级"""
    DEVELOPMENT = "development"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"
    CLUSTER = "cluster"
    SUPER_CLUSTER = "super_cluster"


class NetworkType(str, Enum):
    """网络类型"""
    LOCAL = "local"
    VPC = "vpc"
    DEDICATED = "dedicated"
    HYBRID = "hybrid"


class StorageType(str, Enum):
    """存储类型"""
    HDD = "hdd"
    SSD = "ssd"
    NVME = "nvme"
    SAN = "san"
    NAS = "nas"
    CLOUD = "cloud"


class HardwareSettings(BaseSettings):
    """企业级硬件配置"""
    tier: HardwareTier = Field(default=HardwareTier.DEVELOPMENT, description="硬件层级")
    
    # CPU 配置
    cpu_cores: int = Field(default=4, ge=1, le=4096, description="CPU核心数")
    cpu_threads: int = Field(default=8, ge=1, le=8192, description="CPU线程数")
    cpu_base_freq: float = Field(default=2.0, ge=1.0, le=5.0, description="CPU基础频率(GHz)")
    cpu_max_freq: float = Field(default=3.5, ge=1.0, le=6.0, description="CPU最大频率(GHz)")
    cpu_model: str = Field(default="Intel Xeon", description="CPU型号")
    cpu_socket: int = Field(default=1, ge=1, le=8, description="CPU插槽数")
    cpu_tdp: int = Field(default=100, ge=10, le=500, description="CPU功耗(W)")
    
    # 内存配置
    memory_gb: int = Field(default=16, ge=4, le=16384, description="内存容量(GB)")
    memory_type: str = Field(default="DDR4", description="内存类型")
    memory_speed: int = Field(default=3200, description="内存速度(MHz)")
    memory_channels: int = Field(default=2, ge=1, le=8, description="内存通道数")
    memory_ecc: bool = Field(default=False, description="是否启用ECC")
    
    # GPU 配置
    gpu_enabled: bool = Field(default=False, description="是否启用GPU")
    gpu_count: int = Field(default=0, ge=0, le=32, description="GPU数量")
    gpu_model: str = Field(default="", description="GPU型号")
    gpu_vram_gb: int = Field(default=0, ge=0, le=1024, description="单卡VRAM(GB)")
    gpu_total_vram_gb: int = Field(default=0, ge=0, le=32768, description="总VRAM(GB)")
    gpu_memory_bus_bit: int = Field(default=0, ge=0, le=1024, description="GPU显存位宽(bits)")
    gpu_cuda_cores: int = Field(default=0, ge=0, le=100000, description="CUDA核心数")
    gpu_tensor_cores: int = Field(default=0, ge=0, le=10000, description="Tensor核心数")
    gpu_tdp: int = Field(default=0, ge=0, le=1500, description="GPU功耗(W)")
    
    # 存储配置
    storage_type: str = Field(default="NVME", description="存储类型")
    storage_total_gb: int = Field(default=256, ge=64, le=1048576, description="存储容量(GB)")
    storage_iops: int = Field(default=1000, ge=100, le=1000000, description="IOPS")
    storage_throughput_mbps: int = Field(default=1000, ge=100, le=100000, description="吞吐量(MB/s)")
    storage_redundancy: str = Field(default="RAID0", description="存储冗余类型")
    storage_cache_gb: int = Field(default=0, ge=0, le=1024, description="缓存容量(GB)")
    
    # 网络配置
    network_bandwidth_gbps: float = Field(default=1, ge=0.1, le=100, description="网络带宽(Gbps)")
    network_latency_ms: int = Field(default=1, ge=0, le=100, description="网络延迟(ms)")
    network_type: str = Field(default="LOCAL", description="网络类型")
    network_interface_count: int = Field(default=1, ge=1, le=32, description="网卡数量")
    network_failover: bool = Field(default=False, description="是否启用网络故障转移")
    
    # 企业级特性
    high_availability: bool = Field(default=False, description="是否启用高可用")
    load_balancing: bool = Field(default=False, description="是否启用负载均衡")
    auto_scaling: bool = Field(default=False, description="是否启用自动扩缩容")
    backup_enabled: bool = Field(default=True, description="是否启用备份")
    monitoring_enabled: bool = Field(default=True, description="是否启用监控")
    disaster_recovery: bool = Field(default=False, description="是否启用灾难恢复")
    encryption_at_rest: bool = Field(default=True, description="是否启用静态数据加密")
    encryption_in_transit: bool = Field(default=True, description="是否启用传输加密")
    
    # 集群配置
    cluster_nodes: int = Field(default=1, ge=1, le=1000, description="集群节点数")
    cluster_type: str = Field(default="single", description="集群类型")
    distributed_storage: bool = Field(default=False, description="是否启用分布式存储")
    distributed_computing: bool = Field(default=False, description="是否启用分布式计算")
    
    # 性能指标
    max_concurrent_requests: int = Field(default=100, ge=10, le=100000, description="最大并发请求数")
    response_time_ms: int = Field(default=100, ge=1, le=10000, description="目标响应时间(ms)")
    uptime_sla: float = Field(default=99.9, ge=99.0, le=99.9999, description="SLA可用性(%)")

    model_config = SettingsConfigDict(env_prefix="HARDWARE_")

    @field_validator("gpu_total_vram_gb", mode="before")
    @classmethod
    def calculate_total_vram(cls, v, values):
        if v is None or v == 0:
            return values.data.get("gpu_count", 0) * values.data.get("gpu_vram_gb", 0)
        return v

    @property
    def hardware_score(self) -> float:
        """计算硬件综合评分"""
        score = 0
        
        # CPU评分 (30分)
        cpu_score = min(self.cpu_cores * 0.5 + self.cpu_threads * 0.2, 30)
        score += cpu_score
        
        # 内存评分 (25分)
        memory_score = min(self.memory_gb * 0.5, 25)
        score += memory_score
        
        # GPU评分 (25分)
        if self.gpu_enabled and self.gpu_count > 0:
            gpu_score = min(self.gpu_count * self.gpu_vram_gb * 1.5, 25)
            score += gpu_score
        
        # 存储评分 (10分)
        storage_score = min(self.storage_iops / 10000, 10)
        score += storage_score
        
        # 网络评分 (10分)
        network_score = min(self.network_bandwidth_gbps * 2, 10)
        score += network_score
        
        return round(score, 2)

    @property
    def recommended_models(self) -> list[str]:
        """根据硬件配置推荐模型"""
        models = []
        
        if self.gpu_enabled and self.gpu_total_vram_gb >= 80:
            models.extend(["gpt-4o", "claude-3-opus", "gemini-ultra"])
        elif self.gpu_enabled and self.gpu_total_vram_gb >= 40:
            models.extend(["gpt-4", "claude-3-sonnet", "gemini-pro"])
        elif self.gpu_enabled and self.gpu_total_vram_gb >= 24:
            models.extend(["llama3-70b", "qwen2-72b", "mistral-large"])
        elif self.gpu_enabled and self.gpu_total_vram_gb >= 16:
            models.extend(["llama3-8b", "qwen2-7b", "mistral-7b"])
        elif self.memory_gb >= 32:
            models.extend(["llama3-8b", "qwen2-7b"])
        else:
            models.extend(["qwen2-1.5b", "phi-3-mini"])
        
        return models

    @property
    def estimated_cost_per_month(self) -> float:
        """估算月度成本(人民币)"""
        cost = 0
        
        # CPU成本估算
        cost += self.cpu_cores * 50
        
        # 内存成本估算
        cost += self.memory_gb * 30
        
        # GPU成本估算
        if self.gpu_enabled:
            cost += self.gpu_count * (self.gpu_vram_gb * 100 + 500)
        
        # 存储成本估算
        cost += self.storage_total_gb * 2
        
        # 网络成本估算
        cost += self.network_bandwidth_gbps * 100
        
        # 企业特性溢价
        if self.high_availability:
            cost *= 1.3
        if self.disaster_recovery:
            cost *= 1.2
        
        return round(cost, 2)


class Settings(BaseSettings):
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="运行环境")
    debug: bool = Field(default=True, description="调试模式")
    project_root: Path = Field(default=PROJECT_ROOT, description="项目根目录")

    api: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    task: TaskSettings = Field(default_factory=TaskSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    hardware: HardwareSettings = Field(default_factory=HardwareSettings)

    default_parser: str = Field(default="qwen2.5", description="默认解析器")
    default_style: str = Field(default="cyberpunk", description="默认风格")
    skill_market_url: str = Field(default="https://hydraflow-ai.org/market", description="技能市场 URL")

    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API 密钥")
    stability_api_key: Optional[str] = Field(default=None, description="Stability API 密钥")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API 密钥")
    huggingface_api_key: Optional[str] = Field(default=None, description="HuggingFace API 密钥")
    replicate_api_key: Optional[str] = Field(default=None, description="Replicate API 密钥")

    lm_studio_api_base: str = Field(default="http://localhost:1234/v1", description="LM Studio API 地址")
    lm_studio_api_key: str = Field(default="lm-studio", description="LM Studio API 密钥")
    lm_studio_model: str = Field(default="qwen2.5-7b", description="LM Studio 模型")
    ollama_api_base: str = Field(default="http://localhost:11434/v1", description="Ollama API 地址")
    ollama_model: str = Field(default="llama3", description="Ollama 模型")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_configs_private()

    def _load_configs_private(self) -> None:
        """加载JSON配置文件（Settings专用）"""
        self._config: dict[str, Any] = {}
        config_dir = PROJECT_ROOT / "config"
        config_files = {
            "global": "global_config.json",
            "models": "models.json",
            "api_keys": "api_keys.json",
            "categories": "categories.json",
            "skill_template": "skill_template.json",
        }
        for key, filename in config_files.items():
            filepath = config_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self._config[key] = json.load(f)
                except (json.JSONDecodeError, OSError):
                    self._config[key] = {}
            else:
                self._config[key] = {}


    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_staging(self) -> bool:
        return self.environment == Environment.STAGING

    @property
    def models_config(self) -> dict:
        return self._config.get("models", {})

    @property
    def api_keys_config(self) -> dict:
        return self._config.get("api_keys", {})

    @property
    def categories_config(self) -> dict:
        return self._config.get("categories", {})

    @property
    def global_config(self) -> dict:
        return self._config.get("global", {})

    @property
    def skill_market_config(self) -> dict:
        return self._config.get("skill_template", {})


class LegacyConfigManager:
    """兼容旧配置文件的配置管理器"""

    _instance: "LegacyConfigManager | None" = None
    _watchers: list = []

    def __new__(cls) -> "LegacyConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._config: dict[str, Any] = {}
        self._env_loaded = False
        self._load_env()
        self._load_configs()

    def _load_env(self) -> None:
        if self._env_loaded:
            return
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        self._env_loaded = True

    def _load_configs(self) -> None:
        config_dir = PROJECT_ROOT / "config"
        config_files = {
            "global": "global_config.json",
            "models": "models.json",
            "api_keys": "api_keys.json",
            "categories": "categories.json",
            "skill_template": "skill_template.json",
        }
        for key, filename in config_files.items():
            filepath = config_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self._config[key] = json.load(f)
                except (json.JSONDecodeError, OSError) as e:
                    raise ConfigError(f"加载配置文件失败: {filename}", details={"error": str(e)})
            else:
                self._config[key] = {}

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        keys = key_path.split(".")
        config = self._config
        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value

    def save(self) -> None:
        config_dir = PROJECT_ROOT / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        for key, data in self._config.items():
            filename_map = {
                "global": "global_config.json",
                "models": "models.json",
                "api_keys": "api_keys.json",
                "categories": "categories.json",
                "skill_template": "skill_template.json",
            }
            if key in filename_map:
                filepath = config_dir / filename_map[key]
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

    def add_watcher(self, callback) -> None:
        self._watchers.append(callback)

    @property
    def global_config(self) -> dict:
        return self._config.get("global", {})

    @property
    def models_config(self) -> dict:
        return self._config.get("models", {})

    @property
    def api_keys_config(self) -> dict:
        return self._config.get("api_keys", {})

    @property
    def categories_config(self) -> dict:
        return self._config.get("categories", {})

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT

    def get_api_key(self, provider: str) -> str | None:
        provider_config = self.api_keys_config.get(provider, {})
        if isinstance(provider_config, dict):
            return provider_config.get("api_key") or os.getenv(f"{provider.upper()}_API_KEY")
        return None

    def is_api_enabled(self, provider: str) -> bool:
        provider_config = self.api_keys_config.get(provider, {})
        if isinstance(provider_config, dict):
            return provider_config.get("enabled", False)
        return False


@lru_cache()
def get_settings() -> Settings:
    """获取全局配置单例（推荐）"""
    return Settings()


def get_legacy_config() -> LegacyConfigManager:
    """获取兼容旧配置的管理器（仅用于迁移，将在 v2.0 移除）"""
    import warnings
    warnings.warn(
        "get_legacy_config() 已弃用，请使用 get_settings()",
        DeprecationWarning,
        stacklevel=2
    )
    return LegacyConfigManager()


def get_config() -> Settings:
    """获取全局配置（统一入口）"""
    return get_settings()
