"""
文件名: tests/api/test_chat_api.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 对话路由单元测试
"""
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


def _auth_patch():
    return patch(
        "app.api.deps.AuthService.verify_token",
        AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"}),
    )


def test_create_session():
    """AC10.1: 创建会话"""
    with patch("app.api.chat.AgentService") as MockSvc:
        instance = MockSvc.return_value
        instance.create_session = AsyncMock(return_value={"session_id": "s1", "title": "新会话"})
        with _auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/chat/sessions", json={"title": "新会话"},
                            headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["session_id"] == "s1"


def test_get_sessions():
    """AC10.2: 会话列表"""
    with patch("app.api.chat.AgentService") as MockSvc:
        instance = MockSvc.return_value
        instance.get_sessions = AsyncMock(return_value={
            "list": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0
        })
        with _auth_patch():
            client = TestClient(app)
            r = client.get("/api/v1/chat/sessions?page=1&page_size=20",
                           headers={"Authorization": "Bearer fake"})
            assert r.json()["code"] == 0


def test_delete_session():
    """AC10.4: 删除会话"""
    with patch("app.api.chat.AgentService") as MockSvc:
        instance = MockSvc.return_value
        instance.delete_session = AsyncMock()
        with _auth_patch():
            client = TestClient(app)
            r = client.delete("/api/v1/chat/sessions/s1",
                              headers={"Authorization": "Bearer fake"})
            assert r.json()["code"] == 0
