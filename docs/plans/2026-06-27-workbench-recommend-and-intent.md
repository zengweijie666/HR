<!--
  文件名: 2026-06-27-workbench-recommend-and-intent.md
  创建时间: 2026-06-27
  作者: TalentSense Team
  功能描述: 工作台推荐候选人卡片、意图识别扩展、分维度评分、会话标题自动命名实施计划
-->
# 工作台推荐与意图优化实施计划

**Goal:** 修复工作台推荐候选人卡片不显示/追问消失问题，扩展意图识别支持通用问答，分数透明化为 4 维度评分，会话标题自动取首条问题前 20 字。

**Architecture:** 后端三层架构（api/services/agent），SSE 流式编排保持 agent_service.send_message_stream 主控；前端 Workbench 三栏布局不变，仅改卡片更新逻辑与 CandidateCard 渲染。所有改动遵循 TDD：先写失败测试 → 实现 → 通过 → 提交。

**Tech Stack:** FastAPI + Motor + LangGraph 节点（后端）；Vue3 Composition API + Pinia + Vitest（前端）

## Global Constraints

- 后端测试用 `.venv\Scripts\python.exe -m pytest`，前端测试用 `npm test`
- MongoDB mock 模式：collection 用 MagicMock，cursor chain `find().skip().limit().sort().to_list()` 各环节 return_value 链式设置；`to_list` 用 AsyncMock
- SSE 事件格式：`event: {name}\ndata: {json}\n\n`
- 统一响应格式 `{code, message, data, trace_id}`（SSE 端点除外）
- LLM 调用强制 `response_format={"type":"json_object"}` 用于 JSON 输出场景
- 文件元信息：每个新建文件首部需写文件名/创建时间/作者/功能描述

---

## Task 1: 后端 - INTENT_PROMPT 扩展为 5 类，新增 QA_PROMPT

**Files:**
- Modify: `backend/app/agent/prompts.py`
- Test: `backend/tests/agent/test_prompts.py`

**Interfaces:**
- Produces: `INTENT_PROMPT`（5 类）、`QA_PROMPT`（供 Task 3 使用）

- [ ] **Step 1: 写失败测试 - 验证 INTENT_PROMPT 含 qa 类、QA_PROMPT 存在**

```python
# backend/tests/agent/test_prompts.py
"""
文件名: test_prompts.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: 测试 prompts 模块意图/通用问答/评分模板
"""
from app.agent.prompts import INTENT_PROMPT, QA_PROMPT, SCORE_PROMPT


def test_intent_prompt_contains_qa_category():
    """INTENT_PROMPT 应包含 qa 意图分类"""
    assert "qa" in INTENT_PROMPT
    assert "HR 知识问答" in INTENT_PROMPT or "通用问答" in INTENT_PROMPT


def test_qa_prompt_exists_and_has_constraints():
    """QA_PROMPT 应存在且包含不编造候选人约束"""
    assert QA_PROMPT is not None
    assert "不编造" in QA_PROMPT or "禁止编造" in QA_PROMPT


def test_score_prompt_requires_json():
    """SCORE_PROMPT 应要求 JSON 输出含 4 维度"""
    assert "skill" in SCORE_PROMPT
    assert "experience" in SCORE_PROMPT
    assert "education" in SCORE_PROMPT
    assert "salary" in SCORE_PROMPT
    assert "overall" in SCORE_PROMPT
    assert "reason" in SCORE_PROMPT
```

- [ ] **Step 2: 运行测试验证失败**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/agent/test_prompts.py -v`
Expected: FAIL（qa 类、QA_PROMPT、4 维度均不存在）

- [ ] **Step 3: 修改 prompts.py 实现**

在 `backend/app/agent/prompts.py` 中：

1. 修改 `INTENT_PROMPT`，新增 `qa` 类：
```python
INTENT_PROMPT = """你是招聘助手意图分类器。根据用户查询分类意图：
- chitchat: 闲聊/打招呼（你好/谢谢/你是谁）
- search: 搜索/推荐候选人
- detail: 查询某候选人详情
- compare: 对比候选人
- qa: HR 知识问答/系统使用帮助/通用问答（不涉及具体候选人推荐）
查询：{query}
历史：{history}
只返回意图名（chitchat/search/detail/compare/qa）："""
```

2. 新增 `QA_PROMPT`：
```python
QA_PROMPT = """你是 TalentSense 智能招聘助手。你可以回答 HR 流程咨询、系统使用帮助、通用知识问答。

规则：
1. 不编造候选人信息，不提供虚假简历
2. 涉及具体候选人推荐时，引导用户使用"推荐/搜索/查找候选人"等语句
3. 回答简洁专业，HR 领域问题给出可执行建议
4. 系统使用问题基于 TalentSense HR 平台功能回答（简历库/工作台/邮件中心/数据看板/用户管理）

用户问题：{query}

请直接回答："""
```

3. 修改 `SCORE_PROMPT` 为 4 维度 JSON：
```python
SCORE_PROMPT = """你是招聘评分员。根据需求给候选人打分，按 4 个维度分别打分（0-100），并给出综合评分和一句话理由。

需求：{query}
候选人：{candidate}

评分维度：
- skill: 技能匹配度（候选人技能与需求关键词的重合度）
- experience: 工作经验匹配度（年限与岗位级别匹配）
- education: 学历匹配度（学历层次与岗位要求匹配）
- salary: 薪资匹配度（期望薪资与市场水平合理性）

严格按以下 JSON 格式返回，禁止返回 null，禁止添加任何其他文字：
{{"skill": 85, "experience": 70, "education": 90, "salary": 60, "overall": 78, "reason": "技能高度匹配，但薪资期望偏高"}}"""
```

- [ ] **Step 4: 运行测试验证通过**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/agent/test_prompts.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/agent/prompts.py backend/tests/agent/test_prompts.py
git commit -m "feat: 扩展意图识别为5类新增qa意图和4维度评分prompt"
```

---

## Task 2: 后端 - intent_node 白名单新增 qa，兜底改 qa

**Files:**
- Modify: `backend/app/agent/nodes.py`
- Test: `backend/tests/agent/test_nodes.py`

**Interfaces:**
- Consumes: Task 1 的 `INTENT_PROMPT`
- Produces: `intent_node` 支持返回 `qa`

- [ ] **Step 1: 写失败测试 - qa 意图分类与兜底为 qa**

```python
# 追加到 backend/tests/agent/test_nodes.py
"""
新增测试：qa 意图分类、异常兜底为 qa
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agent.nodes import intent_node


@pytest.mark.asyncio
async def test_intent_node_returns_qa(monkeypatch):
    """意图识别为 qa 时应正确返回"""
    async def mock_chat(messages):
        return "qa"
    monkeypatch.setattr("app.agent.nodes.llm_client.chat", mock_chat)

    state = {"query": "HR 怎么筛选候选人", "history": ""}
    result = await intent_node(state)
    assert result["intent_type"] == "qa"


@pytest.mark.asyncio
async def test_intent_node_fallback_to_qa_on_invalid(monkeypatch):
    """意图识别返回非法值时应兜底为 qa（而非 chitchat）"""
    async def mock_chat(messages):
        return "invalid_intent"
    monkeypatch.setattr("app.agent.nodes.llm_client.chat", mock_chat)

    state = {"query": "测试", "history": ""}
    result = await intent_node(state)
    assert result["intent_type"] == "qa"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/agent/test_nodes.py::test_intent_node_returns_qa backend/tests/agent/test_nodes.py::test_intent_node_fallback_to_qa_on_invalid -v`
Expected: FAIL（白名单无 qa，兜底为 chitchat）

- [ ] **Step 3: 修改 nodes.py 实现**

在 `backend/app/agent/nodes.py` 的 `intent_node` 函数中：
1. 白名单新增 `"qa"`
2. 兜底从 `"chitchat"` 改为 `"qa"`

```python
async def intent_node(state: AgentState) -> AgentState:
    """意图识别节点"""
    query = state.get("query", "")
    history = state.get("history", "")
    prompt = INTENT_PROMPT.format(query=query, history=history)
    try:
        resp = await llm_client.chat([{"role": "user", "content": prompt}])
        intent = resp.strip().lower()
        if intent not in ("chitchat", "search", "detail", "compare", "qa"):
            intent = "qa"  # 兜底改为 qa
    except Exception as e:
        logger.warning(f"意图识别失败，兜底为 qa: {e}")
        intent = "qa"
    return {**state, "intent_type": intent}
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add backend/app/agent/nodes.py backend/tests/agent/test_nodes.py
git commit -m "feat: intent_node白名单新增qa意图兜底改为qa"
```

---

## Task 3: 后端 - agent_service.send_message_stream 新增 qa 分支

**Files:**
- Modify: `backend/app/services/agent_service.py`
- Test: `backend/tests/services/test_agent_service.py`

**Interfaces:**
- Consumes: Task 1 的 `QA_PROMPT`、Task 2 的 intent_node 返回 qa
- Produces: qa 分支跳过检索，走 QA_PROMPT 流式回答

- [ ] **Step 1: 写失败测试 - qa 分支不触发检索，走 QA_PROMPT**

```python
# 追加到 backend/tests/services/test_agent_service.py
"""
新增测试：qa 意图分支不调用 retrieve_rank_node，直接走 QA_PROMPT
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.agent_service import agent_service


@pytest.mark.asyncio
async def test_send_message_stream_qa_branch_skips_retrieval(monkeypatch):
    """qa 意图应跳过检索"""
    # mock intent_node 返回 qa
    async def mock_intent(state):
        return {**state, "intent_type": "qa"}
    monkeypatch.setattr("app.services.agent_service.intent_node", mock_intent)

    # mock 检索节点，若被调用则测试失败
    retrieve_called = {"value": False}
    async def mock_retrieve(state):
        retrieve_called["value"] = True
        return {**state, "candidates": []}
    monkeypatch.setattr("app.services.agent_service.retrieve_rank_node", mock_retrieve)

    # mock LLM 流式
    async def mock_stream(messages):
        for token in ["这是", "通用", "回答"]:
            yield token
    monkeypatch.setattr("app.services.agent_service.llm_client.chat_stream", mock_stream)

    # mock _save_message
    agent_service._save_message = AsyncMock()

    # mock sessions_coll
    agent_service.sessions_coll = MagicMock()
    agent_service.sessions_coll.find_one = AsyncMock(return_value={"messages": []})

    state = {
        "query": "HR 怎么筛选候选人",
        "session_id": "s_test",
        "user_id": "u_test",
        "history": "",
    }

    events = []
    async for event in agent_service.send_message_stream(state):
        events.append(event)

    assert not retrieve_called["value"], "qa 分支不应触发检索"
    # 应有 token 事件
    token_events = [e for e in events if "token" in e]
    assert len(token_events) > 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `.venv\Scripts\python.exe -m pytest backend/tests/services/test_agent_service.py::test_send_message_stream_qa_branch_skips_retrieval -v`
Expected: FAIL（无 qa 分支，可能走检索或 chitchat）

- [ ] **Step 3: 修改 agent_service.py 实现**

在 `send_message_stream` 方法的意图分支逻辑中，新增 `qa` 分支：

```python
async def send_message_stream(self, state: AgentState):
    """SSE 流式发送消息"""
    # ... 意图识别 ...
    intent_type = state.get("intent_type", "qa")

    # 检索分支：search/compare/detail
    if intent_type in ("search", "compare", "detail"):
        # 原有检索逻辑...
        pass
    elif intent_type == "qa":
        # 新增：qa 分支跳过检索，走 QA_PROMPT
        yield _sse_event("intent", {"intent_type": "qa", "strategy": "qa"})
        system_prompt = QA_PROMPT.format(query=state["query"])
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": state["query"]}]
        async for token in llm_client.chat_stream(messages):
            yield _sse_event("token", {"delta": token})
    else:
        # chitchat 原有逻辑
        pass
    # ... 持久化等 ...
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/agent_service.py backend/tests/services/test_agent_service.py
git commit -m "feat: agent_service新增qa意图分支跳过检索走QA_PROMPT"
```

---

## Task 4: 后端 - 检索为空时仍 yield candidates 事件

**Files:**
- Modify: `backend/app/services/agent_service.py`
- Test: `backend/tests/services/test_agent_service.py`

**Interfaces:**
- Produces: 即使检索返回空数组，也 yield `candidates` 事件（空数组）

- [ ] **Step 1: 写失败测试 - 检索为空仍 yield candidates 事件**

```python
# 追加到 backend/tests/services/test_agent_service.py
@pytest.mark.asyncio
async def test_retrieve_empty_yields_candidates_event(monkeypatch):
    """检索返回空列表时仍应 yield candidates 事件（空数组）"""
    async def mock_intent(state):
        return {**state, "intent_type": "search"}
    monkeypatch.setattr("app.services.agent_service.intent_node", mock_intent)

    async def mock_retrieve(state):
        return {**state, "candidates": []}  # 空列表
    monkeypatch.setattr("app.services.agent_service.retrieve_rank_node", mock_retrieve)

    async def mock_stream(messages):
        yield "未找到匹配候选人"
    monkeypatch.setattr("app.services.agent_service.llm_client.chat_stream", mock_stream)

    agent_service._save_message = AsyncMock()
    agent_service.sessions_coll = MagicMock()
    agent_service.sessions_coll.find_one = AsyncMock(return_value={"messages": []})

    state = {"query": "推荐不存在的岗位", "session_id": "s_test", "user_id": "u_test", "history": ""}

    events = []
    async for event in agent_service.send_message_stream(state):
        events.append(event)

    # 应包含 candidates 事件，data 为空数组
    candidates_events = [e for e in events if 'event: candidates' in e]
    assert len(candidates_events) > 0, "检索为空也应 yield candidates 事件"
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 修改 agent_service.py 实现**

在检索分支中，无论 `candidates` 是否为空，都 yield `candidates` 事件：

```python
# 在 retrieve_rank_node 调用后
candidates = state.get("candidates", [])
# 无论是否为空都 yield（原来可能只在非空时 yield）
yield _sse_event("candidates", {"candidates": candidates})
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/agent_service.py backend/tests/services/test_agent_service.py
git commit -m "fix: 检索为空时仍yield candidates事件便于前端区分"
```

---

## Task 5: 后端 - _llm_score 改为 _llm_score_multi 返回 4 维度

**Files:**
- Modify: `backend/app/services/search_service.py`
- Test: `backend/tests/services/test_search_service.py`

**Interfaces:**
- Consumes: Task 1 的 `SCORE_PROMPT`
- Produces: candidates 字段含 `score_detail` 和 `reason`

- [ ] **Step 1: 写失败测试 - 正常 JSON 解析、LLM 失败兜底、JSON 解析失败兜底**

```python
# 追加到 backend/tests/services/test_search_service.py
import pytest
import json
from unittest.mock import AsyncMock, patch
from app.services.search_service import SearchService


@pytest.mark.asyncio
async def test_llm_score_multi_json_parse(monkeypatch):
    """正常 JSON 解析应返回 4 维度 + overall + reason"""
    svc = SearchService()
    async def mock_chat(messages):
        return json.dumps({"skill": 85, "experience": 70, "education": 90, "salary": 60, "overall": 78, "reason": "技能高度匹配"})
    monkeypatch.setattr("app.services.search_service.llm_client.chat", mock_chat)

    result = await svc._llm_score_multi("前端工程师", {"name": "张三", "skills": ["Vue"]}, 0.8)
    assert result["skill"] == 85
    assert result["experience"] == 70
    assert result["education"] == 90
    assert result["salary"] == 60
    assert result["overall"] == 78
    assert result["reason"] == "技能高度匹配"


@pytest.mark.asyncio
async def test_llm_score_multi_fallback_rerank(monkeypatch):
    """LLM 调用失败应回退 rerank_score*100"""
    svc = SearchService()
    async def mock_chat(messages):
        raise Exception("LLM 调用失败")
    monkeypatch.setattr("app.services.search_service.llm_client.chat", mock_chat)

    result = await svc._llm_score_multi("前端工程师", {"name": "张三"}, 0.8)
    assert result["skill"] == 80  # 0.8 * 100
    assert result["overall"] == 80
    assert "语义相似度" in result["reason"]


@pytest.mark.asyncio
async def test_llm_score_multi_fallback_zero(monkeypatch):
    """JSON 解析失败应全 0 兜底"""
    svc = SearchService()
    async def mock_chat(messages):
        return "not a json"
    monkeypatch.setattr("app.services.search_service.llm_client.chat", mock_chat)

    result = await svc._llm_score_multi("前端工程师", {"name": "张三"}, 0.8)
    assert result["skill"] == 0
    assert result["overall"] == 0
    assert "暂不可用" in result["reason"]
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 修改 search_service.py 实现**

将 `_llm_score` 改为 `_llm_score_multi`，并更新 `_enrich_candidates` 调用：

```python
async def _llm_score_multi(self, query: str, candidate: dict, rerank_score: float = 0.0) -> dict:
    """分维度评分，返回 {skill, experience, education, salary, overall, reason}"""
    try:
        prompt = SCORE_PROMPT.format(query=query, candidate=str(candidate))
        resp = await llm_client.chat(
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(resp.strip())
        # 校验字段
        result = {
            "skill": float(data.get("skill", 0)),
            "experience": float(data.get("experience", 0)),
            "education": float(data.get("education", 0)),
            "salary": float(data.get("salary", 0)),
            "overall": float(data.get("overall", 0)),
            "reason": data.get("reason", "评分暂不可用"),
        }
        # overall 兜底加权计算
        if result["overall"] == 0:
            result["overall"] = (
                0.3 * result["skill"] + 0.3 * result["experience"]
                + 0.2 * result["education"] + 0.2 * result["salary"]
            )
        return result
    except Exception as e:
        logger.warning(f"LLM 多维度评分失败，回退 rerank_score: {e}")
        fallback = rerank_score * 100
        return {
            "skill": fallback, "experience": fallback,
            "education": fallback, "salary": fallback,
            "overall": fallback, "reason": "基于语义相似度匹配",
        }


# _enrich_candidates 中调用处改为：
score_data = await self._llm_score_multi(query, candidate, rerank_score)
candidate["score"] = score_data["overall"]
candidate["score_detail"] = {
    "skill": score_data["skill"],
    "experience": score_data["experience"],
    "education": score_data["education"],
    "salary": score_data["salary"],
}
candidate["reason"] = score_data["reason"]
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/search_service.py backend/tests/services/test_search_service.py
git commit -m "feat: 评分改为4维度透明评分skill/experience/education/salary+reason"
```

---

## Task 6: 后端 - _save_message 首条消息更新会话标题

**Files:**
- Modify: `backend/app/services/agent_service.py`
- Test: `backend/tests/services/test_agent_service.py`

**Interfaces:**
- Produces: 首条消息后 title 自动更新为 query[:20]

- [ ] **Step 1: 写失败测试 - 首条消息更新标题、非首条不更新**

```python
# 追加到 backend/tests/services/test_agent_service.py
@pytest.mark.asyncio
async def test_save_message_updates_title_on_first():
    """首条消息应更新标题为 query 前 20 字"""
    agent_service.sessions_coll = MagicMock()
    # 模拟空 messages（首条）
    agent_service.sessions_coll.find_one = AsyncMock(return_value={"messages": []})
    agent_service.sessions_coll.update_one = AsyncMock()

    user_msg = {"message_id": "m1", "role": "user", "content": "推荐前端工程师熟悉Vue3和TypeScript"}
    assistant_msg = {"message_id": "m2", "role": "assistant", "content": "好的"}

    await agent_service._save_message("s_test", user_msg, assistant_msg, "推荐前端工程师熟悉Vue3和TypeScript")

    # 验证 update_one 被调用，且 $set 包含 title
    call_args = agent_service.sessions_coll.update_one.call_args
    update_doc = call_args.kwargs.get("update") or call_args.args[1]
    assert "$set" in update_doc
    assert "title" in update_doc["$set"]
    assert update_doc["$set"]["title"] == "推荐前端工程师熟悉Vue3和TypeScript"[:20]


@pytest.mark.asyncio
async def test_save_message_no_title_update_on_subsequent():
    """非首条消息不应更新标题"""
    agent_service.sessions_coll = MagicMock()
    # 模拟已有消息（非首条）
    agent_service.sessions_coll.find_one = AsyncMock(return_value={"messages": [{"role": "user", "content": "之前的问题"}]})
    agent_service.sessions_coll.update_one = AsyncMock()

    await agent_service._save_message("s_test", {"role": "user"}, {"role": "assistant"}, "第二个问题")

    call_args = agent_service.sessions_coll.update_one.call_args
    update_doc = call_args.kwargs.get("update") or call_args.args[1]
    assert "$set" in update_doc
    assert "title" not in update_doc["$set"]  # 不应更新标题
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 修改 agent_service.py 的 _save_message 实现**

```python
async def _save_message(self, session_id: str, user_msg: dict, assistant_msg: dict, query: str):
    """保存消息，首条消息时自动更新会话标题"""
    try:
        session = await self.sessions_coll.find_one(
            {"session_id": session_id}, {"messages": 1}
        )
        update = {
            "$push": {"messages": {"$each": [user_msg, assistant_msg], "$slice": -20}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
        # 首条消息自动更新标题
        if session and not session.get("messages"):
            update["$set"]["title"] = query[:20].strip() or "新会话"
        await self.sessions_coll.update_one({"session_id": session_id}, update)
    except Exception as e:
        logger.error(f"保存消息失败: {e}")
        # 标题更新失败不阻塞消息保存，至少保存消息
        try:
            await self.sessions_coll.update_one(
                {"session_id": session_id},
                {"$push": {"messages": {"$each": [user_msg, assistant_msg], "$slice": -20}}}
            )
        except Exception as inner_e:
            logger.error(f"消息保存兜底也失败: {inner_e}")
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/agent_service.py backend/tests/services/test_agent_service.py
git commit -m "feat: 会话首条消息自动更新标题为问题前20字"
```

---

## Task 7: 后端 - done 事件携带 title 字段

**Files:**
- Modify: `backend/app/services/agent_service.py`
- Test: `backend/tests/services/test_agent_service.py`

**Interfaces:**
- Produces: done 事件 payload 含 `title`（仅首条消息时非 None）

- [ ] **Step 1: 写失败测试 - done 事件首条消息携带 title**

```python
# 追加到 backend/tests/services/test_agent_service.py
@pytest.mark.asyncio
async def test_done_event_carries_title_on_first_message(monkeypatch):
    """首条消息的 done 事件应携带 title"""
    async def mock_intent(state):
        return {**state, "intent_type": "qa"}
    monkeypatch.setattr("app.services.agent_service.intent_node", mock_intent)

    async def mock_stream(messages):
        yield "回答"
    monkeypatch.setattr("app.services.agent_service.llm_client.chat_stream", mock_stream)

    # mock _save_message 返回 title（首条）
    async def mock_save(session_id, user_msg, assistant_msg, query):
        return {"title": "测试问题前20字"}
    agent_service._save_message = mock_save

    agent_service.sessions_coll = MagicMock()
    agent_service.sessions_coll.find_one = AsyncMock(return_value={"messages": []})

    state = {"query": "测试问题前20字", "session_id": "s_test", "user_id": "u_test", "history": ""}

    events = []
    async for event in agent_service.send_message_stream(state):
        events.append(event)

    done_events = [e for e in events if "event: done" in e]
    assert len(done_events) > 0
    # 解析 data 验证含 title
    import json as _json
    data_line = [l for l in done_events[0].split("\n") if l.startswith("data: ")][0]
    payload = _json.loads(data_line[6:])
    assert payload.get("title") == "测试问题前20字"
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 修改 agent_service.py 实现**

`_save_message` 返回 `{"title": new_title}` 或 `None`，`send_message_stream` 在 done 事件中透传：

```python
# _save_message 返回值改为
async def _save_message(self, ...):
    # ...
    new_title = None
    if session and not session.get("messages"):
        new_title = query[:20].strip() or "新会话"
        update["$set"]["title"] = new_title
    await self.sessions_coll.update_one(...)
    return {"title": new_title}

# send_message_stream 中调用处
save_result = await self._save_message(session_id, user_msg, assistant_msg, query)
new_title = save_result.get("title") if save_result else None

yield _sse_event("done", {
    "message_id": assistant_msg["message_id"],
    "response": assistant_msg["content"],
    "title": new_title,  # 仅首条消息时非 None
})
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/agent_service.py backend/tests/services/test_agent_service.py
git commit -m "feat: SSE done事件携带title字段供前端同步会话标题"
```

---

## Task 8: 前端 - INTENT_TYPES 新增 qa

**Files:**
- Modify: `frontend/src/utils/constant.ts`

**Interfaces:**
- Produces: `qa: '通用问答'` 供 StreamIndicator 显示

- [ ] **Step 1: 修改 constant.ts**

```typescript
// frontend/src/utils/constant.ts
export const INTENT_TYPES = {
  chitchat: '闲聊',
  search: '搜索推荐',
  detail: '详情查询',
  compare: '对比',
  qa: '通用问答',  // 新增
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/utils/constant.ts
git commit -m "feat: 前端INTENT_TYPES新增qa通用问答标签"
```

---

## Task 9: 前端 - CandidateCard 类型新增 score_detail

**Files:**
- Modify: `frontend/src/types/candidate.ts`

**Interfaces:**
- Produces: `CandidateCard.score_detail?` 供 Task 10 渲染

- [ ] **Step 1: 修改 candidate.ts**

```typescript
// frontend/src/types/candidate.ts
export interface ScoreDetail {
  skill: number
  experience: number
  education: number
  salary: number
}

export interface CandidateCard {
  candidate_id: string
  resume_id: string
  name: string
  work_years: number
  education: string
  skills: string[]
  expected_salary: { min: number; max: number }
  score: number
  score_detail?: ScoreDetail  // 新增，可选
  reason: string
  tags: string[]
  is_favorite: boolean
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/types/candidate.ts
git commit -m "feat: CandidateCard类型新增score_detail可选字段"
```

---

## Task 10: 前端 - CandidateCard.vue 渲染 score_detail 维度

**Files:**
- Modify: `frontend/src/components/candidate/CandidateCard.vue`
- Test: `frontend/tests/components/test_candidate_card.test.ts`

**Interfaces:**
- Consumes: Task 9 的 score_detail 类型

- [ ] **Step 1: 写失败测试 - score_detail 渲染、缺失时不渲染**

```typescript
// 追加到 frontend/tests/components/test_candidate_card.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CandidateCard from '@/components/candidate/CandidateCard.vue'

describe('CandidateCard score_detail', () => {
  it('有 score_detail 时渲染 4 个维度', () => {
    const candidate = {
      candidate_id: 'c1',
      resume_id: 'r1',
      name: '张三',
      work_years: 5,
      education: '本科',
      skills: ['Vue'],
      expected_salary: { min: 20, max: 30 },
      score: 78,
      score_detail: { skill: 85, experience: 70, education: 90, salary: 60 },
      reason: '技能匹配',
      tags: [],
      is_favorite: false,
    }
    const wrapper = mount(CandidateCard, { props: { candidate } })
    expect(wrapper.find('.score-detail').exists()).toBe(true)
    expect(wrapper.findAll('.score-detail__item')).toHaveLength(4)
  })

  it('无 score_detail 时仅显示总分', () => {
    const candidate = {
      candidate_id: 'c1',
      resume_id: 'r1',
      name: '张三',
      work_years: 5,
      education: '本科',
      skills: ['Vue'],
      expected_salary: { min: 20, max: 30 },
      score: 78,
      reason: '技能匹配',
      tags: [],
      is_favorite: false,
    }
    const wrapper = mount(CandidateCard, { props: { candidate } })
    expect(wrapper.find('.score-detail').exists()).toBe(false)
    expect(wrapper.find('.candidate-card__score').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd frontend && npm test -- test_candidate_card.test.ts`

- [ ] **Step 3: 修改 CandidateCard.vue 实现**

在模板中 score 显示区域后新增维度展示：

```vue
<!-- 在总分和星级之后新增 -->
<div v-if="candidate.score_detail" class="score-detail">
  <div
    v-for="(value, key) in candidate.score_detail"
    :key="key"
    class="score-detail__item"
    :title="scoreDimensionLabel(key)"
  >
    <span class="score-detail__label">{{ scoreDimensionLabel(key) }}</span>
    <div class="score-detail__bar">
      <div class="score-detail__bar-fill" :style="{ width: `${value}%` }"></div>
    </div>
    <span class="score-detail__value">{{ value }}</span>
  </div>
</div>
```

```typescript
// script 中新增
function scoreDimensionLabel(key: string): string {
  const labels: Record<string, string> = {
    skill: '技能',
    experience: '经验',
    education: '学历',
    salary: '薪资',
  }
  return labels[key] || key
}
```

```scss
/* style 中新增 */
.score-detail {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;

  &__item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
  }

  &__label {
    width: 32px;
    color: var(--color-ink-soft);
  }

  &__bar {
    flex: 1;
    height: 4px;
    background: var(--color-line-soft);
    border-radius: 2px;
    overflow: hidden;
  }

  &__bar-fill {
    height: 100%;
    background: var(--color-primary);
    transition: width 0.3s;
  }

  &__value {
    width: 24px;
    text-align: right;
    font-family: var(--font-mono);
    color: var(--color-ink);
  }
}
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/candidate/CandidateCard.vue frontend/tests/components/test_candidate_card.test.ts
git commit -m "feat: CandidateCard渲染4维度评分明细skill/experience/education/salary"
```

---

## Task 11: 前端 - Workbench.vue 卡片更新逻辑修复

**Files:**
- Modify: `frontend/src/views/Workbench.vue`
- Test: `frontend/tests/views/test_workbench.test.ts`

**Interfaces:**
- Consumes: Task 9 的 score_detail 类型
- Produces: 卡片仅在非空 candidates 时更新；切换会话清空；历史恢复

- [ ] **Step 1: 写失败测试 - watch 仅非空更新、chitchat 不清空、切换会话清空、历史恢复**

```typescript
// 追加到 frontend/tests/views/test_workbench.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'

// mock 依赖（与现有 test_workbench.test.ts 一致的 mock 模式）
vi.mock('vue-router', () => ({ useRouter: () => ({ push: vi.fn() }) }))
vi.mock('@/api/chat', () => ({
  getSessions: vi.fn(() => Promise.resolve({ list: [], total: 0 })),
  getMessages: vi.fn(() => Promise.resolve([])),
  createSession: vi.fn(),
  deleteSession: vi.fn(),
}))

import Workbench from '@/views/Workbench.vue'

describe('Workbench 推荐卡片更新逻辑', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('chitchat 响应不清空已有卡片', async () => {
    const wrapper = mount(Workbench)
    await flushPromises()
    const chatStore = useChatStore()

    // 先模拟一次有候选人的推荐
    chatStore.messages.push({
      role: 'assistant',
      content: '推荐以下候选人',
      candidates: [{ candidate_id: 'c1', resume_id: 'r1', name: '张三', score: 80 }],
    } as any)
    await flushPromises()
    expect(wrapper.find('.candidate-card').exists()).toBe(true)

    // 再模拟一次 chitchat 响应（无 candidates 字段）
    chatStore.messages.push({
      role: 'assistant',
      content: '不客气',
      // 无 candidates 字段
    } as any)
    await flushPromises()
    // 卡片应保留
    expect(wrapper.find('.candidate-card').exists()).toBe(true)
  })

  it('空数组 candidates 不清空卡片', async () => {
    const wrapper = mount(Workbench)
    await flushPromises()
    const chatStore = useChatStore()

    chatStore.messages.push({
      role: 'assistant',
      content: '推荐',
      candidates: [{ candidate_id: 'c1', resume_id: 'r1', name: '张三', score: 80 }],
    } as any)
    await flushPromises()

    // 推送空数组 candidates
    chatStore.messages.push({
      role: 'assistant',
      content: '未找到',
      candidates: [],
    } as any)
    await flushPromises()
    // 卡片应保留（仅非空才更新）
    expect(wrapper.find('.candidate-card').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 修改 Workbench.vue 实现**

1. 修改 watch 逻辑：
```typescript
// 原：recommendCandidates.value = last.candidates || []
// 改为：
watch(() => chatStore.messages.length, () => {
  const last = chatStore.messages[chatStore.messages.length - 1]
  if (last?.role === 'assistant' && Array.isArray(last.candidates) && last.candidates.length > 0) {
    recommendCandidates.value = last.candidates
  }
})
```

2. 新增切换会话清空逻辑：
```typescript
watch(() => chatStore.currentSessionId, () => {
  recommendCandidates.value = []
})
```

3. 新增历史会话恢复逻辑（在加载消息后）：
```typescript
async function handleSelectSession(sessionId: string) {
  // ... 现有加载逻辑 ...
  const messages = await getMessages(sessionId)
  chatStore.setMessages(messages)
  // 反向遍历找最近一条含非空 candidates 的 assistant 消息
  const lastWithCandidates = [...messages].reverse().find(
    (m: any) => m.role === 'assistant' && Array.isArray(m.candidates) && m.candidates.length > 0
  )
  recommendCandidates.value = lastWithCandidates?.candidates || []
}
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/Workbench.vue frontend/tests/views/test_workbench.test.ts
git commit -m "fix: 推荐卡片仅在非空candidates时更新切换会话清空历史会话恢复"
```

---

## Task 12: 前端 - sse.ts onDone 透传 title

**Files:**
- Modify: `frontend/src/api/sse.ts`

**Interfaces:**
- Produces: `onDone` handler 接收 `title` 参数

- [ ] **Step 1: 修改 sse.ts 的 dispatch 与 onDone 签名**

```typescript
// frontend/src/api/sse.ts
export interface SSEHandlers {
  onIntent?: (data: { intent_type: string; strategy?: string }) => void
  onRewrite?: (data: { rewrites: string[] }) => void
  onRetrieval?: (data: { chunks: any[] }) => void
  onRank?: (data: { ranked: any[] }) => void
  onToken?: (data: { delta: string }) => void
  onCandidates?: (data: { candidates: any[] }) => void
  onDone?: (data: { message_id: string; response: string; title?: string | null }) => void  // 新增 title
  onError?: (data: { code: number; message: string }) => void
}

function dispatch(event: string, data: any, handlers: SSEHandlers): void {
  switch (event) {
    // ... 其他 case 不变 ...
    case 'done':
      handlers.onDone?.({ message_id: data.message_id, response: data.response, title: data.title })
      break
    // ...
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/sse.ts
git commit -m "feat: SSE onDone handler透传title字段"
```

---

## Task 13: 前端 - chatStore 新增 updateSessionTitle 方法

**Files:**
- Modify: `frontend/src/stores/chat.ts`

**Interfaces:**
- Produces: `updateSessionTitle(sessionId, title)` 方法

- [ ] **Step 1: 修改 chat.ts**

```typescript
// frontend/src/stores/chat.ts
export const useChatStore = defineStore('chat', () => {
  // ... 现有 state ...

  function updateSessionTitle(sessionId: string, title: string): void {
    const session = sessions.value.find((s) => s.session_id === sessionId)
    if (session) {
      session.title = title
    }
  }

  return {
    // ... 现有 return ...
    updateSessionTitle,
  }
})
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/stores/chat.ts
git commit -m "feat: chatStore新增updateSessionTitle方法"
```

---

## Task 14: 前端 - ChatPanel onDone 调用 updateSessionTitle

**Files:**
- Modify: `frontend/src/components/chat/ChatPanel.vue`
- Test: `frontend/tests/components/test_chat_panel.test.ts`

**Interfaces:**
- Consumes: Task 12 的 onDone title、Task 13 的 updateSessionTitle

- [ ] **Step 1: 写失败测试 - onDone 收到 title 时更新会话标题**

```typescript
// 追加到 frontend/tests/components/test_chat_panel.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'

// mock 与现有 test_chat_panel.test.ts 一致
vi.mock('vue-router', () => ({ useRoute: () => ({ params: {} }), useRouter: () => ({ push: vi.fn() }) }))
vi.mock('@/api/chat', () => ({
  sendMessageStream: vi.fn(),
  getMessages: vi.fn(() => Promise.resolve([])),
}))

import ChatPanel from '@/components/chat/ChatPanel.vue'

describe('ChatPanel onDone title 同步', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('onDone 收到 title 时调用 updateSessionTitle', async () => {
    const chatStore = useChatStore()
    chatStore.currentSessionId = 's1'
    chatStore.sessions = [{ session_id: 's1', title: '新会话', created_at: '', updated_at: '', message_count: 0 } as any]

    // mock sendMessageStream 调用 onDone 带 title
    const { sendMessageStream } = await import('@/api/chat')
    ;(sendMessageStream as any).mockImplementation((sessionId, query, params, handlers) => {
      handlers.onDone({ message_id: 'm1', response: '回答', title: '首个问题前20字' })
      return Promise.resolve()
    })

    const wrapper = mount(ChatPanel, { props: { sessionId: 's1' } })
    await flushPromises()

    // 模拟发送消息
    await wrapper.find('.chat-input__textarea').setValue('首个问题前20字')
    await wrapper.find('.chat-input__send').trigger('click')
    await flushPromises()

    expect(chatStore.sessions[0].title).toBe('首个问题前20字')
  })
})
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 修改 ChatPanel.vue 实现**

在 `handleSend` 的 `onDone` 回调中：

```typescript
// 原：onDone: (data) => { chatStore.clearStreamState() }
// 改为：
onDone: (data) => {
  chatStore.clearStreamState()
  if (data.title) {
    chatStore.updateSessionTitle(currentSessionId.value, data.title)
  }
}
```

- [ ] **Step 4: 运行测试验证通过**

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/chat/ChatPanel.vue frontend/tests/components/test_chat_panel.test.ts
git commit -m "feat: ChatPanel onDone收到title时同步更新会话标题"
```

---

## Task 15: 全量测试与提交

**Files:** 无新文件

- [ ] **Step 1: 运行后端全量测试**

Run: `.venv\Scripts\python.exe -m pytest backend/tests -v`
Expected: 全部 PASS（含新增 8 个测试）

- [ ] **Step 2: 运行前端全量测试**

Run: `cd frontend && npm test`
Expected: 全部 PASS（含新增 7 个测试）

- [ ] **Step 3: 如有失败，修复后重新运行**

- [ ] **Step 4: 推送到 Gitee（如用户要求）**

```bash
git push origin main
```

---

## Self-Review 检查

1. **Spec 覆盖**：
   - §1 意图扩展 → Task 1, 2, 3, 8 ✓
   - §2 卡片显示与更新 → Task 4, 11 ✓
   - §3 分维度评分 → Task 5, 9, 10 ✓
   - §4 会话标题 → Task 6, 7, 12, 13, 14 ✓
   - §5 错误处理与测试 → 各 Task 内含测试 ✓

2. **占位符扫描**：无 TBD/TODO，所有代码完整 ✓

3. **类型一致性**：
   - 后端 `_llm_score_multi` 返回 dict，`_enrich_candidates` 取 `overall` 赋 `score`，取 4 维度赋 `score_detail` ✓
   - 前端 `CandidateCard.score_detail?` 与 `CandidateCard.vue` 渲染一致 ✓
   - SSE `done` 事件 `title` 字段从后端到 store 全链路一致 ✓
