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


def test_register_api_success():
    """注册接口成功返回 pending"""
    with patch("app.api.auth.AuthService") as MockSvc:
        instance = MockSvc.return_value
        instance.register = AsyncMock(return_value={"user_id": "u_x", "username": "zhangsan", "status": "pending"})
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/auth/register", json={"username": "zhangsan", "password": "Pass1234", "email": "z@t.com", "name": "张三"})
        body = r.json()
        assert r.status_code == 200
        assert body["code"] == 0
        assert body["data"]["status"] == "pending"


def test_change_password_api_success():
    """修改密码接口成功"""
    with patch("app.api.auth.AuthService") as MockSvc:
        instance = MockSvc.return_value
        instance.change_password = AsyncMock(return_value=None)
        client = TestClient(app, raise_server_exceptions=False)
        with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"})):
            r = client.put("/api/v1/auth/password", json={"old_password": "Old1234", "new_password": "New12345"}, headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert r.status_code == 200
            assert body["code"] == 0
