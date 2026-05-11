"""HydraFlow AI 配置管理器"""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.core.exceptions import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class ConfigManager:
    _instance: "ConfigManager | None" = None
    _watchers: list = []

    def __new__(cls) -> "ConfigManager":
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


_config_instance: ConfigManager | None = None


def get_config() -> ConfigManager:
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
