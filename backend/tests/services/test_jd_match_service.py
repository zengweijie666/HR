"""
文件名: tests/services/test_jd_match_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: JdMatchService 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.jd_match_service import JdMatchService


@pytest.fixture
def svc():
    s = JdMatchService()
    s.resumes_coll = MagicMock()
    s.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[])
    s.embedding = MagicMock()
    s.embedding.encode = MagicMock(return_value=([[0.1] * 1024], [{}]))
    s.vector_store = AsyncMock()
    s.reranker = MagicMock()
    s.reranker.rerank = MagicMock(return_value=[0.92, 0.75])
    s.llm = AsyncMock()
    return s


@pytest.mark.asyncio
async def test_match_jd_basic(svc):
    """AC19.1: JD 解析 + 匹配候选人"""
    svc.llm.chat = AsyncMock(side_effect=[
        '{"title":"Java 工程师","skills":["Java","Spring"],"work_years_min":3,"salary_max":30}',
        "匹配度高，5 年 Java 经验，技能完全匹配",
    ])
    svc.vector_store.hybrid_search = AsyncMock(return_value=[
        {"candidate_id": "c1", "score": 0.9, "parent_content": "Java 5年经验"}
    ])
    svc.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[
        {"candidate_id": "c1", "resume_id": "r1", "name": "张三", "work_years": 5, "skills": ["Java"], "summary": ""}
    ])
    result = await svc.match_jd(jd_text="招聘 Java 工程师，3 年经验，30K 以内")
    assert "title" in result["jd"]
    assert "candidates" in result
    assert len(result["candidates"]) >= 1
    assert "match_score" in result["candidates"][0]
    assert "reason" in result["candidates"][0]


@pytest.mark.asyncio
async def test_jd_parse(svc):
    """AC19.2: LLM 解析 JD"""
    svc.llm.chat = AsyncMock(return_value='{"title":"Python 开发","skills":["Python","Django"],"work_years_min":2,"salary_max":25}')
    parsed = await svc._parse_jd("招 Python 开发，2 年经验")
    assert parsed["title"] == "Python 开发"
    assert "Python" in parsed["skills"]
    assert parsed["work_years_min"] == 2
