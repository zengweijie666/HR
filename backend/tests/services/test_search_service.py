"""
文件名: tests/services/test_search_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: SearchService 单元测试
"""
import json
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
        {"chunk_id": "c1", "candidate_id": "r1", "score": 0.9, "parent_content": "Java 5年经验"},
        {"chunk_id": "c2", "candidate_id": "r2", "score": 0.5, "parent_content": "Python 3年经验"},
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
    _score_json = json.dumps({"skill": 85, "experience": 80, "education": 75, "salary": 85, "overall": 0, "reason": "匹配度高"})
    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=[_score_json])
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
        {"chunk_id": "c1", "candidate_id": "r1", "score": 0.5, "parent_content": "doc1"},
        {"chunk_id": "c2", "candidate_id": "r2", "score": 0.9, "parent_content": "doc2"},
    ])
    svc.reranker.rerank = MagicMock(return_value=[0.3, 0.95])
    svc.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[
        {"candidate_id": "c2", "resume_id": "r2", "name": "李四"},
        {"candidate_id": "c1", "resume_id": "r1", "name": "张三"},
    ])
    _score_high = json.dumps({"skill": 90, "experience": 85, "education": 75, "salary": 80, "overall": 0, "reason": "好"})
    _score_low = json.dumps({"skill": 60, "experience": 50, "education": 75, "salary": 80, "overall": 0, "reason": "差"})
    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=[_score_high, _score_low])
        results = await svc.search("Java", filters={}, top_k=10)
    # rerank 后 r2 (0.95) 在前；_enrich 后顺序保持
    assert results[0]["candidate_id"] == "c2"


@pytest.mark.asyncio
async def test_llm_score_multi_json_parse():
    """_llm_score_multi 正常 JSON 解析应返回 4 维度 + overall + reason

    overall 由代码加权计算（0.4*skill + 0.3*experience + 0.2*education + 0.1*salary），
    不再信任 LLM 返回的 overall，避免评分趋同。
    """
    svc = SearchService()
    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value=json.dumps({
            "skill": 85, "experience": 70, "education": 90, "salary": 60,
            "overall": 78, "reason": "技能高度匹配"
        }))
        result = await svc._llm_score_multi("前端工程师", {"name": "张三", "skills": ["Vue"]}, 0.8)
    assert result["skill"] == 85
    assert result["experience"] == 70
    assert result["education"] == 90
    assert result["salary"] == 60
    # overall = 0.4*85 + 0.3*70 + 0.2*90 + 0.1*60 = 34+21+18+6 = 79
    assert result["overall"] == 79
    assert result["reason"] == "技能高度匹配"


@pytest.mark.asyncio
async def test_llm_score_multi_fallback_rerank():
    """_llm_score_multi LLM 调用失败应回退 rerank_score*100"""
    svc = SearchService()
    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=Exception("LLM 调用失败"))
        result = await svc._llm_score_multi("前端工程师", {"name": "张三"}, 0.8)
    assert result["skill"] == 80  # 0.8 * 100
    assert result["experience"] == 80
    assert result["education"] == 80
    assert result["salary"] == 80
    assert result["overall"] == 80
    assert "语义相似度" in result["reason"]


@pytest.mark.asyncio
async def test_llm_score_multi_fallback_zero():
    """_llm_score_multi JSON 解析失败应回退到 rerank_score 兜底（而非全0，保证排序稳定性）"""
    svc = SearchService()
    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value="not a json")
        result = await svc._llm_score_multi("前端工程师", {"name": "张三"}, 0.8)
    # JSON 解析失败时回退 rerank_score*100，所有维度=80，overall=80
    assert result["skill"] == 80
    assert result["experience"] == 80
    assert result["education"] == 80
    assert result["salary"] == 80
    assert result["overall"] == 80
    assert "语义相似度" in result["reason"]


@pytest.mark.asyncio
async def test_search_nlp_recalls_bert_candidate_via_synonym_expand(svc):
    """AC: 搜索 NLP 时通过同义词扩展多查询检索，能召回写 BERT/FastText 但没写 NLP 的候选人

    业务场景: 简历库中张三写了 NLP，李四只写了 BERT/FastText（没写 NLP）。
    直接检索"NLP"只能召回张三；扩展为"NLP BERT FastText ..."后多查询检索，
    第二次检索用扩展查询能命中李四，最终两人都被召回。
    """
    # 1. strategy_selector 返回 direct 策略 + 同义词扩展后的两个查询
    svc.strategy_selector.select = AsyncMock(return_value="direct")
    svc.strategy_selector.rewrite = AsyncMock(return_value=[
        "NLP",
        "NLP BERT FastText Transformer 自然语言处理",
    ])

    # 2. vector_store 第一次检索（用 "NLP"）只命中张三
    #    第二次检索（用扩展查询）命中李四（写 BERT 的候选人）
    svc.vector_store.hybrid_search = AsyncMock(side_effect=[
        [{"chunk_id": "c1", "candidate_id": "r1", "score": 0.9, "parent_content": "张三 NLP 算法工程师"}],
        [{"chunk_id": "c2", "candidate_id": "r2", "score": 0.85, "parent_content": "李四 BERT FastText 文本分类"}],
    ])

    # 3. MongoDB 返回两位候选人元数据
    svc.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[
        {"resume_id": "r1", "candidate_id": "c1", "name": "张三", "skills": ["NLP", "Python"],
         "work_years": 5, "education": "硕士", "education_level": 2,
         "expected_salary": {"min": 20, "max": 30}, "tags": [], "is_favorite": False},
        {"resume_id": "r2", "candidate_id": "c2", "name": "李四", "skills": ["BERT", "FastText", "Python"],
         "work_years": 3, "education": "硕士", "education_level": 2,
         "expected_salary": {"min": 18, "max": 25}, "tags": [], "is_favorite": False},
    ])

    # 4. Reranker 给两个文档打分
    svc.reranker.rerank = MagicMock(return_value=[0.9, 0.85])

    # 5. LLM 评分（每个候选人调一次 chat）
    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=[
            json.dumps({"skill": 90, "experience": 80, "education": 90, "salary": 70,
                        "overall": 85, "reason": "NLP技能高度匹配"}),
            json.dumps({"skill": 85, "experience": 70, "education": 90, "salary": 75,
                        "overall": 80, "reason": "BERT/FastText 属 NLP 领域，关联匹配"}),
        ])
        results = await svc.search("NLP", filters={}, top_k=10)

    # 验证：两位候选人都被召回（李四虽没写 NLP，但通过同义词扩展被召回）
    names = [r["name"] for r in results]
    assert "张三" in names
    assert "李四" in names, "写 BERT/FastText 但没写 NLP 的候选人必须通过同义词扩展被召回"

    # 验证：vector_store 被调用了两次（多查询检索）
    assert svc.vector_store.hybrid_search.call_count == 2


@pytest.mark.asyncio
async def test_score_differentiation_between_senior_and_junior():
    """AC: 同需求下 4年经验资深候选人 overall 必须高于 0年经验应届生

    业务场景: 搜索 NLP 工程师，毛光铭(4年NLP经验)应远高于苏威(0年应届生)。
    之前问题: LLM 给所有候选人都打 78 分，无区分度。
    修复: overall 用代码加权计算，且 SCORE_PROMPT 强制要求 experience 维度按年限拉开差距。
    """
    svc = SearchService()

    # 模拟 LLM 对 4年经验资深候选人的评分（高 skill + 高 experience）
    senior_resp = json.dumps({
        "skill": 92, "experience": 90, "education": 75, "salary": 85,
        "overall": 99, "reason": "4年NLP对口经验，技能完全覆盖"
    })
    # 模拟 LLM 对 0年经验应届生的评分（中等 skill + 低 experience）
    junior_resp = json.dumps({
        "skill": 72, "experience": 50, "education": 75, "salary": 85,
        "overall": 99, "reason": "仅有BERT课程项目，无对口工作经验"
    })

    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=[senior_resp, junior_resp])

        senior = await svc._llm_score_multi("NLP工程师", {
            "name": "毛光铭", "work_years": 4, "education": "本科",
            "skills": ["BERT", "NLP", "Transformer"],
            "work_experience": [{"company": "某公司", "position": "NLP开发工程师"}],
        }, 0.9)

        junior = await svc._llm_score_multi("NLP工程师", {
            "name": "苏威", "work_years": 0, "education": "本科",
            "skills": ["BERT", "NLP"],
            "work_experience": [],
        }, 0.7)

    # 验证：资深候选人 overall 明显高于应届生（区分度 ≥ 10 分）
    assert senior["overall"] > junior["overall"]
    assert senior["overall"] - junior["overall"] >= 10, (
        f"区分度不足: senior={senior['overall']}, junior={junior['overall']}, "
        f"差值应≥10"
    )
    # experience 维度必须有明显差距
    assert senior["experience"] > junior["experience"]


@pytest.mark.asyncio
async def test_overall_ignores_llm_overall_uses_weighted_formula():
    """AC: overall 由代码加权计算，不信任 LLM 返回的 overall

    防止 LLM 给所有候选人都返回相同 overall=78 导致无区分度。
    即使 LLM 返回 overall=99，代码也会重新计算。
    """
    svc = SearchService()
    with patch("app.services.search_service.llm_client") as mock_llm:
        # LLM 故意返回 overall=99（虚高）
        mock_llm.chat = AsyncMock(return_value=json.dumps({
            "skill": 85, "experience": 70, "education": 90, "salary": 60,
            "overall": 99, "reason": "测试"
        }))
        result = await svc._llm_score_multi("前端", {"name": "张三", "skills": ["Vue"]}, 0.8)

    # overall 应为加权计算结果 79，而非 LLM 返回的 99
    expected = round(0.4 * 85 + 0.3 * 70 + 0.2 * 90 + 0.1 * 60)
    assert result["overall"] == expected
    assert result["overall"] != 99


def test_build_candidate_brief_extracts_key_fields():
    """AC: _build_candidate_brief 只提取评分相关字段，过滤 resume_id/tags 等无关字段"""
    candidate = {
        "resume_id": "res_abc",
        "candidate_id": "c123",
        "basic_info": {"name": "张三"},
        "work_years": 5,
        "education": "硕士",
        "skills": ["Python", "NLP", "BERT"],
        "work_experience": [
            {"company": "阿里", "position": "算法工程师", "description": "..."},
        ],
        "projects": [
            {"name": "NLP文本分类系统", "description": "基于BERT实现文本分类"},
        ],
        "summary": "5年NLP算法工程师",
        "tags": ["推荐"],  # 无关字段
        "is_favorite": False,  # 无关字段
        "expected_salary": {"min": 20, "max": 30},  # 无关字段（评分里有专门处理）
    }

    brief = SearchService._build_candidate_brief(candidate)

    # 应包含关键字段
    assert "张三" in brief
    assert "5年" in brief
    assert "硕士" in brief
    assert "NLP" in brief
    assert "阿里" in brief
    assert "算法工程师" in brief
    assert "NLP文本分类系统" in brief

    # 不应包含无关字段
    assert "res_abc" not in brief
    assert "c123" not in brief
    assert "is_favorite" not in brief
    assert "tags" not in brief


def test_build_candidate_brief_handles_missing_fields():
    """AC: _build_candidate_brief 应优雅处理缺失字段"""
    candidate = {}  # 空文档
    brief = SearchService._build_candidate_brief(candidate)
    assert "姓名:" in brief
    assert "工作年限:0年" in brief


def test_build_candidate_brief_truncates_long_project_desc():
    """AC: _build_candidate_brief 项目描述超长时应截断"""
    long_desc = "X" * 500
    candidate = {
        "name": "张三",
        "projects": [
            {"name": "项目A", "description": long_desc},
        ],
    }
    brief = SearchService._build_candidate_brief(candidate)
    # 项目描述应被截断到 100 字
    assert "项目A" in brief
    assert "X" * 500 not in brief
