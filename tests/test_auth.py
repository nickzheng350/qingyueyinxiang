"""认证模块测试（AuthManager 为单例，由 fixture 在每个用例前重置）"""


def test_create_user_and_authenticate(auth_manager):
    user = auth_manager.create_user("alice", "secret123", email="alice@example.com")
    assert user is not None
    assert user.username == "alice"
    token = auth_manager.authenticate("alice", "secret123")
    assert token
    assert auth_manager.verify_token(token) == "alice"


def test_duplicate_username_rejected(auth_manager):
    assert auth_manager.create_user("alice", "p") is not None
    assert auth_manager.create_user("alice", "p") is None


def test_wrong_password_rejected(auth_manager):
    auth_manager.create_user("bob", "correct")
    assert auth_manager.authenticate("bob", "wrong") is None


def test_authenticate_unknown_user_returns_none(auth_manager):
    assert auth_manager.authenticate("ghost", "p") is None


def test_verify_invalid_token_returns_none(auth_manager):
    assert auth_manager.verify_token("not-a-jwt") is None


def test_logout_revokes_token(auth_manager):
    auth_manager.create_user("carol", "p")
    token = auth_manager.authenticate("carol", "p")
    assert auth_manager.logout(token) is True
    assert auth_manager.verify_token(token) is None


def test_logout_invalid_token_returns_false(auth_manager):
    assert auth_manager.logout("not-a-jwt") is False


def test_update_user_role(auth_manager):
    auth_manager.create_user("dave", "p")
    assert auth_manager.update_user("dave", role="admin") is True
    assert auth_manager.get_user("dave").role == "admin"


def test_update_user_enabled_flag(auth_manager):
    auth_manager.create_user("erin", "p")
    assert auth_manager.update_user("erin", enabled=False) is True
    assert auth_manager.get_user("erin").enabled is False
    assert auth_manager.authenticate("erin", "p") is None


def test_update_missing_user_returns_false(auth_manager):
    assert auth_manager.update_user("ghost", role="admin") is False


def test_delete_user(auth_manager):
    auth_manager.create_user("frank", "p")
    assert auth_manager.delete_user("frank") is True
    assert auth_manager.get_user("frank") is None


def test_delete_missing_user_returns_false(auth_manager):
    assert auth_manager.delete_user("ghost") is False


def test_list_users(auth_manager):
    auth_manager.create_user("u1", "p")
    auth_manager.create_user("u2", "p")
    usernames = {u.username for u in auth_manager.list_users()}
    assert {"u1", "u2"} == usernames
