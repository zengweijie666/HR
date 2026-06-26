"""
文件名: tests/services/test_search_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: SearchService 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.search_service import SearchService


@pytest.fixture
def svc():
    """构造全 mock 的 SearchService 实例"""
    s = SearchService()
    s.embedding = MagicMock()
    s.embedding.encode = MagicMock(return_value=([[0.1] * 1024], [{}]))
    s.reranker = MagicMock()
    s.reranker.rerank = MagicMock(return_value=[0.9, 0.5])
    s.vector_store = AsyncMock()
    s.vector_store.hybrid_search = AsyncMock(return_value=[
        {"chunk_id": "c1", "candidate_id": "c1", "score": 0.9, "parent_content": "Java 5年经验"},
        {"chunk_id": "c2", "candidate_id": "c2", "score": 0.5, "parent_content": "Python 3年经验"},
    ])
    s.strategy_selector = AsyncMock()
    s.strategy_selector.select = AsyncMock(return_value="direct")
    s.strategy_selector.rewrite = AsyncMock(return_value=["Java 5年"])
    # motor find() 同步返回 cursor，需用 MagicMock；to_list 是 async
    s.resumes_coll = MagicMock()
    s.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[])
    s.redis = AsyncMock()
    s.redis.get = AsyncMock(return_value=None)
    s.redis.setex = AsyncMock()
    return s


@pytest.mark.asyncio
async def test_search_basic(svc):
    """AC13.1: 自然语言搜索返回候选人卡片"""
    svc.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[
        {"resume_id": "r1", "candidate_id": "c1", "name": "张三", "skills": ["Java"], "work_years": 5,
         "education": "本科", "education_level": 2, "expected_salary": {"min": 20, "max": 30},
         "tags": [], "is_favorite": False}
    ])
    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=["85", "匹配度高"])
        results = await svc.search("Java 5年", filters={}, top_k=10)
    assert len(results) >= 1
    assert results[0]["candidate_id"] == "c1"


@pytest.mark.asyncio
async def test_search_with_filters(svc):
    """AC13.2: 条件过滤（学历/年限/薪资）透传到 vector_store"""
    svc.vector_store.hybrid_search = AsyncMock(return_value=[
        {"chunk_id": "c1", "candidate_id": "c1", "score": 0.9, "parent_content": "..."}
    ])
    filters = {"education_min": 2, "work_years_min": 5, "salary_max": 30}
    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=["80", "匹配"])
        await svc.search("Java", filters=filters, top_k=10)
    call_kwargs = svc.vector_store.hybrid_search.call_args.kwargs
    assert call_kwargs.get("filters") == filters or svc.vector_store.hybrid_search.call_args[0][2] == filters


@pytest.mark.asyncio
async def test_search_cache(svc):
    """AC13.3: 相同查询命中缓存，不调用 vector_store"""
    svc.redis.get = AsyncMock(return_value='[{"candidate_id":"c_cached"}]')
    results = await svc.search("Java 5年", filters={}, top_k=10)
    assert results[0]["candidate_id"] == "c_cached"
    svc.vector_store.hybrid_search.assert_not_called()


@pytest.mark.asyncio
async def test_search_rerank_order(svc):
    """AC13.4: Reranker 重排后按 score 降序"""
    svc.vector_store.hybrid_search = AsyncMock(return_value=[
        {"chunk_id": "c1", "candidate_id": "c1", "score": 0.5, "parent_content": "doc1"},
        {"chunk_id": "c2", "candidate_id": "c2", "score": 0.9, "parent_content": "doc2"},
    ])
    svc.reranker.rerank = MagicMock(return_value=[0.3, 0.95])
    svc.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[
        {"candidate_id": "c2", "resume_id": "r2", "name": "李四"},
        {"candidate_id": "c1", "resume_id": "r1", "name": "张三"},
    ])
    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=["90", "好", "60", "差"])
        results = await svc.search("Java", filters={}, top_k=10)
    # rerank 后 c2 (0.95) 在前；_enrich 后顺序保持
    assert results[0]["candidate_id"] == "c2"
