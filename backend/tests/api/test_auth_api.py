"""
文件名: tests/api/test_auth_api.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试认证路由
"""
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.auth import TokenResponse, UserInfo


def test_login_success():
    with patch("app.api.auth.AuthService") as MockSvc:
        instance = MockSvc.return_value
        instance.login = AsyncMock(return_value=TokenResponse(
            access_token="at", refresh_token="rt", expires_in=3600,
            user=UserInfo(user_id="u1", username="admin", role="hr", email="a@b.com")
        ))
        client = TestClient(app)
        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "123"})
        body = r.json()
        assert r.status_code == 200
        assert body["code"] == 0
        assert body["data"]["access_token"] == "at"


def test_protected_without_token():
    """AC1.3: 未带 Token 访问受保护接口返回 1002"""
    client = TestClient(app)
    r = client.get("/api/v1/auth/me")
    body = r.json()
    assert body["code"] == 1002


def test_logout():
    with patch("app.api.auth.AuthService") as MockSvc:
        instance = MockSvc.return_value
        instance.logout = AsyncMock()
        client = TestClient(app)
        client.headers.update({"Authorization": "Bearer fake"})
        with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"})):
            r = client.post("/api/v1/auth/logout")
            body = r.json()
            assert body["code"] == 0
