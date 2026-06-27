"""
文件名: tests/api/test_email_api.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 邮件路由单元测试（模板 CRUD + 发送 + SMTP 配置）
"""
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


def _auth_patch():
    return patch(
        "app.api.deps.AuthService.verify_token",
        AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"}),
    )


def _admin_auth_patch():
    """admin 身份（用于 config 接口）"""
    return patch(
        "app.api.deps.AuthService.verify_token",
        AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "admin"}),
    )


def test_send_mail_by_template():
    """发送邮件（模板）"""
    with patch("app.api.email.EmailService") as MockSvc:
        instance = MockSvc.return_value
        instance.send_mail = AsyncMock(return_value={"status": "success"})
        with _auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/email/send", json={
                "to_email": "cand@x.com", "template_id": "t1",
                "variables": {"candidate_name": "张三"}
            }, headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["status"] == "success"


def test_send_test_admin():
    """发送测试邮件（admin only）"""
    with patch("app.api.email.EmailService") as MockSvc:
        instance = MockSvc.return_value
        instance.send_test = AsyncMock(return_value={"status": "success"})
        with _admin_auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/email/send-test", json={"to_email": "admin@x.com"}, headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["status"] == "success"


def test_send_test_hr_forbidden():
    """hr 无权发送测试邮件"""
    with _auth_patch():
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/email/send-test", json={"to_email": "x@y.com"}, headers={"Authorization": "Bearer fake"})
        assert r.json()["code"] == 1003


def test_list_templates():
    """模板列表"""
    with patch("app.api.email.EmailTemplateService") as MockSvc:
        instance = MockSvc.return_value
        instance.list_templates = AsyncMock(return_value={"list": [{"template_id": "t1", "name": "面试邀请"}], "total": 1})
        with _auth_patch():
            client = TestClient(app)
            r = client.get("/api/v1/email/templates", headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert body["code"] == 0
            assert body["data"]["total"] == 1


def test_create_template_admin():
    """admin 创建模板"""
    with patch("app.api.email.EmailTemplateService") as MockSvc:
        instance = MockSvc.return_value
        instance.create_template = AsyncMock(return_value={"template_id": "t1", "name": "自定义"})
        with _admin_auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/email/templates", json={
                "name": "自定义", "subject": "主题", "body": "<p>正文</p>", "category": "custom"
            }, headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["template_id"] == "t1"


def test_create_template_hr_forbidden():
    """hr 无权创建模板"""
    with _auth_patch():
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/email/templates", json={
            "name": "x", "subject": "x", "body": "x"
        }, headers={"Authorization": "Bearer fake"})
        assert r.json()["code"] == 1003


def test_delete_template_admin():
    """admin 删除模板"""
    with patch("app.api.email.EmailTemplateService") as MockSvc:
        instance = MockSvc.return_value
        instance.delete_template = AsyncMock()
        with _admin_auth_patch():
            client = TestClient(app)
            r = client.delete("/api/v1/email/templates/t1", headers={"Authorization": "Bearer fake"})
            assert r.json()["code"] == 0


def test_get_config():
    """AC18.1: 获取 SMTP 配置（仅 admin）"""
    with patch("app.api.email.EmailService") as MockSvc:
        instance = MockSvc.return_value
        instance.get_config = AsyncMock(return_value={"smtp_host": "smtp.x.com", "smtp_port": 465})
        with _admin_auth_patch():
            client = TestClient(app)
            r = client.get("/api/v1/email/config", headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["smtp_host"] == "smtp.x.com"


def test_update_config():
    """AC18.2: 更新 SMTP 配置（仅 admin）"""
    with patch("app.api.email.EmailService") as MockSvc:
        instance = MockSvc.return_value
        instance.update_config = AsyncMock()
        with _admin_auth_patch():
            client = TestClient(app)
            r = client.put("/api/v1/email/config", json={
                "smtp_host": "smtp.new.com", "smtp_port": 587,
                "smtp_user": "hr@new.com", "smtp_password": "secret"
            }, headers={"Authorization": "Bearer fake"})
            assert r.json()["code"] == 0
