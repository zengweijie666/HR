"""
文件名: tests/test_integration.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 全量集成测试 - 健康检查 / OpenAPI / 路由覆盖 / 统一响应格式 / 404 兜底
"""
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app


def test_health_check():
    """健康检查端点"""
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_openapi_docs():
    """OpenAPI 文档可访问"""
    client = TestClient(app)
    r = client.get("/docs")
    assert r.status_code == 200


def test_all_routers_mounted():
    """所有 9 个路由模块已挂载"""
    client = TestClient(app)
    r = client.get("/openapi.json")
    paths = r.json()["paths"]
    expected_prefixes = [
        "/api/v1/auth", "/api/v1/resumes", "/api/v1/chat",
        "/api/v1/search", "/api/v1/candidates", "/api/v1/email",
        "/api/v1/jd", "/api/v1/interview", "/api/v1/dashboard",
    ]
    for prefix in expected_prefixes:
        found = any(p.startswith(prefix) for p in paths)
        assert found, f"路由前缀未挂载: {prefix}"


def test_unified_response_format():
    """统一响应格式 {code, message, data, trace_id}"""
    with patch("app.api.dashboard.DashboardService") as MockSvc:
        instance = MockSvc.return_value
        instance.get_stats = AsyncMock(return_value={"total_resumes": 0})
        with patch(
            "app.api.deps.AuthService.verify_token",
            AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"}),
        ):
            client = TestClient(app)
            r = client.get(
                "/api/v1/dashboard/stats",
                headers={"Authorization": "Bearer fake"},
            )
            body = r.json()
            assert "code" in body
            assert "message" in body
            assert "data" in body
            assert "trace_id" in body


def test_404_handler():
    """404 兜底：未注册路径返回 404"""
    client = TestClient(app)
    r = client.get("/api/v1/not-exist")
    assert r.status_code == 404
