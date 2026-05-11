"""HydraFlow AI 配置管理器 - 使用 pydantic-settings"""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

from src.core.exceptions import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class StorageType(str, Enum):
    LOCAL = "local"
    MINIO = "minio"
    S3 = "s3"


class DatabaseSettings(BaseSettings):
    url: str = Field(default="sqlite+aiosqlite:///./data/hydraflow.db", description="数据库连接 URL")
    pool_size: int = Field(default=20, ge=1, description="连接池大小")
    max_overflow: int = Field(default=10, ge=0, description="最大溢出连接数")
    echo: bool = Field(default=False, description="是否打印 SQL")

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


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
    type: StorageType = Field(default=StorageType.LOCAL, description="存储类型")
    local_path: Path = Field(default=Path("./data/storage"), description="本地存储路径")
    minio_endpoint: Optional[str] = Field(default=None, description="MinIO 端点")
    minio_access_key: Optional[str] = Field(default=None, description="MinIO 访问密钥")
    minio_secret_key: Optional[str] = Field(default=None, description="MinIO 秘密密钥")
    minio_bucket: str = Field(default="hydraflow", description="MinIO 桶名")
    minio_secure: bool = Field(default=False, description="MinIO 是否使用 HTTPS")
    s3_access_key_id: Optional[str] = Field(default=None, description="S3 访问密钥 ID")
    s3_secret_access_key: Optional[str] = Field(default=None, description="S3 秘密访问密钥")
    s3_region: str = Field(default="us-east-1", description="S3 区域")
    s3_bucket: str = Field(default="hydraflow", description="S3 桶名")

    model_config = SettingsConfigDict(env_prefix="")

    @field_validator("local_path")
    @classmethod
    def validate_local_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v


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
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v.strip() for v in v.split(",")]
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
    workers: int = Field(default=4, ge=1, description="工作进程数")
    reload: bool = Field(default=True, description="是否启用热重载")
    docs_enabled: bool = Field(default=True, description="是否启用 API 文档")

    model_config = SettingsConfigDict(env_prefix="API_")


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

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_staging(self) -> bool:
        return self.environment == Environment.STAGING


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
    """获取全局配置单例"""
    return Settings()


def get_legacy_config() -> LegacyConfigManager:
    """获取兼容旧配置的管理器（用于迁移）"""
    return LegacyConfigManager()


get_config = get_legacy_config
