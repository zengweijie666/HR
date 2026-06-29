"""
文件名: tests/agent/test_nodes.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: LangGraph 5 节点单元测试
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agent.state import make_state
from app.agent.nodes import (
    intent_node,
    retrieve_rank_node,
    clarify_node,
    detail_node,
    respond_node,
)


@pytest.mark.asyncio
async def test_intent_search():
    """AC11.1: 意图识别 - 搜索"""
    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value="search")
        state = make_state(query="找一个Java 5年的候选人", session_id="s1")
        result = await intent_node(state)
        assert result["intent_type"] == "search"


@pytest.mark.asyncio
async def test_intent_chitchat():
    """AC11.1: 意图识别 - 闲聊"""
    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value="chitchat")
        state = make_state(query="你好", session_id="s1")
        result = await intent_node(state)
        assert result["intent_type"] == "chitchat"


@pytest.mark.asyncio
async def test_retrieve_rank_node():
    """AC12.1: 检索+精排节点"""
    with patch("app.agent.nodes.search_service") as mock_svc:
        mock_svc.search = AsyncMock(return_value=[{"candidate_id": "c1", "score": 85.0}])
        state = make_state(query="Java 5年", session_id="s1")
        state["intent_type"] = "search"
        result = await retrieve_rank_node(state)
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["candidate_id"] == "c1"


@pytest.mark.asyncio
async def test_clarify_node():
    """澄清节点（候选人为空时引导）"""
    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value="请问您需要哪种技术栈的候选人？")
        state = make_state(query="找个候选人", session_id="s1")
        state["intent_type"] = "search"
        # candidates 为空（make_state 默认 []），触发澄清
        result = await clarify_node(state)
        assert "请问" in result["response"] or result["response"] != ""


@pytest.mark.asyncio
async def test_detail_node():
    """详情查询节点"""
    with patch("app.agent.nodes.resume_service") as mock_svc:
        mock_svc.get_detail = AsyncMock(return_value={"resume_id": "r1", "name": "张三"})
        state = make_state(query="c1 的详情", session_id="s1")
        state["intent_type"] = "detail"
        state["candidates"] = [{"candidate_id": "c1", "resume_id": "r1", "name": "张三"}]
        result = await detail_node(state)
        assert "detail" in result or "candidate" in result


@pytest.mark.asyncio
async def test_respond_node_chitchat():
    """响应节点 - 闲聊（流式）"""
    with patch("app.agent.nodes.llm_client") as mock_llm:

        async def fake_stream(*args, **kwargs):
            for tok in ["你", "好", "！"]:
                yield tok

        mock_llm.chat_stream = fake_stream
        state = make_state(query="你好", session_id="s1")
        state["intent_type"] = "chitchat"
        result = await respond_node(state)
        assert result["response"] != ""


@pytest.mark.asyncio
async def test_intent_node_returns_qa():
    """AC11.1: 意图识别 - qa 通用问答（HR 知识/系统使用/通用问答）"""
    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value="qa")
        state = make_state(query="HR 怎么筛选候选人", session_id="s1")
        result = await intent_node(state)
        assert result["intent_type"] == "qa"


@pytest.mark.asyncio
async def test_intent_node_fallback_to_qa_on_invalid():
    """意图识别返回非法值时应兜底为 qa（而非 chitchat）"""
    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value="invalid_intent")
        state = make_state(query="测试", session_id="s1")
        result = await intent_node(state)
        assert result["intent_type"] == "qa"


@pytest.mark.asyncio
async def test_intent_node_fallback_to_qa_on_exception():
    """意图识别 LLM 调用异常时应兜底为 qa"""
    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=Exception("LLM 调用失败"))
        state = make_state(query="测试", session_id="s1")
        result = await intent_node(state)
        assert result["intent_type"] == "qa"


@pytest.mark.asyncio
async def test_query_decompose_node_extracts_subqueries_and_filters():
    """query_decompose_node 应正确拆出 main_query/sub_queries/structured_filters"""
    from app.agent.nodes import query_decompose_node

    decompose_resp = json.dumps({
        "main_query": "后端工程师 Python Docker 3年经验",
        "sub_queries": ["后端工程师 Python Docker", "3年经验后端开发"],
        "structured_filters": {
            "required_skills": ["python", "docker"],
            "work_years_min": 3,
            "job_type": "后端"
        }
    }, ensure_ascii=False)

    state = {
        "query": "3年经验后端工程师会Python和Docker",
        "filters": {},
        "intent_type": "search",
    }
    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value=decompose_resp)
        result = await query_decompose_node(state)

    assert "decomposed" in result
    assert "filters" in result
    decomposed = result["decomposed"]
    assert decomposed["main_query"] == "后端工程师 Python Docker 3年经验"
    assert len(decomposed["sub_queries"]) == 2
    # filters 合并了 structured_filters
    filters = result["filters"]
    assert "python" in filters["required_skills"]
    assert "docker" in filters["required_skills"]
    assert filters["work_years_min"] == 3


@pytest.mark.asyncio
async def test_query_decompose_node_fallback_on_llm_failure():
    """LLM 失败时回退到 regex 提取 filters，decomposed 为空 dict"""
    from app.agent.nodes import query_decompose_node

    state = {
        "query": "会python的工程师",
        "filters": {},
        "intent_type": "search",
    }
    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=Exception("LLM 调用失败"))
        result = await query_decompose_node(state)

    # 兜底：filters 走 regex（python 应被提取）
    assert "python" in result["filters"].get("required_skills", [])
    # decomposed 为空 dict，不阻断流程
    assert result["decomposed"] == {}


@pytest.mark.asyncio
async def test_query_decompose_node_skips_non_search_intent():
    """非 search 意图不提取，直接返回原 filters"""
    from app.agent.nodes import query_decompose_node

    state = {
        "query": "你好",
        "filters": {"existing": "value"},
        "intent_type": "chitchat",
    }
    result = await query_decompose_node(state)
    assert result["filters"] == {"existing": "value"}
    assert result["decomposed"] == {}
