"""
文件名: tests/api/test_interview_api.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 面试路由单元测试
"""
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


def _auth_patch():
    return patch(
        "app.api.deps.AuthService.verify_token",
        AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"}),
    )


def test_generate_questions():
    """AC20.1: 生成面试题"""
    with patch("app.api.interview.InterviewService") as MockSvc:
        instance = MockSvc.return_value
        instance.generate_questions = AsyncMock(return_value=[
            {"question": "Java GC", "category": "技术"}
        ])
        with _auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/interview/questions", json={
                "resume_id": "r1", "job_title": "Java"
            }, headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert body["code"] == 0
            assert body["data"][0]["question"] == "Java GC"


def test_save_note():
    """AC21.1: 保存面试评价"""
    with patch("app.api.interview.InterviewService") as MockSvc:
        instance = MockSvc.return_value
        instance.save_note = AsyncMock(return_value={"note_id": "n1", "rating": 4})
        with _auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/interview/notes", json={
                "resume_id": "r1", "interviewer": "HR", "rating": 4,
                "result": "通过", "content": "好"
            }, headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["note_id"] == "n1"


def test_get_notes():
    """AC21.2: 查询面试评价"""
    with patch("app.api.interview.InterviewService") as MockSvc:
        instance = MockSvc.return_value
        instance.get_notes = AsyncMock(return_value=[{"note_id": "n1", "rating": 4}])
        with _auth_patch():
            client = TestClient(app)
            r = client.get("/api/v1/interview/notes/r1", headers={"Authorization": "Bearer fake"})
            assert r.json()["data"][0]["note_id"] == "n1"
