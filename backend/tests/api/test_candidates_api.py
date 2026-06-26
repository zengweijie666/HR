"""
文件名: tests/api/test_candidates_api.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 候选人路由单元测试
"""
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


def _auth_patch():
    return patch(
        "app.api.deps.AuthService.verify_token",
        AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"}),
    )


def test_export_excel():
    """AC14.1: 导出 Excel"""
    with patch("app.api.candidates.ExportService") as MockSvc:
        instance = MockSvc.return_value
        instance.export_excel = AsyncMock(return_value=b"fake-excel-bytes")
        with _auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/candidates/export",
                            json={"candidate_ids": ["c1"], "columns": ["name"]},
                            headers={"Authorization": "Bearer fake"})
            assert r.status_code == 200
            assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_get_similar():
    """AC15.1: 相似候选人"""
    with patch("app.api.candidates.CandidateService") as MockSvc:
        instance = MockSvc.return_value
        instance.get_similar = AsyncMock(return_value=[{"candidate_id": "c2", "name": "李四"}])
        with _auth_patch():
            client = TestClient(app)
            r = client.get("/api/v1/candidates/similar/r1",
                           headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert body["code"] == 0
            assert body["data"][0]["candidate_id"] == "c2"


def test_compare():
    """AC16.1: 候选人对比"""
    with patch("app.api.candidates.CandidateService") as MockSvc:
        instance = MockSvc.return_value
        instance.compare = AsyncMock(return_value={"candidates": [], "dimensions": ["work_years"]})
        with _auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/candidates/compare",
                            json={"candidate_ids": ["c1", "c2"]},
                            headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert body["code"] == 0
            assert "dimensions" in body["data"]
