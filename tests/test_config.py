"""配置模块测试"""

from src.core.config import get_config, get_settings


def test_legacy_config_loads_json_files():
    config = get_config()
    assert config.global_config, "global_config.json 未加载"
    assert config.models_config, "models.json 未加载"


def test_legacy_config_returns_default_for_missing_key():
    config = get_config()
    assert config.get("a.b.c", "fallback") == "fallback"


def test_legacy_config_project_root_exists():
    config = get_config()
    assert config.project_root.exists()


def test_settings_defaults():
    settings = get_settings()
    assert settings.api.port == 8000
    assert settings.environment is not None


def test_settings_is_cached_singleton():
    assert get_settings() is get_settings()
