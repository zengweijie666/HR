"""
文件名: tests/api/test_search_api.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 检索路由单元测试
"""
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


def test_search():
    """AC13.1: POST /api/v1/search 返回候选人卡片"""
    with patch("app.api.search.SearchService") as MockSvc:
        instance = MockSvc.return_value
        instance.search = AsyncMock(return_value=[{
            "candidate_id": "c1", "resume_id": "r1", "name": "张三", "work_years": 5,
            "education": "本科", "skills": ["Java"], "expected_salary": {"min": 20, "max": 30},
            "score": 85.0, "reason": "匹配度高", "tags": [], "is_favorite": False
        }])
        with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"})):
            client = TestClient(app)
            r = client.post("/api/v1/search", json={"query": "Java 5年", "filters": {}, "top_k": 10},
                            headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert body["code"] == 0
            assert body["data"][0]["candidate_id"] == "c1"
