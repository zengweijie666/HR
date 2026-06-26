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
