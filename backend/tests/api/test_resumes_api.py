"""
文件名: tests/api/test_resumes_api.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 简历路由 API 测试
"""
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


def test_upload_resume():
    """上传简历应返回 code=0 和 resume_id"""
    with patch("app.api.resumes.ResumeService") as MockSvc:
        instance = MockSvc.return_value
        instance.upload = AsyncMock(return_value={
            "resume_id": "r1", "candidate_id": "c1", "file_name": "test.pdf",
            "parse_status": "parsing", "is_duplicate": False, "duplicate_with": None,
        })
        with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"})):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post("/api/v1/resumes/upload",
                files={"file": ("test.pdf", b"pdf-bytes", "application/pdf")},
                headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert r.status_code == 200
            assert body["code"] == 0
            assert body["data"]["resume_id"] == "r1"


def test_list_resumes():
    """列表查询应返回 code=0 和 total"""
    with patch("app.api.resumes.ResumeService") as MockSvc:
        instance = MockSvc.return_value
        instance.list = AsyncMock(return_value={"list": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0})
        with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"})):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/resumes", headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert body["code"] == 0
            assert body["data"]["total"] == 0


def test_get_detail_not_found():
    """不存在应返回 code=1004"""
    with patch("app.api.resumes.ResumeService") as MockSvc:
        instance = MockSvc.return_value
        from app.core.exceptions import NotFoundError
        instance.get_detail = AsyncMock(side_effect=NotFoundError("不存在"))
        with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"})):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/resumes/r1", headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert body["code"] == 1004


def test_delete_resume():
    """删除应返回 code=0"""
    with patch("app.api.resumes.ResumeService") as MockSvc:
        instance = MockSvc.return_value
        instance.delete = AsyncMock()
        with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"})):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.delete("/api/v1/resumes/r1", headers={"Authorization": "Bearer fake"})
            assert r.json()["code"] == 0


def test_update_tags_api():
    """AC7.1: 更新标签"""
    with patch("app.api.resumes.TagService") as MockSvc:
        instance = MockSvc.return_value
        instance.update_tags = AsyncMock(return_value={"resume_id": "r1", "tags": ["已面试"]})
        with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"})):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.put("/api/v1/resumes/r1/tags", json={"tags": ["已面试"]}, headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["tags"] == ["已面试"]


def test_toggle_favorite_api():
    """AC8.1: 切换收藏"""
    with patch("app.api.resumes.TagService") as MockSvc:
        instance = MockSvc.return_value
        instance.toggle_favorite = AsyncMock(return_value={"resume_id": "r1", "is_favorite": True})
        with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"})):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.put("/api/v1/resumes/r1/favorite", json={"is_favorite": True}, headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["is_favorite"] is True


def test_update_notes_api():
    """AC9.1: 更新评价"""
    with patch("app.api.resumes.TagService") as MockSvc:
        instance = MockSvc.return_value
        instance.update_notes = AsyncMock(return_value={"resume_id": "r1", "notes": "x"})
        with patch("app.api.deps.AuthService.verify_token", AsyncMock(return_value={"user_id": "u1", "username": "admin", "role": "hr"})):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.put("/api/v1/resumes/r1/notes", json={"notes": "x"}, headers={"Authorization": "Bearer fake"})
            assert r.json()["code"] == 0
