"""API 端点测试（走完整 HTTP 栈）"""


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "version" in body


def test_parse_intent_success(client):
    response = client.post(
        "/api/v1/intent/parse", json={"text": "生成一张猫的图片"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "intent" in body
    assert "confidence" in body


def test_parse_intent_requires_text(client):
    response = client.post("/api/v1/intent/parse", json={})
    assert response.status_code == 422


def test_list_models(client):
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["models"], list)
    assert body["total"] == len(body["models"])


def test_list_styles(client):
    response = client.get("/api/v1/styles")
    assert response.status_code == 200


def test_list_parsers(client):
    response = client.get("/api/v1/parsers")
    assert response.status_code == 200


def test_task_statistics(client):
    response = client.get("/api/v1/tasks/statistics")
    assert response.status_code == 200


def test_register_login_me_logout_flow(client):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "username": "api_tester",
            "password": "test_pass_123",
            "email": "api_tester@example.com",
        },
    )
    assert register.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "api_tester", "password": "test_pass_123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "api_tester"

    logout = client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
    )
    assert logout.status_code == 200


def test_login_with_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "api_tester2",
            "password": "right_pass",
            "email": "api_tester2@example.com",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "api_tester2", "password": "wrong_pass"},
    )
    assert response.status_code == 401


def test_access_protected_endpoint_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_unknown_route_returns_404(client):
    assert client.get("/api/v1/__not_exist__").status_code == 404


def test_model_stats_endpoint(client):
    """回归：该端点曾调用不存在的方法，且被 /models/{model_id} 吞掉"""
    response = client.get("/api/v1/models/stats")
    assert response.status_code == 200
    body = response.json()
    assert "stats" in body
    assert body["total"] > 0


def test_model_stats_with_unknown_model(client):
    assert client.get("/api/v1/models/stats?model_id=__nope__").status_code == 404


def test_no_duplicate_route_registrations(client):
    """同一个 (方法, 路径) 只能注册一次"""
    seen: dict[tuple[str, str], int] = {}
    for route in client.app.routes:
        methods = getattr(route, "methods", None)
        if not methods:
            continue
        for method in methods:
            key = (method, route.path)
            seen[key] = seen.get(key, 0) + 1

    duplicates = {key: count for key, count in seen.items() if count > 1}
    assert not duplicates, f"存在重复注册的路由: {duplicates}"
