"""
文件名: tests/services/test_candidate_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: CandidateService 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.candidate_service import CandidateService


@pytest.fixture
def svc():
    s = CandidateService()
    s.resumes_coll = MagicMock()
    s.resumes_coll.find_one = AsyncMock(return_value=None)
    s.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[])
    s.embedding = MagicMock()
    s.embedding.encode = MagicMock(return_value=([[0.1] * 1024], [{}]))
    s.vector_store = AsyncMock()
    return s


@pytest.mark.asyncio
async def test_get_similar(svc):
    """AC15.1: 基于向量找相似候选人"""
    svc.resumes_coll.find_one = AsyncMock(return_value={
        "resume_id": "r1", "candidate_id": "c1", "summary": "Java 5年", "skills": ["Java"]
    })
    svc.vector_store.hybrid_search = AsyncMock(return_value=[
        {"candidate_id": "c2", "score": 0.85, "parent_content": "..."},
        {"candidate_id": "c3", "score": 0.78, "parent_content": "..."},
    ])
    svc.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[
        {"candidate_id": "c2", "resume_id": "r2", "name": "李四", "work_years": 4, "skills": ["Java"]},
        {"candidate_id": "c3", "resume_id": "r3", "name": "王五", "work_years": 6, "skills": ["Java", "Spring"]},
    ])
    result = await svc.get_similar(resume_id="r1", top_k=5)
    assert len(result) >= 2
    assert result[0]["candidate_id"] == "c2"


@pytest.mark.asyncio
async def test_compare_candidates(svc):
    """AC16.1: 候选人对比"""
    svc.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[
        {"candidate_id": "c1", "name": "张三", "work_years": 5, "skills": ["Java"],
         "expected_salary": {"min": 20, "max": 30}, "education": "本科", "education_level": 2},
        {"candidate_id": "c2", "name": "李四", "work_years": 7, "skills": ["Python"],
         "expected_salary": {"min": 25, "max": 35}, "education": "硕士", "education_level": 3},
    ])
    result = await svc.compare(candidate_ids=["c1", "c2"])
    assert len(result["candidates"]) == 2
    dimensions = result["dimensions"]
    assert "work_years" in dimensions
    assert "education_level" in dimensions
