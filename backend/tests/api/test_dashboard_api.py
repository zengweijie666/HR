"""
文件名: tests/api/test_dashboard_api.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 看板路由单元测试
"""
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


def _auth_patch():
    return patch(
        "app.api.deps.AuthService.verify_token",
        AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"}),
    )


def test_get_stats():
    """AC22.1-22.3: 获取看板统计"""
    with patch("app.api.dashboard.DashboardService") as MockSvc:
        instance = MockSvc.return_value
        instance.get_stats = AsyncMock(return_value={
            "total_resumes": 100, "favorite_count": 30, "parsing_count": 5,
            "total_sessions": 50, "top_skills": [],
            "education_distribution": [], "salary_distribution": [],
        })
        with _auth_patch():
            client = TestClient(app)
            r = client.get("/api/v1/dashboard/stats", headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert body["code"] == 0
            assert body["data"]["total_resumes"] == 100
