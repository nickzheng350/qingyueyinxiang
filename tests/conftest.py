"""pytest 共享 fixtures。

将项目根目录加入 sys.path，保证 `import src.*` 在任何调用方式下都可用。
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def client():
    """FastAPI 测试客户端，完整走 HTTP 栈（含中间件与异常处理器）"""
    from fastapi.testclient import TestClient

    from src.api.app import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def parser_factory():
    from src.intent_parser.factory import IntentParserFactory

    return IntentParserFactory()


@pytest.fixture
def prompt_engine():
    from src.prompt_engine.engine import PromptEngine

    return PromptEngine()


@pytest.fixture
def dispatcher():
    from src.model_dispatcher.dispatcher import ModelDispatcher

    return ModelDispatcher()


@pytest.fixture
def cache_manager():
    """缓存管理器为单例，每个用例前清空，避免互相污染"""
    from src.cache import get_cache_manager

    manager = get_cache_manager()
    manager.clear_all()
    return manager


@pytest.fixture
def auth_manager():
    """AuthManager 为单例，每个用例前重置用户与吊销令牌"""
    from src.auth import get_auth_manager

    manager = get_auth_manager()
    manager._users.clear()
    manager._revoked_tokens.clear()
    return manager
