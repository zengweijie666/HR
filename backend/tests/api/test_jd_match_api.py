"""
文件名: tests/api/test_jd_match_api.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: JD 匹配路由单元测试
"""
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


def _auth_patch():
    return patch(
        "app.api.deps.AuthService.verify_token",
        AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"}),
    )


def test_match_jd():
    """AC19.1-19.2: JD 匹配候选人"""
    with patch("app.api.jd_match.JdMatchService") as MockSvc:
        instance = MockSvc.return_value
        instance.match_jd = AsyncMock(return_value={
            "jd": {"title": "Java 工程师", "skills": ["Java"], "work_years_min": 3, "salary_max": 30},
            "candidates": [
                {"candidate_id": "c1", "name": "张三", "match_score": 92.0, "reason": "5 年 Java 经验"}
            ],
        })
        with _auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/jd-match", json={
                "jd_text": "招聘 Java 工程师，3 年经验，30K 以内",
                "top_k": 10,
            }, headers={"Authorization": "Bearer fake"})
            assert r.status_code == 200
            body = r.json()
            assert body["code"] == 0
            assert body["data"]["jd"]["title"] == "Java 工程师"
            assert len(body["data"]["candidates"]) == 1
            assert body["data"]["candidates"][0]["match_score"] == 92.0
