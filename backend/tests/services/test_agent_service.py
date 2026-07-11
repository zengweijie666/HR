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
         patch.object(svc, "_save_user_message", AsyncMock(return_value=None)), \
         patch.object(svc, "_save_assistant_message", AsyncMock(return_value={"title": None})):

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
         patch.object(svc, "_save_user_message", AsyncMock(return_value=None)), \
         patch.object(svc, "_save_assistant_message", AsyncMock(return_value={"title": None})):

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


@pytest.mark.asyncio
async def test_save_user_message_updates_title_on_first(svc):
    """首条消息应更新标题为 query 前 20 字"""
    # 模拟空 messages（首条）
    svc.sessions_coll.find_one = AsyncMock(return_value={"session_id": "s1", "messages": []})
    svc.sessions_coll.update_one = AsyncMock()

    title = await svc._save_user_message(
        session_id="s1",
        message_id="m1",
        query="推荐前端工程师熟悉Vue3和TypeScript",
    )

    # 验证返回标题
    expected_title = "推荐前端工程师熟悉Vue3和TypeScript"[:20]
    assert title == expected_title
    # 验证 update_one 被调用，且 $set 包含 title
    call_args = svc.sessions_coll.update_one.call_args
    update_doc = call_args.kwargs.get("update") or call_args.args[1]
    assert "$set" in update_doc
    assert "title" in update_doc["$set"]
    assert update_doc["$set"]["title"] == expected_title


@pytest.mark.asyncio
async def test_save_user_message_no_title_update_on_subsequent(svc):
    """非首条消息不应更新标题"""
    # 模拟已有消息（非首条）
    svc.sessions_coll.find_one = AsyncMock(return_value={
        "session_id": "s1",
        "messages": [{"role": "user", "content": "之前的问题"}]
    })
    svc.sessions_coll.update_one = AsyncMock()

    title = await svc._save_user_message(
        session_id="s1",
        message_id="m2",
        query="第二个问题",
    )

    assert title is None
    call_args = svc.sessions_coll.update_one.call_args
    update_doc = call_args.kwargs.get("update") or call_args.args[1]
    assert "$set" in update_doc
    assert "title" not in update_doc["$set"], "非首条消息不应更新标题"


@pytest.mark.asyncio
async def test_done_event_carries_title_on_first_message(svc):
    """首条消息的 done 事件应携带 title"""
    svc.sessions_coll.find_one = AsyncMock(return_value={
        "session_id": "s1", "messages": [], "user_id": "u1"
    })

    with patch("app.services.agent_service.intent_node", AsyncMock(return_value={"intent_type": "qa"})), \
         patch("app.services.agent_service.llm_client") as mock_llm:

        async def fake_stream(*args, **kwargs):
            yield "回答"

        mock_llm.chat_stream = fake_stream
        # _save_message 会真实调用，需 mock update_one
        svc.sessions_coll.update_one = AsyncMock()

        events = []
        async for sse_str in svc.send_message_stream(
            session_id="s1", user_id="u1", query="测试问题前20字"
        ):
            events.append(sse_str)
            if len(events) > 50:
                break

    # 找 done 事件
    done_events = [e for e in events if e.startswith("event: done")]
    assert len(done_events) > 0, "应有 done 事件"
    # 解析 data 验证含 title
    import json as _json
    data_line = [l for l in done_events[0].split("\n") if l.startswith("data: ")][0]
    payload = _json.loads(data_line[6:])
    assert payload.get("title") == "测试问题前20字", f"done 事件应携带 title，实际: {payload}"


@pytest.mark.asyncio
async def test_done_event_no_title_on_subsequent_message(svc):
    """非首条消息的 done 事件 title 应为 None"""
    svc.sessions_coll.find_one = AsyncMock(return_value={
        "session_id": "s1",
        "messages": [{"role": "user", "content": "之前的问题"}],
        "user_id": "u1"
    })

    with patch("app.services.agent_service.intent_node", AsyncMock(return_value={"intent_type": "qa"})), \
         patch("app.services.agent_service.llm_client") as mock_llm:

        async def fake_stream(*args, **kwargs):
            yield "回答"

        mock_llm.chat_stream = fake_stream
        svc.sessions_coll.update_one = AsyncMock()

        events = []
        async for sse_str in svc.send_message_stream(
            session_id="s1", user_id="u1", query="第二个问题"
        ):
            events.append(sse_str)
            if len(events) > 50:
                break

    done_events = [e for e in events if e.startswith("event: done")]
    assert len(done_events) > 0
    import json as _json
    data_line = [l for l in done_events[0].split("\n") if l.startswith("data: ")][0]
    payload = _json.loads(data_line[6:])
    assert payload.get("title") is None, f"非首条消息 done 事件 title 应为 None，实际: {payload}"


@pytest.mark.asyncio
async def test_compare_reuses_last_candidates_no_new_retrieval(svc):
    """compare 意图应复用历史 candidates，不触发新检索

    业务场景: 用户先搜索NLP工程师得到候选人列表，然后说"对比李志鹏和温佳蕊"，
    应该从历史列表中取两人对比，而不是用"对比李志鹏和温佳蕊"做新的向量检索。
    """
    last_candidates = [
        {"candidate_id": "c1", "name": "毛光铭", "work_years": 4, "skills": ["BERT", "NLP"], "score": 83},
        {"candidate_id": "c2", "name": "李志鹏", "work_years": 0, "skills": ["BERT", "FastText"], "score": 75},
        {"candidate_id": "c3", "name": "温佳蕊", "work_years": 1, "skills": ["BERT", "FastText", "NLP"], "score": 72},
    ]
    svc.sessions_coll.find_one = AsyncMock(return_value={
        "session_id": "s1",
        "messages": [
            {"role": "user", "content": "帮我找一些nlp方向的工程师"},
            {"role": "assistant", "content": "找到3位候选人", "candidates": last_candidates},
        ],
        "user_id": "u1",
    })

    retrieve_called = {"value": False}

    async def mock_retrieve(state):
        retrieve_called["value"] = True
        return {**state, "candidates": []}

    with patch("app.services.agent_service.intent_node", AsyncMock(return_value={"intent_type": "compare"})), \
         patch("app.services.agent_service.retrieve_rank_node", mock_retrieve), \
         patch("app.services.agent_service.llm_client") as mock_llm, \
         patch.object(svc, "_save_user_message", AsyncMock(return_value=None)), \
         patch.object(svc, "_save_assistant_message", AsyncMock(return_value={"title": None})):

        async def fake_stream(*args, **kwargs):
            yield "对比结果"

        mock_llm.chat_stream = fake_stream
        events = []
        async for sse_str in svc.send_message_stream(
            session_id="s1", user_id="u1", query="对比李志鹏和温佳蕊"
        ):
            events.append(sse_str)
            if len(events) > 50:
                break

    assert not retrieve_called["value"], "compare 不应触发新检索"
    event_types = [e.split(":", 1)[1].split("\n", 1)[0].strip() for e in events if e.startswith("event:")]
    assert "candidates" in event_types, "compare 应 yield candidates 事件（复用历史）"
    assert "retrieval" not in event_types, "compare 不应有 retrieval 事件"


def test_extract_names_from_query():
    """_extract_names_from_query 应正确提取中文姓名"""
    result = AgentService._extract_names_from_query("对比李志鹏和温佳蕊")
    assert "李志鹏" in result
    assert "温佳蕊" in result


def test_match_candidates_by_query():
    """_match_candidates_by_query 应根据查询中的姓名匹配候选人"""
    candidates = [
        {"candidate_id": "c1", "name": "毛光铭", "score": 83},
        {"candidate_id": "c2", "name": "李志鹏", "score": 75},
        {"candidate_id": "c3", "name": "温佳蕊", "score": 72},
    ]
    matched = AgentService._match_candidates_by_query("对比李志鹏和温佳蕊", candidates)
    names = [c["name"] for c in matched]
    assert "李志鹏" in names
    assert "温佳蕊" in names
    assert "毛光铭" not in names


def test_match_candidates_exact_name_no_partial():
    """精确全名匹配：短词不应误匹配长名字（如'李志'不应匹配'李志鹏'）"""
    candidates = [
        {"candidate_id": "c1", "name": "李志鹏", "score": 75},
        {"candidate_id": "c2", "name": "李志", "score": 80},
        {"candidate_id": "c3", "name": "温佳蕊", "score": 72},
    ]
    # 查询中有"李志鹏"全名，应精确匹配李志鹏，不应匹配"李志"
    matched = AgentService._match_candidates_by_query("对比李志鹏和温佳蕊", candidates)
    names = [c["name"] for c in matched]
    assert "李志鹏" in names
    assert "温佳蕊" in names
    assert "李志" not in names, "'李志'不应被子串匹配误命中"


def test_match_candidates_direct_query():
    """直接从原始 query 查找候选人全名（最可靠路径）"""
    candidates = [
        {"candidate_id": "c1", "name": "张三", "score": 90},
        {"candidate_id": "c2", "name": "李四", "score": 80},
    ]
    matched = AgentService._match_candidates_by_query("张三的详情", candidates)
    assert len(matched) == 1
    assert matched[0]["name"] == "张三"


def test_extract_last_candidates():
    """_extract_last_candidates 应从历史中提取最近一次 assistant 的 candidates"""
    history = [
        {"role": "user", "content": "前端"},
        {"role": "assistant", "content": "回答1", "candidates": [{"name": "A"}, {"name": "B"}]},
        {"role": "user", "content": "对比A和B"},
        {"role": "assistant", "content": "对比回答", "candidates": [{"name": "A"}, {"name": "B"}, {"name": "C"}]},
    ]
    result = AgentService._extract_last_candidates(history)
    assert len(result) == 3
    assert result[0]["name"] == "A"


def test_extract_last_candidates_empty():
    """历史无 candidates 时返回空列表"""
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！"},
    ]
    result = AgentService._extract_last_candidates(history)
    assert result == []


@pytest.mark.asyncio
async def test_qa_with_candidates_context(svc):
    """qa 意图有历史候选人时应带上候选人数据作为上下文，不触发新检索

    业务场景: 用户先搜索NLP得到候选人，然后问"为什么李志鹏评分比温佳蕊高"，
    这是 qa 意图但应该能看到候选人评分数据来解释，而不是给套话。
    """
    last_candidates = [
        {"candidate_id": "c1", "name": "李志鹏", "work_years": 0, "skills": ["BERT"], "score": 75, "score_detail": {"skill": 80, "experience": 50}},
        {"candidate_id": "c2", "name": "温佳蕊", "work_years": 1, "skills": ["BERT", "NLP"], "score": 72, "score_detail": {"skill": 70, "experience": 70}},
    ]
    svc.sessions_coll.find_one = AsyncMock(return_value={
        "session_id": "s1",
        "messages": [
            {"role": "user", "content": "找NLP工程师"},
            {"role": "assistant", "content": "找到候选人", "candidates": last_candidates},
        ],
        "user_id": "u1",
    })

    retrieve_called = {"value": False}
    passed_messages = {"value": None}

    async def mock_retrieve(state):
        retrieve_called["value"] = True
        return {**state, "candidates": []}

    with patch("app.services.agent_service.intent_node", AsyncMock(return_value={"intent_type": "qa"})), \
         patch("app.services.agent_service.retrieve_rank_node", mock_retrieve), \
         patch("app.services.agent_service.llm_client") as mock_llm, \
         patch.object(svc, "_save_user_message", AsyncMock(return_value=None)), \
         patch.object(svc, "_save_assistant_message", AsyncMock(return_value={"title": None})):

        async def fake_stream(messages, **kwargs):
            passed_messages["value"] = messages
            yield "因为..."

        mock_llm.chat_stream = fake_stream
        events = []
        async for sse_str in svc.send_message_stream(
            session_id="s1", user_id="u1", query="为什么李志鹏评分比温佳蕊高"
        ):
            events.append(sse_str)
            if len(events) > 50:
                break

    assert not retrieve_called["value"], "qa 不应触发新检索"
    event_types = [e.split(":", 1)[1].split("\n", 1)[0].strip() for e in events if e.startswith("event:")]
    assert "retrieval" not in event_types
    # qa 有历史候选人时应带 candidates 事件
    assert "candidates" in event_types, "qa 有历史候选人时应 yield candidates 事件"
    # system prompt 应包含候选人数据
    sys_msg = passed_messages["value"][0]["content"]
    assert "李志鹏" in sys_msg, "qa system prompt 应包含候选人数据以便解释评分差异"
    assert "温佳蕊" in sys_msg
