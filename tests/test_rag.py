"""RAG 知识库与本地推理服务探测端点测试"""

UNIQUE_DOC = "九头蛇工作流平台的检索增强测试文档"


def test_add_documents_and_count(client):
    response = client.post(
        "/api/v1/rag/documents",
        json={"documents": ["赛博朋克是一种科幻视觉风格", UNIQUE_DOC]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["added"] == 2
    assert body["total"] >= 2

    count = client.get("/api/v1/rag/documents/count")
    assert count.status_code == 200
    assert count.json()["count"] >= 2


def test_query_returns_sources(client):
    client.post("/api/v1/rag/documents", json={"documents": [UNIQUE_DOC]})
    response = client.post(
        "/api/v1/rag/query", json={"question": "检索增强测试文档", "top_k": 3}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "检索增强测试文档"
    assert body["total_results"] >= 1
    assert body["sources"]


def test_query_top_k_is_validated(client):
    response = client.post(
        "/api/v1/rag/query", json={"question": "测试", "top_k": 999}
    )
    assert response.status_code == 422


def test_delete_document(client):
    add = client.post("/api/v1/rag/documents", json={"documents": ["待删除文档"]})
    assert add.status_code == 200

    query = client.post("/api/v1/rag/query", json={"question": "待删除文档", "top_k": 1})
    doc_id = query.json()["sources"][0]["id"]

    delete = client.delete(f"/api/v1/rag/documents/{doc_id}")
    assert delete.status_code == 200

    missing = client.delete("/api/v1/rag/documents/__not_exist__")
    assert missing.status_code == 404


def test_providers_probe_endpoint(client):
    response = client.get("/api/v1/system/providers")
    assert response.status_code == 200
    providers = response.json()["providers"]
    names = {p["name"] for p in providers}
    assert names == {"lm_studio", "ollama"}
    for provider in providers:
        assert isinstance(provider["available"], bool)
