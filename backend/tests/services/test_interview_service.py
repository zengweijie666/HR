"""
文件名: tests/services/test_interview_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: InterviewService 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.interview_service import InterviewService


@pytest.fixture
def svc():
    """构造带 mock collection 的 service（motor find() 同步返回 cursor，用 MagicMock）"""
    s = InterviewService()
    s.resumes_coll = MagicMock()
    s.notes_coll = MagicMock()
    return s


@pytest.mark.asyncio
async def test_generate_questions(svc):
    """AC20.1: LLM 生成面试题"""
    with patch("app.services.interview_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value='[{"question":"介绍项目经验","category":"项目"},{"question":"Java GC 机制","category":"技术"}]')
        svc.resumes_coll.find_one = AsyncMock(return_value={
            "resume_id": "r1", "name": "张三", "skills": ["Java", "Spring"], "work_years": 5
        })
        result = await svc.generate_questions(resume_id="r1", job_title="Java 工程师")
        assert len(result) == 2
        assert result[0]["question"] == "介绍项目经验"
        assert "category" in result[0]


@pytest.mark.asyncio
async def test_generate_questions_resume_not_found(svc):
    """AC20.2: 简历不存在时返回空列表"""
    svc.resumes_coll.find_one = AsyncMock(return_value=None)
    result = await svc.generate_questions(resume_id="r_not_exist", job_title="x")
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_save_note(svc):
    """AC21.1: 保存面试评价"""
    svc.notes_coll.insert_one = AsyncMock()
    result = await svc.save_note(
        resume_id="r1", interviewer="HR-小李", rating=4,
        result="通过", content="技术能力扎实，沟通良好"
    )
    assert "note_id" in result
    svc.notes_coll.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_notes(svc):
    """AC21.2: 查询面试评价列表"""
    svc.notes_coll.find.return_value.sort.return_value.to_list = AsyncMock(return_value=[
        {"note_id": "n1", "resume_id": "r1", "interviewer": "HR", "rating": 4, "content": "好"}
    ])
    result = await svc.get_notes(resume_id="r1")
    assert len(result) == 1
    assert result[0]["note_id"] == "n1"


@pytest.mark.asyncio
async def test_get_notes_empty(svc):
    """AC21.3: 无评价返回空列表"""
    svc.notes_coll.find.return_value.sort.return_value.to_list = AsyncMock(return_value=[])
    result = await svc.get_notes(resume_id="r1")
    assert result == []
