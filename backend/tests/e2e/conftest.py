"""
文件名: tests/e2e/conftest.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 端到端测试 fixtures - 统一 mock 所有外部依赖
入参: 无
出参: e2e_env fixture（含 FakeMongo / FakeRedis / client / 共享状态）

设计要点：
1. 用 FakeMongoDB 替换 MongoDB.db，使数据在 API 间真实流转
2. mock 所有 AI 服务（LLM/Embedding/Reranker/OCR/MinIO/StrategySelector）
3. 预置用户数据用于登录测试
4. 共享状态 dict 在测试步骤间传递 token / resume_id 等
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from tests.e2e.fake_infra import FakeMongoDB, FakeRedis


@pytest.fixture(scope="module")
def e2e_env():
    """端到端测试环境：统一 mock 外部依赖，数据在内存 DB 真实流转

    返回 dict:
        - client: TestClient
        - mongo: FakeMongoDB（数据存储）
        - redis: FakeRedis
        - state: 共享状态 dict（token / resume_id 等）
        - llm_mock: LLM mock 对象（可按需调整 side_effect）
    """
    mongo = FakeMongoDB()
    redis = FakeRedis()

    # 预置 HR 用户（密码 admin123 的 bcrypt hash）
    import bcrypt
    password_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
    mongo.users._data.append({
        "user_id": "u_admin",
        "username": "admin",
        "password_hash": password_hash,
        "role": "hr",
        "email": "admin@talentsense.com",
    })

    # 预置 2 个已解析的简历（供检索/对比/看板等流程使用）
    mongo.resumes._data.extend([
        {
            "resume_id": "res_demo_zhang",
            "candidate_id": "cand_zhang",
            "basic_info": {"name": "张三", "phone_masked": "138****1234"},
            "name": "张三",
            "education": "本科",
            "education_level": 2,
            "work_years": 5,
            "skills": ["Java", "Spring", "MySQL"],
            "work_experience": [],
            "education_detail": [],
            "summary": "5 年 Java 后端开发经验，精通 Spring 微服务",
            "expected_salary": {"min": 20, "max": 30},
            "tags": [],
            "is_favorite": False,
            "notes": "",
            "parse_info": {"parse_status": "completed"},
            "file_info": {"file_id": "minio_demo_zhang", "file_name": "zhang.pdf", "file_type": "pdf"},
        },
        {
            "resume_id": "res_demo_li",
            "candidate_id": "cand_li",
            "basic_info": {"name": "李四", "phone_masked": "139****5678"},
            "name": "李四",
            "education": "硕士",
            "education_level": 3,
            "work_years": 3,
            "skills": ["Python", "Django", "PostgreSQL"],
            "work_experience": [],
            "education_detail": [],
            "summary": "3 年 Python 后端开发经验，擅长 Django 框架",
            "expected_salary": {"min": 18, "max": 25},
            "tags": [],
            "is_favorite": False,
            "notes": "",
            "parse_info": {"parse_status": "completed"},
            "file_info": {"file_id": "minio_demo_li", "file_name": "li.pdf", "file_type": "pdf"},
        },
    ])

    # 预置邮件配置（密码 "secret" 的 base64）
    import base64
    mongo.email_config._data.append({
        "_id": "default",
        "smtp_host": "smtp.example.com",
        "smtp_port": 465,
        "smtp_user": "hr@talentsense.com",
        "smtp_password_encrypted": base64.b64encode(b"secret").decode(),
    })

    # 构造 LLM mock：默认返回可配置
    llm_mock = AsyncMock()
    # 意图识别默认返回 search
    llm_chat_responses = [
        "search",  # intent_node
        "85",      # search_service _llm_score
        "张三匹配度高，5 年 Java 经验",  # search_service _llm_reason
    ]
    llm_chat_call_count = {"i": 0}

    async def _chat_side_effect(messages, **kwargs):
        idx = llm_chat_call_count["i"]
        llm_chat_call_count["i"] += 1
        if idx < len(llm_chat_responses):
            return llm_chat_responses[idx]
        return "ok"

    llm_mock.chat = AsyncMock(side_effect=_chat_side_effect)

    # chat_stream：yield 几个 token
    async def _chat_stream_side_effect(messages, **kwargs):
        for tok in ["推荐", "张三", "，5 年 Java 经验"]:
            yield tok

    llm_mock.chat_stream = _chat_stream_side_effect

    # Embedding mock
    embedding_mock = MagicMock()
    embedding_mock.encode = MagicMock(return_value=([[0.1] * 1024], [{"key": 0.1}]))

    # Reranker mock
    reranker_mock = MagicMock()
    reranker_mock.rerank = MagicMock(return_value=[0.95, 0.80])

    # VectorStore mock：返回预置候选人（Milvus candidate_id 字段实际存的是 resume_id）
    vector_store_mock = AsyncMock()
    vector_store_mock.hybrid_search = AsyncMock(return_value=[
        {"chunk_id": "ck1", "candidate_id": "res_demo_zhang", "score": 0.95, "parent_content": "Java 5年经验"},
        {"chunk_id": "ck2", "candidate_id": "res_demo_li", "score": 0.80, "parent_content": "Python 3年经验"},
    ])
    vector_store_mock.insert = AsyncMock()
    vector_store_mock.delete_by_resume_id = AsyncMock()

    # MinIO mock
    minio_mock = MagicMock()
    minio_mock.upload_bytes = MagicMock(return_value="minio_new_file")
    minio_mock.presigned_url = MagicMock(return_value="https://minio.example.com/presigned")
    minio_mock.delete = MagicMock()

    # OCR mock
    ocr_mock = MagicMock()
    ocr_mock.extract_text = MagicMock(return_value="张三 5年Java开发经验 Spring微服务")

    # StrategySelector mock
    strategy_mock = AsyncMock()
    strategy_mock.select = AsyncMock(return_value="direct")
    strategy_mock.rewrite = AsyncMock(return_value=["Java 5年经验"])

    # aiosmtplib.send mock
    aiosmtp_send_mock = AsyncMock()

    # 直接修改 MongoDB / RedisClient 类属性（不 patch 整个类）
    # 因为 service 模块顶部已 from app.core.database import MongoDB 绑定原类引用
    from app.core.database import MongoDB as _MongoCls, RedisClient as _RedisCls
    original_mongo_db = _MongoCls.db
    original_mongo_connect = _MongoCls.connect
    original_mongo_disconnect = _MongoCls.disconnect
    original_redis_pool = _RedisCls.pool
    original_redis_connect = _RedisCls.connect
    original_redis_get_client = _RedisCls.get_client

    _MongoCls.db = mongo
    _MongoCls.connect = AsyncMock()
    _MongoCls.disconnect = AsyncMock()
    _RedisCls.pool = MagicMock()  # 非 None，使 service 初始化时走 redis 分支
    _RedisCls.connect = AsyncMock()
    _RedisCls.get_client = MagicMock(return_value=redis)

    # 用 ExitStack 管理大量 patch，避免 Python 静态嵌套块限制
    from contextlib import ExitStack
    patch_specs = [
        ("app.core.llm_client.llm_client", {"new": llm_mock}),
        ("app.services.resume_service.llm_client", {"new": llm_mock}),
        ("app.services.resume_service.minio_client", {"new": minio_mock}),
        ("app.services.resume_service.ocr_engine", {"new": ocr_mock}),
        ("app.core.embedding.embedding_model", {"new": embedding_mock}),
        ("app.core.vector_store.vector_store", {"new": vector_store_mock}),
        ("app.core.reranker.reranker_model", {"new": reranker_mock}),
        ("app.core.strategy_selector.strategy_selector", {"new": strategy_mock}),
        ("app.services.search_service.llm_client", {"new": llm_mock}),
        ("app.services.interview_service.llm_client", {"new": llm_mock}),
        ("app.services.email_service.aiosmtplib.send", {"new": aiosmtp_send_mock}),
        ("app.agent.nodes.llm_client", {"new": llm_mock}),
        ("app.agent.nodes.search_service", {}),
        ("app.agent.nodes.resume_service", {}),
        ("app.services.agent_service.llm_client", {"new": llm_mock}),
        # 模块级 import 绑定问题：candidate_service / search_service / jd_match_service
        # 在模块顶部 from app.core.xxx import xxx 绑定了原始对象引用，
        # 仅 patch 源模块属性无法影响这些 service 中已绑定的引用，
        # 必须在 service 模块上再 patch 一份
        ("app.services.candidate_service.embedding_model", {"new": embedding_mock}),
        ("app.services.candidate_service.vector_store", {"new": vector_store_mock}),
        ("app.services.search_service.embedding_model", {"new": embedding_mock}),
        ("app.services.search_service.reranker_model", {"new": reranker_mock}),
        ("app.services.search_service.vector_store", {"new": vector_store_mock}),
        ("app.services.search_service.strategy_selector", {"new": strategy_mock}),
        ("app.services.jd_match_service.embedding_model", {"new": embedding_mock}),
        ("app.services.jd_match_service.reranker_model", {"new": reranker_mock}),
        ("app.services.jd_match_service.vector_store", {"new": vector_store_mock}),
    ]

    with ExitStack() as stack:
        # nodes 的 search_service / resume_service 返回值需要保存（索引 12/13）
        mock_nodes_search = stack.enter_context(patch(patch_specs[12][0], **patch_specs[12][1]))
        mock_nodes_resume = stack.enter_context(patch(patch_specs[13][0], **patch_specs[13][1]))
        # 其余 patch 直接 enter
        for i in range(len(patch_specs)):
            if i in (12, 13):
                continue
            stack.enter_context(patch(patch_specs[i][0], **patch_specs[i][1]))

        # nodes 中的 search_service 和 resume_service 单例
        # search_service.search 需调用真实逻辑（会用到 mock 的 embedding/reranker/vector_store）
        from app.services.search_service import SearchService
        real_search = SearchService()
        real_search.resumes_coll = mongo.resumes
        mock_nodes_search.search = real_search.search
        # resume_service.get_detail 调用真实逻辑
        from app.services.resume_service import ResumeService
        real_resume = ResumeService()
        real_resume.resumes_coll = mongo.resumes
        mock_nodes_resume.get_detail = real_resume.get_detail

        client = TestClient(app)

        yield {
            "client": client,
            "mongo": mongo,
            "redis": redis,
            "state": {},
            "llm_mock": llm_mock,
            "llm_chat_responses": llm_chat_responses,
            "llm_chat_call_count": llm_chat_call_count,
            "minio_mock": minio_mock,
            "aiosmtp_send_mock": aiosmtp_send_mock,
        }

    # 恢复 MongoDB / RedisClient 类属性，避免污染其他测试
    _MongoCls.db = original_mongo_db
    _MongoCls.connect = original_mongo_connect
    _MongoCls.disconnect = original_mongo_disconnect
    _RedisCls.pool = original_redis_pool
    _RedisCls.connect = original_redis_connect
    _RedisCls.get_client = original_redis_get_client


def _auth_header(token: str) -> dict:
    """构造认证请求头"""
    return {"Authorization": f"Bearer {token}"}


def parse_sse_events(response_text: str) -> list[dict]:
    """解析 SSE 响应文本，返回 [{event, data}, ...]

    入参:
        response_text: SSE 原始文本
    出参:
        事件列表
    """
    events = []
    for block in response_text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_name = ""
        data_str = ""
        for line in block.split("\n"):
            if line.startswith("event: "):
                event_name = line[7:]
            elif line.startswith("data: "):
                data_str = line[6:]
        if event_name:
            import json as _json
            try:
                data = _json.loads(data_str) if data_str else {}
            except Exception:
                data = {"raw": data_str}
            events.append({"event": event_name, "data": data})
    return events
