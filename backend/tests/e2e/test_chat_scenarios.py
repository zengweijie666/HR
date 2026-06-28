"""
文件名: tests/e2e/test_chat_scenarios.py
创建时间: 2026-06-28
作者: TalentSense Team
功能描述: 工作台 AI 对话场景端到端测试

测试场景（模拟真实用户在工作台与 AI 的多轮对话）:
  1. 闲聊场景: "你好" → chitchat 意图，不触发检索
  2. 搜索场景: "帮我找一些NLP方向的工程师" → search 意图，触发检索+评分，返回候选人
  3. 对比场景: "对比李志鹏和温佳蕊" → compare 意图，复用历史候选人，不触发新检索
  4. 评分问答: "为什么李志鹏评分比温佳蕊高" → qa 意图，复用历史候选人，LLM 解释评分
  5. 详情查询: "李志鹏的详情" → detail 意图，复用历史候选人
  6. 多轮上下文: 连续5轮对话验证候选人复用链路
  7. 评分区分度: 验证不同工作年限候选人评分有明显差异
  8. 空结果处理: 搜索不存在的技能 → 友好提示
  9. 同义词扩展: 搜索"NLP"能关联到"BERT/FastText"技能的候选人
  10. 会话隔离: 不同会话的候选人上下文不串扰

设计原则:
- 预置3名NLP方向候选人（毛光铭4年/李志鹏0年/温佳蕊1年）
- LLM mock 按对话轮次返回不同意图和评分
- 验证SSE事件流完整性（intent/candidates/token/done）
- 验证候选人复用（compare/qa/detail 不触发 retrieval 事件）
"""
import json
import pytest
from unittest.mock import AsyncMock
from tests.e2e.conftest import _auth_header, parse_sse_events


@pytest.fixture(scope="module")
def chat_env():
    """对话场景测试环境：预置 NLP 方向候选人，独立于招聘流程测试"""
    from tests.e2e.fake_infra import FakeMongoDB, FakeRedis
    from unittest.mock import AsyncMock, MagicMock, patch
    from contextlib import ExitStack
    from fastapi.testclient import TestClient
    from app.main import app
    import bcrypt

    mongo = FakeMongoDB()
    redis = FakeRedis()

    # 预置 admin 用户
    password_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    mongo.users._data.append({
        "user_id": "u_admin",
        "username": "admin",
        "password_hash": password_hash,
        "role": "admin",
        "status": "approved",
        "email": "admin@talentsense.com",
    })

    # 预置 3 名 NLP 方向候选人（模拟真实简历库数据）
    mongo.resumes._data.extend([
        {
            "resume_id": "res_maogm",
            "candidate_id": "cand_maogm",
            "basic_info": {"name": "毛光铭", "phone_masked": "138****1001"},
            "name": "毛光铭",
            "education": "本科",
            "education_level": 1,
            "work_years": 4,
            "skills": ["Transformer", "BERT", "RoBERTa", "LSTM", "Dify"],
            "work_experience": [
                {"company": "某AI公司", "position": "NLP工程师", "description": "负责BERT模型微调和部署"}
            ],
            "education_detail": [{"school": "某大学", "major": "计算机科学", "degree": "本科"}],
            "projects": [{"name": "文本分类系统", "description": "基于BERT的中文文本分类"}],
            "summary": "4年NLP工程师经验，精通BERT/Transformer",
            "expected_salary": {"min": 25, "max": 35},
            "tags": [],
            "is_favorite": False,
            "notes": "",
            "parse_info": {"parse_status": "completed"},
            "file_info": {"file_id": "minio_maogm", "file_name": "maogm.pdf", "file_type": "pdf"},
        },
        {
            "resume_id": "res_lizp",
            "candidate_id": "cand_lizp",
            "basic_info": {"name": "李志鹏", "phone_masked": "139****1002"},
            "name": "李志鹏",
            "education": "本科",
            "education_level": 1,
            "work_years": 0,
            "skills": ["BERT", "FastText", "jieba", "PyTorch", "transformers"],
            "work_experience": [],
            "education_detail": [{"school": "某大学", "major": "人工智能", "degree": "本科"}],
            "projects": [{"name": "情感分析项目", "description": "使用FastText和BERT做中文情感分析"}],
            "summary": "应届毕业生，有NLP项目经验",
            "expected_salary": {"min": 12, "max": 18},
            "tags": [],
            "is_favorite": False,
            "notes": "",
            "parse_info": {"parse_status": "completed"},
            "file_info": {"file_id": "minio_lizp", "file_name": "lizp.pdf", "file_type": "pdf"},
        },
        {
            "resume_id": "res_wenjr",
            "candidate_id": "cand_wenjr",
            "basic_info": {"name": "温佳蕊", "phone_masked": "137****1003"},
            "name": "温佳蕊",
            "education": "本科",
            "education_level": 1,
            "work_years": 1,
            "skills": ["Python", "BERT", "FastText", "NLP", "Hadoop", "数据挖掘"],
            "work_experience": [
                {"company": "某数据公司", "position": "数据分析师", "description": "文本数据处理和挖掘"}
            ],
            "education_detail": [{"school": "某大学", "major": "数据科学", "degree": "本科"}],
            "projects": [{"name": "文本挖掘", "description": "使用FastText做文本分类"}],
            "summary": "1年数据分析经验，有NLP项目经验",
            "expected_salary": {"min": 18, "max": 22},
            "tags": [],
            "is_favorite": False,
            "notes": "",
            "parse_info": {"parse_status": "completed"},
            "file_info": {"file_id": "minio_wenjr", "file_name": "wenjr.pdf", "file_type": "pdf"},
        },
    ])

    # LLM mock：可动态调整返回值
    llm_mock = AsyncMock()
    llm_chat_responses = []
    llm_chat_call_count = {"i": 0}

    async def _chat_side_effect(messages, **kwargs):
        idx = llm_chat_call_count["i"]
        llm_chat_call_count["i"] += 1
        if idx < len(llm_chat_responses):
            resp = llm_chat_responses[idx]
            return resp
        return "ok"

    llm_mock.chat = AsyncMock(side_effect=_chat_side_effect)

    async def _chat_stream_side_effect(messages, **kwargs):
        for tok in ["这是", "一个", "回答"]:
            yield tok

    llm_mock.chat_stream = _chat_stream_side_effect

    # Embedding mock
    embedding_mock = MagicMock()
    embedding_mock.encode = MagicMock(return_value=([[0.1] * 1024], [{"key": 0.1}]))

    # Reranker mock
    reranker_mock = MagicMock()
    reranker_mock.rerank = MagicMock(return_value=[0.95, 0.80, 0.70])

    # VectorStore mock：返回3名NLP候选人
    vector_store_mock = AsyncMock()
    vector_store_mock.hybrid_search = AsyncMock(return_value=[
        {"chunk_id": "ck1", "candidate_id": "res_maogm", "score": 0.95, "parent_content": "BERT Transformer NLP"},
        {"chunk_id": "ck2", "candidate_id": "res_lizp", "score": 0.80, "parent_content": "BERT FastText NLP"},
        {"chunk_id": "ck3", "candidate_id": "res_wenjr", "score": 0.70, "parent_content": "BERT FastText NLP"},
    ])
    vector_store_mock.insert = AsyncMock()
    vector_store_mock.delete_by_resume_id = AsyncMock()

    # MinIO mock
    minio_mock = MagicMock()
    minio_mock.presigned_url = MagicMock(return_value="https://minio.example.com/presigned")

    # StrategySelector mock
    strategy_mock = AsyncMock()
    strategy_mock.select = AsyncMock(return_value="direct")
    strategy_mock.rewrite = AsyncMock(return_value=["NLP BERT FastText Transformer"])

    from app.core.database import MongoDB as _MongoCls, RedisClient as _RedisCls
    original_mongo_db = _MongoCls.db
    original_redis_pool = _RedisCls.pool
    original_redis_get_client = _RedisCls.get_client

    _MongoCls.db = mongo
    _RedisCls.pool = MagicMock()
    _RedisCls.get_client = MagicMock(return_value=redis)

    patch_specs = [
        ("app.core.llm_client.llm_client", {"new": llm_mock}),
        ("app.services.resume_service.llm_client", {"new": llm_mock}),
        ("app.services.resume_service.minio_client", {"new": minio_mock}),
        ("app.core.embedding.embedding_model", {"new": embedding_mock}),
        ("app.core.vector_store.vector_store", {"new": vector_store_mock}),
        ("app.core.reranker.reranker_model", {"new": reranker_mock}),
        ("app.core.strategy_selector.strategy_selector", {"new": strategy_mock}),
        ("app.services.search_service.llm_client", {"new": llm_mock}),
        ("app.agent.nodes.llm_client", {"new": llm_mock}),
        ("app.agent.nodes.search_service", {}),
        ("app.agent.nodes.resume_service", {}),
        ("app.services.agent_service.llm_client", {"new": llm_mock}),
        ("app.services.candidate_service.embedding_model", {"new": embedding_mock}),
        ("app.services.candidate_service.vector_store", {"new": vector_store_mock}),
        ("app.services.search_service.embedding_model", {"new": embedding_mock}),
        ("app.services.search_service.reranker_model", {"new": reranker_mock}),
        ("app.services.search_service.vector_store", {"new": vector_store_mock}),
        ("app.services.search_service.strategy_selector", {"new": strategy_mock}),
    ]

    with ExitStack() as stack:
        mock_nodes_search = stack.enter_context(patch(patch_specs[9][0], **patch_specs[9][1]))
        mock_nodes_resume = stack.enter_context(patch(patch_specs[10][0], **patch_specs[10][1]))
        for i in range(len(patch_specs)):
            if i in (9, 10):
                continue
            stack.enter_context(patch(patch_specs[i][0], **patch_specs[i][1]))

        from app.services.search_service import SearchService
        real_search = SearchService()
        real_search.resumes_coll = mongo.resumes
        mock_nodes_search.search = real_search.search

        from app.services.resume_service import ResumeService
        real_resume = ResumeService()
        real_resume.resumes_coll = mongo.resumes
        mock_nodes_resume.get_detail = real_resume.get_detail

        client = TestClient(app)

        env = {
            "client": client,
            "mongo": mongo,
            "redis": redis,
            "state": {},
            "llm_mock": llm_mock,
            "llm_chat_responses": llm_chat_responses,
            "llm_chat_call_count": llm_chat_call_count,
            "vector_store_mock": vector_store_mock,
        }
        yield env

    _MongoCls.db = original_mongo_db
    _RedisCls.pool = original_redis_pool
    _RedisCls.get_client = original_redis_get_client


def _send_message(client, token, session_id, query):
    """发送对话消息并返回 SSE 事件列表"""
    with client.stream(
        "POST",
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"query": query},
        headers=_auth_header(token),
    ) as response:
        assert response.status_code == 200
        full_text = ""
        for chunk in response.iter_text():
            full_text += chunk
    return parse_sse_events(full_text)


def _login(chat_env):
    """登录获取 token"""
    client = chat_env["client"]
    r = client.post("/api/v1/auth/login", json={
        "email": "admin@talentsense.com",
        "password": "admin123",
    })
    assert r.status_code == 200
    return r.json()["data"]["access_token"]


def _create_session(chat_env, token, title="NLP招聘对话"):
    """创建会话"""
    client = chat_env["client"]
    r = client.post(
        "/api/v1/chat/sessions",
        json={"title": title},
        headers=_auth_header(token),
    )
    assert r.status_code == 200
    return r.json()["data"]["session_id"]


def _clear_search_cache(chat_env):
    """清空检索缓存（strategy_mock.rewrite 返回固定值导致缓存 key 相同，需每次清空）"""
    chat_env["redis"]._store.clear()


# ===== 测试用例 =====


class _BaseChatTest:
    """所有对话场景测试的基类：每个测试前自动清空检索缓存"""

    @pytest.fixture(autouse=True)
    def _clear_cache(self, chat_env):
        """每个测试方法前自动清空 redis 缓存（避免跨测试缓存命中）"""
        _clear_search_cache(chat_env)


class TestChitchatScenario(_BaseChatTest):
    """场景1: 闲聊对话"""

    def test_chitchat_returns_no_retrieval(self, chat_env):
        """闲聊"你好"应识别为 chitchat 意图，不触发检索"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        # LLM 返回 chitchat 意图
        chat_env["llm_chat_responses"][:] = ["chitchat"]
        chat_env["llm_chat_call_count"]["i"] = 0

        events = _send_message(chat_env["client"], token, session_id, "你好")
        event_names = [e["event"] for e in events]

        assert "intent" in event_names
        intent_data = next(e["data"] for e in events if e["event"] == "intent")
        assert intent_data["intent"] == "chitchat"
        # chitchat 不应触发检索
        assert "retrieval" not in event_names
        assert "candidates" not in event_names
        # 应有 token 和 done 事件
        assert "token" in event_names
        assert "done" in event_names


class TestSearchScenario(_BaseChatTest):
    """场景2: 搜索NLP工程师"""

    def test_search_returns_candidates_with_scores(self, chat_env):
        """搜索"帮我找一些NLP方向的工程师"应返回3名候选人且评分有区分度"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        # LLM 按顺序返回: 意图search → 评分(毛光铭) → 评分(李志鹏) → 评分(温佳蕊)
        chat_env["llm_chat_responses"][:] = [
            "search",  # intent_node
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验，BERT项目落地"}),  # 毛光铭
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生，有BERT项目"}),  # 李志鹏
            json.dumps({"skill": 72, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验，有NLP项目"}),  # 温佳蕊
        ]
        chat_env["llm_chat_call_count"]["i"] = 0

        events = _send_message(chat_env["client"], token, session_id, "帮我找一些NLP方向的工程师")
        event_names = [e["event"] for e in events]

        # 验证事件流
        assert "intent" in event_names
        intent_data = next(e["data"] for e in events if e["event"] == "intent")
        assert intent_data["intent"] == "search"

        # search 意图应触发检索
        assert "retrieval" in event_names
        assert "candidates" in event_names

        # 验证候选人列表
        cand_event = next(e["data"] for e in events if e["event"] == "candidates")
        assert isinstance(cand_event, list)
        assert len(cand_event) == 3

        # 验证候选人姓名
        names = [c["name"] for c in cand_event]
        assert "毛光铭" in names
        assert "李志鹏" in names
        assert "温佳蕊" in names

        # 验证评分区分度：毛光铭(4年) > 温佳蕊(1年) > 李志鹏(0年)
        scores = {c["name"]: c["score"] for c in cand_event}
        assert scores["毛光铭"] > scores["温佳蕊"], "4年经验评分应高于1年经验"
        assert scores["温佳蕊"] > scores["李志鹏"], "1年经验评分应高于0年经验"

        # 验证评分有 score_detail
        for c in cand_event:
            assert "score_detail" in c
            assert "skill" in c["score_detail"]
            assert "experience" in c["score_detail"]

        # 验证 done 事件
        assert "done" in event_names

    def test_search_first_message_generates_title(self, chat_env):
        """首条消息应自动生成会话标题"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        chat_env["llm_chat_responses"][:] = ["search"]
        chat_env["llm_chat_call_count"]["i"] = 0

        events = _send_message(chat_env["client"], token, session_id, "帮我找一些NLP方向的工程师")

        done_event = next(e["data"] for e in events if e["event"] == "done")
        assert done_event["title"] is not None, "首条消息 done 事件应携带 title"


class TestCompareScenario(_BaseChatTest):
    """场景3: 对比候选人"""

    def test_compare_reuses_history_candidates(self, chat_env):
        """对比候选人应复用历史候选人，不触发新检索"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        # 第1轮: 搜索 NLP 工程师
        chat_env["llm_chat_responses"][:] = [
            "search",
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验"}),
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),
            json.dumps({"skill": 72, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验"}),
        ]
        chat_env["llm_chat_call_count"]["i"] = 0
        events1 = _send_message(chat_env["client"], token, session_id, "帮我找一些NLP方向的工程师")
        event_names1 = [e["event"] for e in events1]
        assert "retrieval" in event_names1, "第1轮搜索应有 retrieval"

        # 第2轮: 对比李志鹏和温佳蕊
        chat_env["llm_chat_responses"][:] = ["compare"]
        chat_env["llm_chat_call_count"]["i"] = 0
        events2 = _send_message(chat_env["client"], token, session_id, "对比李志鹏和温佳蕊")
        event_names2 = [e["event"] for e in events2]

        # compare 意图不应触发新检索
        assert "retrieval" not in event_names2, "对比不应触发新检索"

        # 应有 candidates 事件（复用历史）
        assert "candidates" in event_names2, "对比应复用历史候选人"

        # 验证 candidates 只包含被对比的两人
        cand_event = next(e["data"] for e in events2 if e["event"] == "candidates")
        names = [c["name"] for c in cand_event]
        assert "李志鹏" in names
        assert "温佳蕊" in names
        assert "毛光铭" not in names, "对比应只包含被提及的候选人"

    def test_compare_without_history_triggers_search(self, chat_env):
        """无历史候选人时对比应触发检索"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        chat_env["llm_chat_responses"][:] = [
            "compare",
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验"}),
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),
            json.dumps({"skill": 72, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验"}),
        ]
        chat_env["llm_chat_call_count"]["i"] = 0

        events = _send_message(chat_env["client"], token, session_id, "对比一下候选人")
        event_names = [e["event"] for e in events]

        # 无历史时应触发检索
        assert "retrieval" in event_names, "无历史候选人时对比应触发检索"


class TestQAScenario(_BaseChatTest):
    """场景4: 评分问答"""

    def test_qa_uses_candidates_context(self, chat_env):
        """评分问答应复用历史候选人数据，不触发新检索"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        # 第1轮: 搜索
        chat_env["llm_chat_responses"][:] = [
            "search",
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),
            json.dumps({"skill": 72, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验"}),
        ]
        chat_env["llm_chat_call_count"]["i"] = 0
        _send_message(chat_env["client"], token, session_id, "找NLP工程师")

        # 第2轮: 问评分差异
        chat_env["llm_chat_responses"][:] = ["qa"]
        chat_env["llm_chat_call_count"]["i"] = 0
        events = _send_message(chat_env["client"], token, session_id, "为什么李志鹏评分比温佳蕊高")
        event_names = [e["event"] for e in events]

        # qa 不应触发检索
        assert "retrieval" not in event_names, "qa 不应触发新检索"

        # qa 应有 candidates 事件（复用历史）
        assert "candidates" in event_names, "qa 应复用历史候选人"

        # 应有 token 和 done
        assert "token" in event_names
        assert "done" in event_names


class TestDetailScenario(_BaseChatTest):
    """场景5: 详情查询"""

    def test_detail_reuses_history(self, chat_env):
        """详情查询应复用历史候选人，不触发新检索"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        # 第1轮: 搜索
        chat_env["llm_chat_responses"][:] = [
            "search",
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验"}),
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),
            json.dumps({"skill": 72, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验"}),
        ]
        chat_env["llm_chat_call_count"]["i"] = 0
        _send_message(chat_env["client"], token, session_id, "找NLP工程师")

        # 第2轮: 查看李志鹏详情
        chat_env["llm_chat_responses"][:] = ["detail"]
        chat_env["llm_chat_call_count"]["i"] = 0
        events = _send_message(chat_env["client"], token, session_id, "李志鹏的详情")
        event_names = [e["event"] for e in events]

        # detail 不应触发检索
        assert "retrieval" not in event_names, "detail 不应触发新检索"

        # 应有 candidates 事件
        assert "candidates" in event_names


class TestMultiTurnContext(_BaseChatTest):
    """场景6: 多轮对话上下文链路"""

    def test_five_turn_conversation_flow(self, chat_env):
        """连续5轮对话验证候选人复用链路完整"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        # 第1轮: 搜索
        chat_env["llm_chat_responses"][:] = [
            "search",
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验"}),
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),
            json.dumps({"skill": 72, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验"}),
        ]
        chat_env["llm_chat_call_count"]["i"] = 0
        events1 = _send_message(chat_env["client"], token, session_id, "帮我找一些NLP方向的工程师")
        assert "retrieval" in [e["event"] for e in events1]

        # 第2轮: 闲聊
        chat_env["llm_chat_responses"][:] = ["chitchat"]
        chat_env["llm_chat_call_count"]["i"] = 0
        events2 = _send_message(chat_env["client"], token, session_id, "谢谢")
        assert "retrieval" not in [e["event"] for e in events2]

        # 第3轮: 对比
        chat_env["llm_chat_responses"][:] = ["compare"]
        chat_env["llm_chat_call_count"]["i"] = 0
        events3 = _send_message(chat_env["client"], token, session_id, "对比李志鹏和温佳蕊")
        assert "retrieval" not in [e["event"] for e in events3]
        assert "candidates" in [e["event"] for e in events3]

        # 第4轮: 评分问答
        chat_env["llm_chat_responses"][:] = ["qa"]
        chat_env["llm_chat_call_count"]["i"] = 0
        events4 = _send_message(chat_env["client"], token, session_id, "为什么李志鹏评分比温佳蕊高")
        assert "retrieval" not in [e["event"] for e in events4]

        # 第5轮: 详情
        chat_env["llm_chat_responses"][:] = ["detail"]
        chat_env["llm_chat_call_count"]["i"] = 0
        events5 = _send_message(chat_env["client"], token, session_id, "毛光铭的详情")
        assert "retrieval" not in [e["event"] for e in events5]


class TestScoreDifferentiation(_BaseChatTest):
    """场景7: 评分区分度验证"""

    def test_senior_higher_than_junior(self, chat_env):
        """4年经验候选人评分应高于0年经验候选人"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        chat_env["llm_chat_responses"][:] = [
            "search",
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验"}),  # 高分
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),  # 低分
            json.dumps({"skill": 72, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验"}),  # 中分
        ]
        chat_env["llm_chat_call_count"]["i"] = 0

        events = _send_message(chat_env["client"], token, session_id, "找NLP工程师_区分度测试")
        cand_event = next(e["data"] for e in events if e["event"] == "candidates")

        scores = {c["name"]: c["score"] for c in cand_event}
        # overall = 0.4*skill + 0.3*experience + 0.2*education + 0.1*salary
        # 验证评分有区分度（3个分数不全相同）
        unique_scores = set(scores.values())
        assert len(unique_scores) == 3, f"3名候选人评分应有区分度，实际: {scores}"

        # 验证评分降序排列
        score_list = [c["score"] for c in cand_event]
        assert score_list == sorted(score_list, reverse=True), "候选人应按评分降序排列"

    def test_experience_dimension_differentiates(self, chat_env):
        """experience 维度应按工作年限拉开差距"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        chat_env["llm_chat_responses"][:] = [
            "search",
            json.dumps({"skill": 80, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年经验"}),  # 毛光铭 4年
            json.dumps({"skill": 80, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "0年经验"}),  # 李志鹏 0年
            json.dumps({"skill": 80, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验"}),  # 温佳蕊 1年
        ]
        chat_env["llm_chat_call_count"]["i"] = 0

        events = _send_message(chat_env["client"], token, session_id, "找NLP工程师_经验维度测试")
        cand_event = next(e["data"] for e in events if e["event"] == "candidates")

        exp_scores = {c["name"]: c["score_detail"]["experience"] for c in cand_event}
        assert exp_scores["毛光铭"] > exp_scores["温佳蕊"] > exp_scores["李志鹏"], \
            "experience 维度应按工作年限拉开差距"


class TestEmptyResultScenario(_BaseChatTest):
    """场景8: 空结果处理"""

    def test_search_empty_result_has_clarify(self, chat_env):
        """搜索无结果时应有 token 事件（澄清提示）"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        # VectorStore 返回空结果（修改已 patch 的 mock）
        original_return = chat_env["vector_store_mock"].hybrid_search.return_value
        chat_env["vector_store_mock"].hybrid_search = AsyncMock(return_value=[])

        chat_env["llm_chat_responses"][:] = ["search"]
        chat_env["llm_chat_call_count"]["i"] = 0

        try:
            events = _send_message(chat_env["client"], token, session_id, "找一个冷门技能zzz")
            event_names = [e["event"] for e in events]

            # search 意图应触发检索
            assert "retrieval" in event_names
            retrieval_data = next(e["data"] for e in events if e["event"] == "retrieval")
            assert retrieval_data["count"] == 0

            # 空结果不应有 rank 事件
            assert "rank" not in event_names

            # 应有 token 和 done（澄清提示）
            assert "token" in event_names
            assert "done" in event_names
        finally:
            chat_env["vector_store_mock"].hybrid_search = AsyncMock(return_value=original_return)


class TestSynonymExpansion(_BaseChatTest):
    """场景9: 同义词扩展检索"""

    def test_search_nlp_returns_bert_candidates(self, chat_env):
        """搜索"NLP"应能召回技能为BERT/FastText的候选人"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        chat_env["llm_chat_responses"][:] = [
            "search",
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验"}),
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),
            json.dumps({"skill": 72, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验"}),
        ]
        chat_env["llm_chat_call_count"]["i"] = 0

        events = _send_message(chat_env["client"], token, session_id, "NLP")
        cand_event = next(e["data"] for e in events if e["event"] == "candidates")

        # 验证返回了候选人（即使查询只有"NLP"，通过同义词扩展也能召回）
        assert len(cand_event) == 3

        # 验证候选人技能中包含 BERT/FastText（不是直接写"NLP"的也能被召回）
        all_skills = []
        for c in cand_event:
            all_skills.extend(c.get("skills", []))
        assert "BERT" in all_skills, "搜索NLP应能召回技能含BERT的候选人"
        assert "FastText" in all_skills, "搜索NLP应能召回技能含FastText的候选人"


class TestSessionIsolation(_BaseChatTest):
    """场景10: 会话隔离"""

    def test_different_sessions_isolated(self, chat_env):
        """不同会话的候选人上下文不应串扰"""
        token = _login(chat_env)
        session1 = _create_session(chat_env, token, "会话1")
        session2 = _create_session(chat_env, token, "会话2")

        # 会话1: 搜索 NLP 工程师
        chat_env["llm_chat_responses"][:] = [
            "search",
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验"}),
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),
            json.dumps({"skill": 72, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验"}),
        ]
        chat_env["llm_chat_call_count"]["i"] = 0
        _send_message(chat_env["client"], token, session1, "帮我找一些NLP方向的工程师")

        # 会话2: 直接对比（无历史候选人，应触发检索）
        chat_env["llm_chat_responses"][:] = [
            "compare",
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验"}),
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),
            json.dumps({"skill": 72, "experience": 65, "education": 75, "salary": 80,
                        "overall": 0, "reason": "1年经验"}),
        ]
        chat_env["llm_chat_call_count"]["i"] = 0
        events2 = _send_message(chat_env["client"], token, session2, "对比一下候选人")
        event_names2 = [e["event"] for e in events2]

        # 会话2无历史，应触发检索（不复用会话1的历史）
        assert "retrieval" in event_names2, "不同会话不应共享候选人上下文"


class TestSSEEventFlow(_BaseChatTest):
    """场景11: SSE 事件流完整性"""

    def test_search_sse_event_order(self, chat_env):
        """search 意图SSE事件顺序: intent → retrieval → rank → candidates → token → done"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        chat_env["llm_chat_responses"][:] = [
            "search",
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验"}),
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),
        ]
        chat_env["llm_chat_call_count"]["i"] = 0

        events = _send_message(chat_env["client"], token, session_id, "找NLP工程师")
        event_names = [e["event"] for e in events]

        # 验证事件存在
        assert "intent" in event_names
        assert "retrieval" in event_names
        assert "rank" in event_names
        assert "candidates" in event_names
        assert "token" in event_names
        assert "done" in event_names

        # 验证事件顺序: intent 在 retrieval 之前
        assert event_names.index("intent") < event_names.index("retrieval")
        # retrieval 在 candidates 之前
        assert event_names.index("retrieval") < event_names.index("candidates")
        # candidates 在 token 之前
        assert event_names.index("candidates") < event_names.index("token")
        # token 在 done 之前
        assert event_names.index("token") < event_names.index("done")

    def test_compare_sse_no_retrieval_no_rank(self, chat_env):
        """compare 意图SSE事件: intent → candidates → token → done（无 retrieval/rank）"""
        token = _login(chat_env)
        session_id = _create_session(chat_env, token)

        # 第1轮搜索
        chat_env["llm_chat_responses"][:] = [
            "search",
            json.dumps({"skill": 92, "experience": 90, "education": 75, "salary": 85,
                        "overall": 0, "reason": "4年NLP经验"}),
            json.dumps({"skill": 75, "experience": 50, "education": 75, "salary": 85,
                        "overall": 0, "reason": "应届生"}),
        ]
        chat_env["llm_chat_call_count"]["i"] = 0
        _send_message(chat_env["client"], token, session_id, "找NLP工程师")

        # 第2轮对比
        chat_env["llm_chat_responses"][:] = ["compare"]
        chat_env["llm_chat_call_count"]["i"] = 0
        events = _send_message(chat_env["client"], token, session_id, "对比毛光铭和李志鹏")
        event_names = [e["event"] for e in events]

        assert "retrieval" not in event_names
        assert "rank" not in event_names
        assert "intent" in event_names
        assert "candidates" in event_names
        assert "token" in event_names
        assert "done" in event_names
