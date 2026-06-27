"""
文件名: tests/api/test_users_api.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: users 路由 API 测试（全部 admin only）
"""
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


# admin 身份 mock
_ADMIN_USER = {"user_id": "u_admin", "username": "admin", "role": "admin"}


def _admin_auth_patch():
    """返回 admin 身份的 verify_token patch"""
    return patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value=_ADMIN_USER))


def test_list_users_api():
    """用户列表（admin only）"""
    with patch("app.api.users.UserService") as MockSvc:
        instance = MockSvc.return_value
        instance.list_users = AsyncMock(return_value={
            "list": [{"user_id": "u1", "username": "zhangsan"}],
            "total": 1, "page": 1, "page_size": 20, "total_pages": 1,
        })
        with _admin_auth_patch():
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/users?page=1&page_size=20", headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert r.status_code == 200
            assert body["code"] == 0
            assert body["data"]["total"] == 1


def test_create_user_api():
    """创建账号（admin only）"""
    with patch("app.api.users.UserService") as MockSvc:
        instance = MockSvc.return_value
        instance.create_user = AsyncMock(return_value={"user_id": "u2", "username": "new", "status": "approved"})
        with _admin_auth_patch():
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post("/api/v1/users", json={"username": "new", "password": "Pass1234", "role": "hr"}, headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert r.status_code == 200
            assert body["data"]["username"] == "new"


def test_get_user_api():
    """用户详情（admin only）"""
    with patch("app.api.users.UserService") as MockSvc:
        instance = MockSvc.return_value
        instance.get_user = AsyncMock(return_value={"user_id": "u1", "username": "zhangsan", "status": "approved"})
        with _admin_auth_patch():
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/users/u1", headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert r.status_code == 200
            assert body["data"]["user_id"] == "u1"


def test_approve_api():
    """审批通过（admin only）"""
    with patch("app.api.users.UserService") as MockSvc:
        instance = MockSvc.return_value
        instance.approve = AsyncMock(return_value=None)
        with _admin_auth_patch():
            client = TestClient(app, raise_server_exceptions=False)
            r = client.put("/api/v1/users/u1/approve", headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert r.status_code == 200
            assert body["code"] == 0
            instance.approve.assert_called_once_with("u1")


def test_reject_api():
    """拒绝申请（admin only）"""
    with patch("app.api.users.UserService") as MockSvc:
        instance = MockSvc.return_value
        instance.reject = AsyncMock(return_value=None)
        with _admin_auth_patch():
            client = TestClient(app, raise_server_exceptions=False)
            r = client.put("/api/v1/users/u1/reject", headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert r.status_code == 200
            assert body["code"] == 0
            instance.reject.assert_called_once_with("u1")


def test_update_status_api():
    """启用/禁用（admin only）"""
    with patch("app.api.users.UserService") as MockSvc:
        instance = MockSvc.return_value
        instance.update_status = AsyncMock(return_value=None)
        with _admin_auth_patch():
            client = TestClient(app, raise_server_exceptions=False)
            r = client.put("/api/v1/users/u1/status", json={"status": "disabled"}, headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert r.status_code == 200
            assert body["code"] == 0
            instance.update_status.assert_called_once_with("u1", "disabled")


def test_reset_password_api():
    """重置密码（admin only）"""
    with patch("app.api.users.UserService") as MockSvc:
        instance = MockSvc.return_value
        instance.reset_password = AsyncMock(return_value=None)
        with _admin_auth_patch():
            client = TestClient(app, raise_server_exceptions=False)
            r = client.put("/api/v1/users/u1/password", json={"new_password": "NewPass1234"}, headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert r.status_code == 200
            assert body["code"] == 0
            instance.reset_password.assert_called_once_with("u1", "NewPass1234")


def test_delete_user_api():
    """删除账号（admin only，不能删自己）"""
    with patch("app.api.users.UserService") as MockSvc:
        instance = MockSvc.return_value
        instance.delete = AsyncMock(return_value=None)
        with _admin_auth_patch():
            client = TestClient(app, raise_server_exceptions=False)
            r = client.delete("/api/v1/users/u1", headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert r.status_code == 200
            assert body["code"] == 0
            # current_user_id 应来自 admin user 的 user_id
            instance.delete.assert_called_once_with("u1", current_user_id="u_admin")


def test_users_reject_hr():
    """hr 角色调用用户管理接口应被拒绝（403）"""
    with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u_hr", "username": "hr", "role": "hr"})):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/users", headers={"Authorization": "Bearer fake"})
        body = r.json()
        # hr 调用 admin 接口应返回权限不足（FORBIDDEN=1003）
        assert body["code"] == 1003
