"""
文件名: tests/api/test_email_api.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 邮件路由单元测试
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


def test_send_recommendation():
    """AC17.1: 发送推荐邮件"""
    with patch("app.api.email.EmailService") as MockSvc:
        instance = MockSvc.return_value
        instance.send_recommendation = AsyncMock(return_value={"status": "success", "sent_count": 2})
        with _auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/email/send", json={
                "to_email": "boss@x.com", "candidate_ids": ["c1", "c2"], "job_title": "Java"
            }, headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["status"] == "success"


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
