# RAG 增强实施计划

**Goal:** 增强检索召回与精排质量，通过查询分解、多路召回、上下文压缩三模块提升候选人推荐准确率

**Architecture:** 在现有单 Agent 状态图上新增 `query_decompose` 节点（替代 `filter_extract`）和 `context_compress` 节点（精排后插入），`search_service.search()` 改造为多路召回（Route A/B/C），所有 LLM 调用有兜底回退现有逻辑

**Tech Stack:** Python 3.12 / LangGraph 0.2 / motor（MongoDB）/ pymilvus / 通义千问 LLM / pytest

## Global Constraints

- 启动用 `.venv\Scripts\python.exe`，不修改基础环境
- 所有 LLM 调用必须有 try/except + 日志 + 兜底回退
- 统一响应格式 `{code, message, data, trace_id}`
- 文件开头写元信息（文件名/创建时间/作者/功能描述）
- 每个函数/类写文档注释（入参/出参/核心逻辑）
- TDD：先写测试→见证失败→再实现
- 每个模块测试通过后才能 git commit

## File Structure

| 文件 | 变更类型 | 职责 |
|------|---------|------|
| `app/agent/prompts.py` | 修改 | 新增 QUERY_DECOMPOSE_PROMPT、CONTEXT_COMPRESS_PROMPT |
| `app/agent/nodes.py` | 修改 | 新增 query_decompose_node、context_compress_node；删除 filter_extract_node（合并进 decompose） |
| `app/agent/graph.py` | 修改 | 节点替换：filter_extract→decompose，精排后插入 compress |
| `app/core/strategy_selector.py` | 修改 | 新增 decompose 策略路由 |
| `app/services/search_service.py` | 修改 | 多路召回逻辑（Route A/B/C）、压缩 context 接入 |
| `app/agent/state.py` | 修改 | 新增 decomposed / compressed_context 字段 |
| `tests/agent/test_nodes.py` | 新增 | query_decompose、context_compress 单测 |
| `tests/services/test_search_service.py` | 新增 | 多路召回、压缩集成测试 |
| `tests/core/test_strategy_selector.py` | 新增 | decompose 策略测试 |

---

### Task 1: 新增 QUERY_DECOMPOSE_PROMPT

**Files:**
- Modify: `app/agent/prompts.py`（末尾追加）

**Interfaces:**
- Produces: `QUERY_DECOMPOSE_PROMPT` 模板，供 Task 3 的 query_decompose_node 使用

- [ ] **Step 1: 在 prompts.py 末尾追加 QUERY_DECOMPOSE_PROMPT**

```python
QUERY_DECOMPOSE_PROMPT = """你是招聘查询分解器。将用户查询分解为主查询、子查询列表和结构化过滤条件，以严格JSON返回。

要求：
1. main_query: 原始查询的核心语义版本（去除口语化词如"有没有"、"帮我找"）
2. sub_queries: 拆解出 1-3 个子查询，每个聚焦一个条件维度（技能/经验/岗位），用于多路召回
3. structured_filters: 提取硬性条件
   - required_skills: 技能关键词列表（小写），如 ["python", "docker"]
   - work_years_min: 最低工作年限（整数，无则不填）
   - salary_max: 最高期望薪资（K，整数，无则不填）
   - education_min: 最低学历等级（0=专科/1=本科/2=硕士/3=博士，无则不填）
   - job_type: 岗位类型（如"后端"/"前端"/"算法"，无则填空字符串）

示例：
查询"3年经验后端工程师会Python和Docker 30K以内"
{{
  "main_query": "后端工程师 Python Docker 3年经验 30K以内",
  "sub_queries": ["后端工程师 Python Docker", "3年经验后端开发", "Python Docker 微服务"],
  "structured_filters": {{
    "required_skills": ["python", "docker"],
    "work_years_min": 3,
    "salary_max": 30,
    "job_type": "后端"
  }}
}}

查询"有没有会html的"
{{
  "main_query": "html",
  "sub_queries": ["html 前端"],
  "structured_filters": {{
    "required_skills": ["html"],
    "job_type": "前端"
  }}
}}

查询"nlp相关的呢"
{{
  "main_query": "nlp",
  "sub_queries": ["nlp 自然语言处理", "bert transformer"],
  "structured_filters": {{
    "required_skills": ["nlp"],
    "job_type": "算法"
  }}
}}

现在分解以下查询，只返回JSON，不要其他文字：
查询：{query}
"""
```

- [ ] **Step 2: 验证 import 无报错**

Run: `.venv\Scripts\python.exe -c "from app.agent.prompts import QUERY_DECOMPOSE_PROMPT; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/agent/prompts.py
git commit -m "feat: 新增 QUERY_DECOMPOSE_PROMPT 查询分解提示词"
```

---

### Task 2: 新增 CONTEXT_COMPRESS_PROMPT

**Files:**
- Modify: `app/agent/prompts.py`（末尾追加）

**Interfaces:**
- Produces: `CONTEXT_COMPRESS_PROMPT` 模板，供 Task 4 的 context_compress_node 使用

- [ ] **Step 1: 在 prompts.py 末尾追加 CONTEXT_COMPRESS_PROMPT**

```python
CONTEXT_COMPRESS_PROMPT = """你是简历上下文压缩器。将同一简历的多个检索片段合并压缩为单一精炼摘要，聚焦于与查询的相关性。

要求：
1. 输出 ≤500 字
2. 聚焦三个维度：技能匹配点、经验匹配点、项目匹配点
3. 去除重复信息，保留关键事实（技能名、年限、公司、项目名）
4. 不要评价，只陈述事实

查询：{query}

简历片段（按相关性排序）：
{chunks_text}

只输出压缩后的摘要，不要其他文字：
"""
```

- [ ] **Step 2: 验证 import 无报错**

Run: `.venv\Scripts\python.exe -c "from app.agent.prompts import CONTEXT_COMPRESS_PROMPT; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/agent/prompts.py
git commit -m "feat: 新增 CONTEXT_COMPRESS_PROMPT 上下文压缩提示词"
```

---

### Task 3: AgentState 新增 decomposed / compressed_context 字段

**Files:**
- Modify: `app/agent/state.py:13-37`

**Interfaces:**
- Produces: `decomposed: dict`（查询分解结果）、`compressed_context: dict`（resume_id→压缩context映射）

- [ ] **Step 1: 在 AgentState TypedDict 中新增两个字段**

在 `state.py` 的 `AgentState` 类中，`ranked` 字段后追加：

```python
    ranked: list[dict]           # 重排后的结果
    decomposed: dict             # 查询分解结果（main_query/sub_queries/structured_filters）
    compressed_context: dict     # resume_id → 压缩后的 context 字符串
    candidates: list[dict]       # 候选人卡片
```

- [ ] **Step 2: 在 make_state 初始化新字段**

在 `make_state` 函数的 return 中，`ranked=[]` 后追加：

```python
        ranked=[],
        decomposed={},
        compressed_context={},
        candidates=last_candidates or [],
```

- [ ] **Step 3: 验证 import 无报错**

Run: `.venv\Scripts\python.exe -c "from app.agent.state import make_state; s=make_state('test','s1'); assert 'decomposed' in s; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add app/agent/state.py
git commit -m "feat: AgentState 新增 decomposed/compressed_context 字段"
```

---

### Task 4: 实现 query_decompose_node（替代 filter_extract_node）

**Files:**
- Modify: `app/agent/nodes.py`（新增函数，保留 _regex_extract_filters）
- Test: `tests/agent/test_nodes.py`（新增测试）

**Interfaces:**
- Consumes: `state.query`, `state.filters`, `state.intent_type`
- Produces: `{"filters": 合并后filters, "decomposed": 分解结果dict}`
- 替代: `filter_extract_node`（合并 filter 提取 + 查询分解为一步）

- [ ] **Step 1: 写失败测试**

在 `tests/agent/test_nodes.py` 末尾追加：

```python
@pytest.mark.asyncio
async def test_query_decompose_node_extracts_subqueries_and_filters():
    """query_decompose_node 应正确拆出 main_query/sub_queries/structured_filters"""
    from app.agent.nodes import query_decompose_node
    from unittest.mock import AsyncMock, patch

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
    from unittest.mock import AsyncMock, patch

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
```

- [ ] **Step 2: 运行测试验证失败**

Run: `.venv\Scripts\python.exe -m pytest tests/agent/test_nodes.py::test_query_decompose_node_extracts_subqueries_and_filters -xvs`
Expected: FAIL（ImportError: cannot import name 'query_decompose_node'）

- [ ] **Step 3: 实现 query_decompose_node**

在 `app/agent/nodes.py` 中，import 部分追加 `QUERY_DECOMPOSE_PROMPT`，并在 `filter_extract_node` 函数后新增：

```python
async def query_decompose_node(state: AgentState) -> dict:
    """节点1.5: 查询分解（替代 filter_extract_node，合并过滤提取+查询分解）

    在 intent_node 之后、retrieve_rank_node 之前执行。
    LLM 输出 main_query / sub_queries / structured_filters 三部分。
    structured_filters 合并到 state.filters（与正则提取的 filters 合并）。
    仅对 search 意图生效；其他意图不修改 filters。

    入参:
        state: AgentState（需含 query / filters / intent_type）
    出参:
        {"filters": 合并后filters, "decomposed": 分解结果dict}
    兜底:
        LLM 失败时 filters 走 _regex_extract_filters，decomposed 为空 dict
    """
    intent_type = state.get("intent_type", "search")
    if intent_type not in ("search", None):
        return {"filters": state.get("filters", {}), "decomposed": {}}

    query = state.get("query", "")
    if not query:
        return {"filters": state.get("filters", {}), "decomposed": {}}

    # 先正则兜底（与原 filter_extract_node 一致）
    regex_filters = _regex_extract_filters(query)
    merged = dict(state.get("filters", {}) or {})
    merged.update(regex_filters)

    decomposed: dict = {}
    try:
        prompt = QUERY_DECOMPOSE_PROMPT.format(query=query)
        resp = await llm_client.chat(
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.strip())
        decomposed = {
            "main_query": data.get("main_query", query),
            "sub_queries": data.get("sub_queries", [])[:3],  # 最多3个
            "structured_filters": data.get("structured_filters", {}),
        }
        # 合并 structured_filters 到 filters
        sf = decomposed["structured_filters"]
        for key in ("education_min", "work_years_min", "salary_max"):
            val = sf.get(key)
            if val is not None:
                try:
                    merged[key] = int(val)
                except (TypeError, ValueError):
                    pass
        llm_skills = sf.get("required_skills", [])
        if isinstance(llm_skills, list) and llm_skills:
            existing = set(merged.get("required_skills", []) or [])
            for s in llm_skills:
                if isinstance(s, str) and s.strip():
                    existing.add(s.strip().lower())
            merged["required_skills"] = list(existing)
        logger.info(
            f"查询分解: query='{query}' → sub_queries={decomposed['sub_queries']}, "
            f"filters={merged}"
        )
    except Exception as e:
        logger.warning(f"查询分解失败，回退正则提取: {e}, regex_filters={regex_filters}")

    return {"filters": merged, "decomposed": decomposed}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `.venv\Scripts\python.exe -m pytest tests/agent/test_nodes.py::test_query_decompose_node_extracts_subqueries_and_filters tests/agent/test_nodes.py::test_query_decompose_node_fallback_on_llm_failure tests/agent/test_nodes.py::test_query_decompose_node_skips_non_search_intent -xvs`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/agent/nodes.py tests/agent/test_nodes.py
git commit -m "feat: 实现 query_decompose_node 查询分解节点(替代filter_extract_node)"
```

---

### Task 5: graph.py 替换 filter_extract 为 decompose

**Files:**
- Modify: `app/agent/graph.py:12-19, 59-71`

**Interfaces:**
- Consumes: query_decompose_node from Task 4
- Produces: graph 中 filter_extract 节点替换为 decompose

- [ ] **Step 1: 修改 graph.py import 和节点注册**

将 `app/agent/graph.py` 的 import 部分（第 12-19 行）替换为：

```python
from app.agent.nodes import (
    intent_node,
    query_decompose_node,
    retrieve_rank_node,
    clarify_node,
    detail_node,
    respond_node,
)
```

将 `build_graph()` 中节点注册（第 60 行）替换：

```python
    workflow.add_node("decompose", query_decompose_node)
```

将 `_route_after_intent` 返回值（第 36 行）和条件边映射（第 67-71 行）中的 `"filter_extract"` 替换为 `"decompose"`：

```python
    # search / compare / qa 兜底走 decompose + retrieve_rank
    return "decompose"
```

```python
    workflow.add_conditional_edges("intent", _route_after_intent, {
        "decompose": "decompose",
        "detail": "detail",
        "respond": "respond",
    })
    workflow.add_edge("decompose", "retrieve_rank")
```

- [ ] **Step 2: 运行 agent 相关测试验证不破坏**

Run: `.venv\Scripts\python.exe -m pytest tests/agent/ -xvs`
Expected: 全部 passed

- [ ] **Step 3: Commit**

```bash
git add app/agent/graph.py
git commit -m "refactor: graph 节点 filter_extract 替换为 decompose"
```

---

### Task 6: 实现 context_compress_node

**Files:**
- Modify: `app/agent/nodes.py`（新增函数）
- Test: `tests/agent/test_nodes.py`（新增测试）

**Interfaces:**
- Consumes: `state.chunks`（精排后的 chunks 列表）、`state.query`
- Produces: `{"compressed_context": {resume_id: 压缩后context字符串}}`
- 位置: 在 retrieve_rank_node 之后（精排完成、送 enrich 之前）

- [ ] **Step 1: 写失败测试**

在 `tests/agent/test_nodes.py` 末尾追加：

```python
@pytest.mark.asyncio
async def test_context_compress_node_merges_multi_chunks():
    """同一 resume_id 的多个 chunks 应压缩为单一 context"""
    from app.agent.nodes import context_compress_node
    from unittest.mock import AsyncMock, patch

    chunks = [
        {"candidate_id": "r1", "parent_content": "张三，5年Python开发，会Django", "rerank_score": 0.9},
        {"candidate_id": "r1", "parent_content": "张三做过电商后端项目，用Flask", "rerank_score": 0.7},
        {"candidate_id": "r2", "parent_content": "李四，3年Java", "rerank_score": 0.8},
    ]
    state = {"query": "Python后端", "chunks": chunks}

    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(return_value="张三：5年Python，会Django/Flask，电商后端项目经验")
        result = await context_compress_node(state)

    assert "compressed_context" in result
    ctx_map = result["compressed_context"]
    # r1 有2个chunks，应被压缩
    assert "r1" in ctx_map
    assert "张三" in ctx_map["r1"]
    # r2 只有1个chunk，不压缩，直接用原 parent_content
    assert "r2" in ctx_map
    assert ctx_map["r2"] == "李四，3年Java"


@pytest.mark.asyncio
async def test_context_compress_node_fallback_on_llm_failure():
    """LLM 压缩失败时回退取最高分 chunk 的 parent_content"""
    from app.agent.nodes import context_compress_node
    from unittest.mock import AsyncMock, patch

    chunks = [
        {"candidate_id": "r1", "parent_content": "张三5年Python", "rerank_score": 0.9},
        {"candidate_id": "r1", "parent_content": "张三Flask项目", "rerank_score": 0.5},
    ]
    state = {"query": "Python", "chunks": chunks}

    with patch("app.agent.nodes.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=Exception("LLM 失败"))
        result = await context_compress_node(state)

    ctx_map = result["compressed_context"]
    # 兜底：用最高分 chunk 的 parent_content
    assert ctx_map["r1"] == "张三5年Python"


@pytest.mark.asyncio
async def test_context_compress_node_empty_chunks():
    """无 chunks 时返回空 dict"""
    from app.agent.nodes import context_compress_node

    state = {"query": "test", "chunks": []}
    result = await context_compress_node(state)
    assert result["compressed_context"] == {}
```

- [ ] **Step 2: 运行测试验证失败**

Run: `.venv\Scripts\python.exe -m pytest tests/agent/test_nodes.py::test_context_compress_node_merges_multi_chunks -xvs`
Expected: FAIL（ImportError: cannot import name 'context_compress_node'）

- [ ] **Step 3: 实现 context_compress_node**

在 `app/agent/nodes.py` 中 import 部分追加 `CONTEXT_COMPRESS_PROMPT`，在 `query_decompose_node` 后新增：

```python
async def context_compress_node(state: AgentState) -> dict:
    """节点2.5: 上下文压缩（精排后、硬过滤前）

    对同一 resume_id 的多个 chunks 用 LLM 压缩为单一精炼 context（≤500字）。
    只对命中 ≥2 chunks 的 resume 压缩；单 chunk 直接用原 parent_content。
    LLM 失败时回退取最高分 chunk 的 parent_content。

    入参:
        state: AgentState（需含 chunks / query）
    出参:
        {"compressed_context": {resume_id: 压缩后context字符串}}
    """
    chunks = state.get("chunks", []) or []
    query = state.get("query", "")
    if not chunks:
        return {"compressed_context": {}}

    # 按 resume_id 分组
    groups: dict[str, list[dict]] = {}
    for c in chunks:
        rid = c.get("candidate_id", "")
        if not rid:
            continue
        groups.setdefault(rid, []).append(c)

    compressed: dict[str, str] = {}

    async def _compress_one(rid: str, rchunks: list[dict]) -> tuple[str, str]:
        """压缩单个简历的多 chunks"""
        if len(rchunks) <= 1:
            return rid, rchunks[0].get("parent_content", "")
        # 按rerank_score降序拼接
        sorted_chunks = sorted(rchunks, key=lambda x: x.get("rerank_score", 0), reverse=True)
        chunks_text = "\n---\n".join(
            c.get("parent_content", "") for c in sorted_chunks if c.get("parent_content")
        )
        try:
            prompt = CONTEXT_COMPRESS_PROMPT.format(query=query, chunks_text=chunks_text)
            resp = await llm_client.chat([{"role": "user", "content": prompt}])
            compressed_text = resp.strip()[:500]  # 硬截断500字
            logger.info(f"上下文压缩: resume_id={rid}, {len(rchunks)} chunks → {len(compressed_text)} 字")
            return rid, compressed_text
        except Exception as e:
            logger.warning(f"上下文压缩失败，回退最高分chunk: resume_id={rid}, {e}")
            return rid, sorted_chunks[0].get("parent_content", "")

    # 并发压缩
    import asyncio
    results = await asyncio.gather(*[_compress_one(rid, rchs) for rid, rchs in groups.items()])
    for rid, ctx in results:
        compressed[rid] = ctx

    return {"compressed_context": compressed}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `.venv\Scripts\python.exe -m pytest tests/agent/test_nodes.py::test_context_compress_node_merges_multi_chunks tests/agent/test_nodes.py::test_context_compress_node_fallback_on_llm_failure tests/agent/test_nodes.py::test_context_compress_node_empty_chunks -xvs`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/agent/nodes.py tests/agent/test_nodes.py
git commit -m "feat: 实现 context_compress_node 上下文压缩节点"
```

---

### Task 7: search_service 多路召回（Route A/B/C）

**Files:**
- Modify: `app/services/search_service.py:86-140`（替换多改写检索循环为多路召回）
- Test: `tests/services/test_search_service.py`（新增测试）

**Interfaces:**
- Consumes: `decomposed` dict（从 AgentState 传入，含 main_query/sub_queries/structured_filters）
- Produces: 多路召回合并的 unique_chunks
- 新增参数: `decomposed: dict = None`

- [ ] **Step 1: 写失败测试**

在 `tests/services/test_search_service.py` 末尾追加：

```python
@pytest.mark.asyncio
async def test_search_multi_route_with_decomposed():
    """多路召回：传入 decomposed 时应触发 Route A/B/C 三路检索"""
    svc = SearchService()
    svc.embedding = MagicMock()
    svc.embedding.encode = MagicMock(return_value=([[0.1] * 1024], [{}]))
    svc.reranker = MagicMock()
    svc.reranker.rerank = MagicMock(return_value=[0.9])
    svc.vector_store = AsyncMock()
    # Route A 命中 r1, Route B 命中 r2, Route C MongoDB 命中 r3
    svc.vector_store.hybrid_search = AsyncMock(side_effect=[
        [{"chunk_id": "c1", "candidate_id": "r1", "score": 0.9, "parent_content": "Python 5年"}],
        [{"chunk_id": "c2", "candidate_id": "r2", "score": 0.8, "parent_content": "Docker 微服务"}],
    ])
    svc.strategy_selector = AsyncMock()
    svc.strategy_selector.select = AsyncMock(return_value="direct")
    svc.strategy_selector.rewrite = AsyncMock(return_value=["main query"])
    svc.resumes_coll = MagicMock()
    # Route C MongoDB 查询返回 r3
    svc.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[
        {"resume_id": "r3", "candidate_id": "c3", "name": "王五", "skills": ["python", "docker"],
         "work_years": 3, "education": "本科", "education_level": 1,
         "expected_salary": {"min": 20, "max": 30}, "tags": [], "is_favorite": False}
    ])
    svc.redis = AsyncMock()
    svc.redis.get = AsyncMock(return_value=None)
    svc.redis.setex = AsyncMock()

    decomposed = {
        "main_query": "后端工程师 Python Docker 3年经验",
        "sub_queries": ["Python Docker"],
        "structured_filters": {"required_skills": ["python", "docker"], "work_years_min": 3}
    }

    _score_json = json.dumps({"skill": 85, "experience": 80, "education": 75, "salary": 85, "overall": 0, "reason": "匹配"})
    with patch("app.services.search_service.llm_client") as mock_llm:
        mock_llm.chat = AsyncMock(side_effect=[_score_json, _score_json, _score_json])
        results = await svc.search(
            "后端工程师 Python Docker 3年",
            filters={},
            top_k=10,
            decomposed=decomposed,
        )

    # 应返回多个候选人（Route A 的 r1 + Route C 的 r3）
    names = [r.get("name") for r in results]
    assert len(results) >= 1
    # vector_store 至少被调用2次（Route A + Route B）
    assert svc.vector_store.hybrid_search.call_count >= 2
```

- [ ] **Step 2: 运行测试验证失败**

Run: `.venv\Scripts\python.exe -m pytest tests/services/test_search_service.py::test_search_multi_route_with_decomposed -xvs`
Expected: FAIL（search() 不接受 decomposed 参数）

- [ ] **Step 3: 修改 search() 签名与多路召回逻辑**

在 `app/services/search_service.py` 中，`search` 方法签名追加 `decomposed: dict = None` 参数：

```python
    async def search(
        self,
        query: str,
        filters: dict,
        top_k: int = 10,
        history: list[dict] = None,
        decomposed: dict = None,
    ) -> list[dict]:
```

将原"多改写检索"循环（约第 116-140 行）替换为多路召回逻辑：

```python
        # 多路召回：Route A（主查询）+ Route B（子查询）+ Route C（MongoDB 结构化保底）
        all_chunks: list[dict] = []

        # Route A: 主查询 hybrid_search（若 decomposed 有 main_query 用它，否则走 strategy_selector）
        route_a_queries = [query]
        if decomposed and decomposed.get("main_query"):
            route_a_queries = [decomposed["main_query"]]
        else:
            strategy = await self.strategy_selector.select(query, history)
            rewrites = await self.strategy_selector.rewrite(query, strategy, history)
            route_a_queries = rewrites
            logger.info(f"检索策略={strategy}, 改写={rewrites}")

        retrieve_per_query = max(settings.RETRIEVE_TOP_K, top_k * 5)

        for rq in route_a_queries:
            dense, sparse = self.embedding.encode([rq])
            chunks = await self.vector_store.hybrid_search(
                dense, sparse, filters=filters, top_k=retrieve_per_query
            )
            all_chunks.extend(chunks)

        # Route B: 子查询独立检索（若 decomposed 提供）
        sub_queries = (decomposed or {}).get("sub_queries", []) if decomposed else []
        for sq in sub_queries[:3]:
            dense, sparse = self.embedding.encode([sq])
            chunks = await self.vector_store.hybrid_search(
                dense, sparse, filters=filters, top_k=retrieve_per_query // 3
            )
            all_chunks.extend(chunks)
            logger.info(f"Route B 子查询召回: '{sq[:30]}' → {len(chunks)} chunks")

        # Route C: MongoDB 结构化保底（按 required_skills + work_years/edu 查 MongoDB）
        if decomposed and decomposed.get("structured_filters"):
            sf = decomposed["structured_filters"]
            mongo_hits = await self._mongo_structured_recall(sf, retrieve_per_query // 2)
            if mongo_hits:
                logger.info(f"Route C MongoDB 结构化保底召回 {len(mongo_hits)} chunks")
                for c in mongo_hits:
                    c["rerank_score"] = 0.0  # 兜底分，让 Reranker 重打
                all_chunks.extend(mongo_hits)

        # chunk_id 去重
        seen_chunk_ids: set[str] = set()
        unique_chunks: list[dict] = []
        for c in all_chunks:
            cid = c.get("chunk_id")
            if cid and cid not in seen_chunk_ids:
                seen_chunk_ids.add(cid)
                unique_chunks.append(c)
        logger.info(f"去重后 chunk 数: {len(unique_chunks)}")
```

在类中新增 `_mongo_structured_recall` 方法（在 `_enrich_candidates` 前插入）：

```python
    async def _mongo_structured_recall(self, sf: dict, limit: int) -> list[dict]:
        """Route C: MongoDB 结构化保底召回

        按 structured_filters 的 required_skills / work_years_min / education_min
        在 MongoDB 查匹配的简历，返回其 chunk 格式（candidate_id + parent_content）。

        入参:
            sf: structured_filters dict
            limit: 最多返回数量
        出参:
            [{"candidate_id", "parent_content", "chunk_id": "mongo_<rid>"}]
        """
        try:
            query: dict = {}
            skills = sf.get("required_skills", [])
            if skills:
                query["skills"] = {"$regex": "|".join(s.lower() for s in skills), "$options": "i"}
            years_min = sf.get("work_years_min")
            if years_min is not None:
                query["work_years"] = {"$gte": years_min}
            edu_min = sf.get("education_min")
            if edu_min is not None:
                query["education_level"] = {"$gte": edu_min}

            if not query:
                return []

            cursor = self.resumes_coll.find(query).limit(limit)
            docs = await cursor.to_list(length=limit)
            logger.info(f"Route C MongoDB 查询: {query} → {len(docs)} 条")
            return [
                {
                    "candidate_id": d.get("resume_id", ""),
                    "parent_content": d.get("summary", "") or d.get("name", "") + " " + " ".join(d.get("skills", []) or []),
                    "chunk_id": f"mongo_{d.get('resume_id', '')}",
                }
                for d in docs
            ]
        except Exception as e:
            logger.warning(f"Route C MongoDB 保底召回失败: {e}")
            return []
```

- [ ] **Step 4: 运行测试验证通过**

Run: `.venv\Scripts\python.exe -m pytest tests/services/test_search_service.py::test_search_multi_route_with_decomposed -xvs`
Expected: passed

- [ ] **Step 5: 运行全部 search_service 测试验证无回归**

Run: `.venv\Scripts\python.exe -m pytest tests/services/test_search_service.py -xvs`
Expected: 全部 passed

- [ ] **Step 6: Commit**

```bash
git add app/services/search_service.py tests/services/test_search_service.py
git commit -m "feat: search_service 多路召回(Route A/B/C) + decomposed参数"
```

---

### Task 8: search_service 接入压缩 context

**Files:**
- Modify: `app/services/search_service.py:160-190`（压缩 context 传入 enrich）

**Interfaces:**
- Consumes: 压缩后的 context map（从 retrieve_rank_node 传入）
- Produces: `_enrich_candidates` 的 chunk_map 使用压缩 context

- [ ] **Step 1: 修改 _enrich_candidates 签名追加 compressed_context 参数**

在 `app/services/search_service.py` 的 `_enrich_candidates` 方法签名追加参数：

```python
    async def _enrich_candidates(
        self,
        candidate_ids: list[str],
        query: str,
        chunks: list[dict],
        filters: dict,
        compressed_context: dict = None,
    ) -> list[dict]:
```

在 `_enrich_candidates` 内构建 `chunk_map` 处（约第 235 行），优先使用压缩 context：

```python
        chunk_map = {c.get("candidate_id"): c for c in chunks}
        # 若有压缩 context，覆盖 chunk 的 parent_content
        if compressed_context:
            for rid, ctx in compressed_context.items():
                if rid in chunk_map:
                    chunk_map[rid]["parent_content"] = ctx
                else:
                    chunk_map[rid] = {"candidate_id": rid, "parent_content": ctx, "rerank_score": 0.0}
```

在 `search()` 方法调用 `_enrich_candidates` 处（约第 190 行）传入 `compressed_context`：

```python
        results = await self._enrich_candidates(
            candidate_ids, query, candidate_chunks, filters,
            compressed_context=compressed_context,
        )
```

在 `search()` 方法签名追加 `compressed_context: dict = None` 参数：

```python
    async def search(
        self,
        query: str,
        filters: dict,
        top_k: int = 10,
        history: list[dict] = None,
        decomposed: dict = None,
        compressed_context: dict = None,
    ) -> list[dict]:
```

- [ ] **Step 2: 运行全部 search_service 测试验证无回归**

Run: `.venv\Scripts\python.exe -m pytest tests/services/test_search_service.py -xvs`
Expected: 全部 passed

- [ ] **Step 3: Commit**

```bash
git add app/services/search_service.py
git commit -m "feat: search_service 接入压缩 context 到 _enrich_candidates"
```

---

### Task 9: retrieve_rank_node 接入 decompose + compress

**Files:**
- Modify: `app/agent/nodes.py:164-182`（retrieve_rank_node 调用 search 时传 decomposed + compressed_context）

**Interfaces:**
- Consumes: state.decomposed, state.compressed_context
- Produces: search() 调用带 decomposed + compressed_context 参数

- [ ] **Step 1: 修改 retrieve_rank_node**

将 `retrieve_rank_node` 中调用 `search_service.search` 的部分改为：

```python
async def retrieve_rank_node(state: AgentState) -> dict:
    """节点2: 检索+精排（多路召回+压缩 context）

    入参:
        state: AgentState（需含 query / filters / history / decomposed / compressed_context）
    出参:
        {"candidates": [...]}
    """
    try:
        # 上下文压缩（若有 chunks 且未压缩）
        compressed_context = state.get("compressed_context", {}) or {}
        if not compressed_context and state.get("chunks"):
            compress_result = await context_compress_node(state)
            compressed_context = compress_result.get("compressed_context", {})

        candidates = await search_service.search(
            query=state["query"],
            filters=state.get("filters", {}),
            top_k=20,
            history=state.get("history", []),
            decomposed=state.get("decomposed", {}),
            compressed_context=compressed_context,
        )
    except Exception as e:
        logger.error(f"检索失败: {e}", exc_info=True)
        candidates = []
    return {"candidates": candidates}
```

- [ ] **Step 2: 运行 agent 测试验证**

Run: `.venv\Scripts\python.exe -m pytest tests/agent/ -xvs`
Expected: 全部 passed

- [ ] **Step 3: Commit**

```bash
git add app/agent/nodes.py
git commit -m "feat: retrieve_rank_node 接入 decompose + compress"
```

---

### Task 10: E2E 测试验证全流程

**Files:**
- Test: `tests/e2e/test_chat_scenarios.py`（新增多路召回场景测试）

- [ ] **Step 1: 新增多条件查询 E2E 测试**

在 `tests/e2e/test_chat_scenarios.py` 末尾追加：

```python
def test_multi_condition_query_decomposes_and_recalls(e2e_env):
    """E2E: 多条件查询应触发查询分解+多路召回"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    e2e_env["llm_chat_responses"][:] = [
        "search",  # 意图识别
        json.dumps({
            "main_query": "后端工程师 Python 3年经验",
            "sub_queries": ["Python 后端", "3年经验开发"],
            "structured_filters": {"required_skills": ["python"], "work_years_min": 3}
        }, ensure_ascii=False),
        "90",  # 评分
        "匹配度高",  # 理由
    ]
    e2e_env["llm_chat_call_count"]["i"] = 0

    r = client.post("/api/v1/chat/sessions", json={"title": "多条件测试"}, headers=_auth_header(token))
    session_id = r.json()["data"]["session_id"]

    with client.stream("POST", f"/api/v1/chat/sessions/{session_id}/messages",
                       json={"query": "3年经验后端工程师会Python"},
                       headers=_auth_header(token)) as response:
        assert response.status_code == 200
        full_text = ""
        for chunk in response.iter_text():
            full_text += chunk

    events = parse_sse_events(full_text)
    event_names = [e["event"] for e in events]
    assert "intent" in event_names
    assert "done" in event_names
```

- [ ] **Step 2: 运行 E2E 测试**

Run: `.venv\Scripts\python.exe -m pytest tests/e2e/test_chat_scenarios.py -xvs`
Expected: 全部 passed

- [ ] **Step 3: 运行全量测试**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: 全部 passed

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/test_chat_scenarios.py
git commit -m "test: 新增多条件查询 E2E 测试场景"
```

---

### Task 11: 更新 README + 最终提交

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 在 README 技术亮点部分追加 RAG 增强说明**

在"同义词扩展检索"技术亮点后追加：

```markdown
- **查询分解（Query Decomposition）**：复杂多条件查询用 LLM 拆为主查询+子查询+结构化过滤条件，子查询用于多路召回独立检索，结构化条件用于硬过滤保底
- **多路召回（Multi-Route Retrieval）**：Route A 主查询 Hybrid 检索 + Route B 子查询独立检索 + Route C MongoDB 结构化精确匹配保底，三路合并去重送 Reranker，解决多条件向量稀释与漏召回
- **上下文压缩（Context Compression）**：同一简历多个 chunks 命中时用 LLM 压缩为单一精炼摘要（≤500字），并发执行，让 LLM 评分基于完整相关 context
```

- [ ] **Step 2: 更新测试计数**

更新 README 中的测试总数（+5 个新测试）。

- [ ] **Step 3: 运行全量测试确认**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: 全部 passed

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: 更新 README 新增 RAG 增强(查询分解/多路召回/上下文压缩)说明"
```

---

## Self-Review

- **Spec 覆盖**: 模块1→Task 1/3/4/5, 模块2→Task 7, 模块3→Task 6/8/9, E2E→Task 10, 文档→Task 11 ✓
- **Placeholder 扫描**: 无 TBD/TODO，每个 step 有完整代码 ✓
- **类型一致性**: search() 签名在 Task 7/8 一致，decomposed/compressed_context 字段在 state/nodes/service 间传递一致 ✓
- **兜底机制**: 模块1 LLM失败→正则(Task 4), 模块2 Route C失败→跳过(Task 7), 模块3 LLM失败→最高分chunk(Task 6) ✓
