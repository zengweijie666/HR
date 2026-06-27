"""
文件名: tests/models/test_models.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试 Pydantic 数据模型
"""
import pytest
from app.models.common import ApiResponse, PageResult
from app.models.auth import LoginRequest, TokenResponse, UserInfo
from app.models.resume import ResumeListItem, ResumeDetail, UploadResponse
from app.models.candidate import CandidateCard
from app.models.chat import ChatMessage


def test_api_response():
    r = ApiResponse(code=0, message="ok", data={"a": 1}, trace_id="t1")
    assert r.code == 0
    assert r.data == {"a": 1}


def test_page_result():
    p = PageResult(list=[1, 2], total=2, page=1, page_size=20, total_pages=1)
    assert p.total_pages == 1


def test_login_request():
    r = LoginRequest(email="a@b.com", password="123")
    assert r.email == "a@b.com"


def test_token_response():
    t = TokenResponse(
        access_token="at", refresh_token="rt", token_type="bearer",
        expires_in=3600, user=UserInfo(user_id="u1", username="admin", role="hr", email="a@b.com")
    )
    assert t.token_type == "bearer"


def test_resume_list_item():
    r = ResumeListItem(
        resume_id="r1", candidate_id="c1", name="张三", gender="男", age=30,
        education="本科", education_level=1, work_years=5, skills=["Java"],
        expected_salary={"min": 20, "max": 30}, tags=[], is_favorite=False,
        parse_status="completed", location="北京", created_at="2026-06-26T10:00:00Z"
    )
    assert r.education_level == 1


def test_candidate_card():
    c = CandidateCard(
        candidate_id="c1", resume_id="r1", name="张三", work_years=5,
        education="本科", skills=["Java"], expected_salary={"min": 20, "max": 30},
        score=95, reason="匹配", tags=[], is_favorite=False
    )
    assert c.score == 95


def test_chat_message():
    m = ChatMessage(
        message_id="m1", session_id="s1", role="user",
        content="hi", intent=None, strategy=None, candidates=None,
        created_at="2026-06-26T10:00:00Z"
    )
    assert m.role == "user"


def test_resume_list_item_validation_error():
    """education_level 越界应抛错"""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ResumeListItem(
            resume_id="r", candidate_id="c", name="x", gender="m", age=1,
            education="x", education_level=9, work_years=1, skills=[],
            expected_salary={"min": 1, "max": 2}, tags=[], is_favorite=False,
            parse_status="completed", location="x", created_at="x"
        )
