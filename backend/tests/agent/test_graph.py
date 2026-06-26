"""
文件名: tests/agent/test_graph.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: LangGraph 图定义单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.agent.graph import build_graph
from app.agent.state import make_state


@pytest.mark.asyncio
async def test_graph_chitchat():
    """闲聊路径: intent → respond"""
    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value="chitchat")

        async def fake_stream(*args, **kwargs):
            for tok in ["你好"]:
                yield tok

        mock_llm.chat_stream = fake_stream
        graph = build_graph()
        state = make_state(query="你好", session_id="s1")
        result = await graph.ainvoke(state)
        assert result["intent_type"] == "chitchat"
        assert result["response"] != ""


@pytest.mark.asyncio
async def test_graph_search():
    """搜索路径: intent → retrieve_rank → respond"""
    with patch("app.agent.nodes.llm_client") as mock_llm, \
         patch("app.agent.nodes.search_service") as mock_svc:
        mock_llm.chat = AsyncMock(return_value="search")
        mock_svc.search = AsyncMock(return_value=[{"candidate_id": "c1", "name": "张三", "score": 85}])

        async def fake_stream(*args, **kwargs):
            for tok in ["推荐", "张三"]:
                yield tok

        mock_llm.chat_stream = fake_stream
        graph = build_graph()
        state = make_state(query="Java 5年", session_id="s1")
        result = await graph.ainvoke(state)
        assert result["intent_type"] == "search"
        assert len(result["candidates"]) == 1
