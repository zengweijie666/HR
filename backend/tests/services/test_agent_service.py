"""
文件名: tests/services/test_agent_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: AgentService 单元测试（会话 CRUD + SSE 流式）
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.agent_service import AgentService


@pytest.fixture
def svc():
    s = AgentService()
    # motor find() 同步返回 cursor，用 MagicMock
    s.sessions_coll = MagicMock()
    s.sessions_coll.insert_one = AsyncMock()
    s.sessions_coll.delete_one = AsyncMock()
    s.sessions_coll.find_one = AsyncMock()
    s.sessions_coll.count_documents = AsyncMock(return_value=0)
    s.sessions_coll.update_one = AsyncMock()
    return s


@pytest.mark.asyncio
async def test_create_session(svc):
    """AC10.1: 创建会话"""
    result = await svc.create_session(user_id="u1", title="测试会话")
    assert "session_id" in result
    assert result["title"] == "测试会话"
    svc.sessions_coll.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_get_sessions(svc):
    """AC10.2: 会话列表"""
    svc.sessions_coll.find.return_value.sort.return_value.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=[
        {"session_id": "s1", "title": "会话1", "updated_at": "2026-06-26T10:00:00Z"}
    ])
    svc.sessions_coll.count_documents = AsyncMock(return_value=1)
    result = await svc.get_sessions(user_id="u1", page=1, page_size=20)
    assert result["total"] == 1
    assert result["list"][0]["session_id"] == "s1"


@pytest.mark.asyncio
async def test_get_messages(svc):
    """AC10.3: 会话消息历史"""
    svc.sessions_coll.find_one = AsyncMock(return_value={
        "session_id": "s1", "messages": [{"message_id": "m1", "role": "user", "content": "你好"}]
    })
    result = await svc.get_messages("s1")
    assert len(result) == 1
    assert result[0]["message_id"] == "m1"


@pytest.mark.asyncio
async def test_delete_session(svc):
    """AC10.4: 删除会话"""
    await svc.delete_session("s1")
    svc.sessions_coll.delete_one.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_stream(svc):
    """AC12.1-12.3: SSE 流式响应"""
    svc.sessions_coll.find_one = AsyncMock(return_value={
        "session_id": "s1", "messages": [], "user_id": "u1"
    })
    events = []
    with patch("app.services.agent_service.intent_node", AsyncMock(return_value={"intent_type": "chitchat"})), \
         patch("app.services.agent_service.llm_client") as mock_llm:

        async def fake_stream(*args, **kwargs):
            for tok in ["你好", "！"]:
                yield tok

        mock_llm.chat_stream = fake_stream
        async for sse_str in svc.send_message_stream(
            session_id="s1", user_id="u1", query="你好"
        ):
            events.append(sse_str)
            if len(events) > 50:
                break
    # SSE 字符串以 "event: <type>\n..." 开头
    event_types = [e.split(":", 1)[1].split("\n", 1)[0].strip() for e in events if e.startswith("event:")]
    assert "intent" in event_types or "done" in event_types or "error" in event_types


@pytest.mark.asyncio
async def test_send_message_stream_qa_branch_skips_retrieval(svc):
    """qa 意图应跳过检索，不触发 retrieve_rank_node"""
    svc.sessions_coll.find_one = AsyncMock(return_value={
        "session_id": "s1", "messages": [], "user_id": "u1"
    })

    retrieve_called = {"value": False}

    async def mock_retrieve(state):
        retrieve_called["value"] = True
        return {**state, "candidates": []}

    with patch("app.services.agent_service.intent_node", AsyncMock(return_value={"intent_type": "qa"})), \
         patch("app.services.agent_service.retrieve_rank_node", mock_retrieve), \
         patch("app.services.agent_service.llm_client") as mock_llm, \
         patch.object(svc, "_save_message", AsyncMock()):

        async def fake_stream(*args, **kwargs):
            for tok in ["这是", "通用", "回答"]:
                yield tok

        mock_llm.chat_stream = fake_stream
        events = []
        async for sse_str in svc.send_message_stream(
            session_id="s1", user_id="u1", query="HR 怎么筛选候选人"
        ):
            events.append(sse_str)
            if len(events) > 50:
                break

    # qa 分支不应触发检索
    assert not retrieve_called["value"], "qa 分支不应触发检索"
    # 应有 token 事件
    event_types = [e.split(":", 1)[1].split("\n", 1)[0].strip() for e in events if e.startswith("event:")]
    assert "token" in event_types, "qa 分支应有 token 事件"
    assert "done" in event_types, "应有 done 事件"
    # 不应有 retrieval/candidates 事件
    assert "retrieval" not in event_types, "qa 分支不应有 retrieval 事件"
    assert "candidates" not in event_types, "qa 分支不应有 candidates 事件"


@pytest.mark.asyncio
async def test_retrieve_empty_yields_candidates_event(svc):
    """检索返回空列表时仍应 yield candidates 事件（空数组），便于前端区分'没触发检索'和'检索为空'"""
    svc.sessions_coll.find_one = AsyncMock(return_value={
        "session_id": "s1", "messages": [], "user_id": "u1"
    })

    async def mock_retrieve(state):
        return {**state, "candidates": []}  # 空列表

    with patch("app.services.agent_service.intent_node", AsyncMock(return_value={"intent_type": "search"})), \
         patch("app.services.agent_service.retrieve_rank_node", mock_retrieve), \
         patch("app.services.agent_service.llm_client") as mock_llm, \
         patch.object(svc, "_save_message", AsyncMock()):

        async def fake_stream(*args, **kwargs):
            yield "未找到匹配候选人"

        mock_llm.chat_stream = fake_stream
        events = []
        async for sse_str in svc.send_message_stream(
            session_id="s1", user_id="u1", query="推荐不存在的岗位"
        ):
            events.append(sse_str)
            if len(events) > 50:
                break

    # 应包含 candidates 事件（即使为空数组）
    candidates_events = [e for e in events if e.startswith("event: candidates")]
    assert len(candidates_events) > 0, "检索为空也应 yield candidates 事件"
    # 解析 data 验证为空数组
    import json as _json
    data_line = [l for l in candidates_events[0].split("\n") if l.startswith("data: ")][0]
    payload = _json.loads(data_line[6:])
    assert payload == [], f"candidates 事件 data 应为空数组，实际: {payload}"
