<!--
  文件名: 2026-06-27-workbench-recommend-and-intent-design.md
  创建时间: 2026-06-27
  作者: TalentSense Team
  功能描述: 工作台推荐候选人卡片、意图识别扩展、分维度评分、会话标题自动命名设计文档
-->
# 工作台推荐与意图优化设计

## 背景与问题

工作台（Workbench）当前存在 5 个问题：

1. **初次推荐没有卡片**：输入明确的推荐请求（如"推荐前端工程师"），右侧推荐区始终显示"对话后将显示推荐候选人"空状态
2. **追问时卡片消失**：追问（如"再推荐几个"）后右侧卡片被清空，期望"意图识别在下次推荐时才更新卡片"
3. **其他问题都围绕简历**：意图识别仅 4 类（chitchat/search/detail/compare），非 chitchat 全走简历检索，导致 HR 知识问答/系统使用帮助等被误导向简历
4. **分数判断依据不透明**：`_llm_score` 用 `SCORE_PROMPT` 让 LLM"只返回数字"，无量化维度，黑盒不可解释
5. **会话名称永远"新会话"**：`create_session` 写死"新会话"，`_save_message` 不更新 title，无重命名 API

## 设计方案（方案 A）

复杂度适中，完整解决 5 个问题，不引入过度抽象。改动集中在 prompts.py / agent_service.py / search_service.py / Workbench.vue 等少量文件。

---

## §1 意图扩展（新增 `qa` 意图）

### 改动文件
- `backend/app/agent/prompts.py`
- `backend/app/agent/nodes.py`
- `backend/app/services/agent_service.py`
- `frontend/src/utils/constant.ts`

### 设计要点

1. **`INTENT_PROMPT` 改写为 5 类意图分类**：
   - `chitchat`: 打招呼/寒暄（你好/谢谢/你是谁）
   - `search`: 搜索/推荐候选人
   - `detail`: 查询某候选人详情
   - `compare`: 对比候选人
   - `qa`: HR 知识问答/系统使用帮助/通用问答（不涉及具体候选人推荐）

2. **`nodes.py` `intent_node`**：白名单新增 `qa`，兜底改为 `qa`（而非 `chitchat`），让兜底也能通用回答

3. **`agent_service.py` `send_message_stream`**：
   - `qa` 分支：跳过检索，用新 `QA_PROMPT` 通用回答
   - `QA_PROMPT` 设计：作为 HR 招聘助手，可回答 HR 流程/系统使用/通用问题，**不编造候选人**，涉及具体候选人时引导用户用"推荐"语句

4. **前端 `INTENT_TYPES`**：新增 `qa: '通用问答'`

---

## §2 推荐候选人卡片显示与更新逻辑

### 改动文件
- `frontend/src/views/Workbench.vue`
- `frontend/src/components/chat/ChatPanel.vue`
- `backend/app/services/agent_service.py`（检索为空时仍 yield candidates 事件）

### 核心原则
卡片只在"产生新的推荐结果"时更新，不在"非推荐响应"时清空。

### 1. 初次推荐没有卡片（bug 排查与修复）

**可能根因**：
- 后端意图误判为 chitchat，未触发检索
- 检索返回空（向量库无数据/检索失败）
- SSE `candidates` 事件未 yield 或事件名不匹配
- 前端 `onCandidates` 回调未正确写入消息 `candidates` 字段

**修复策略**：
- 后端：`retrieve_rank_node` 返回空列表时，仍 yield `candidates` 事件（空数组），前端据此显示"未找到匹配候选人"提示，便于区分"没触发检索"和"检索为空"
- 前端：`Workbench.vue` 的 watch 增加日志，确认 `last.candidates` 是否为 `undefined`（未触发检索）vs `[]`（检索为空）

### 2. 追问时卡片消失（逻辑修复）

**当前问题代码**（`Workbench.vue`）：
```ts
watch(() => chatStore.messages.length, () => {
  const last = chatStore.messages[chatStore.messages.length - 1]
  if (last && last.role === 'assistant') {
    recommendCandidates.value = last.candidates || []  // ← undefined → []，清空了卡片
  }
})
```

**改为**：只在 `last.candidates` 是非空数组时更新；`undefined`/`null`/`[]` 都保留上一次卡片。
```ts
watch(() => chatStore.messages.length, () => {
  const last = chatStore.messages[chatStore.messages.length - 1]
  if (last?.role === 'assistant' && Array.isArray(last.candidates) && last.candidates.length > 0) {
    recommendCandidates.value = last.candidates
  }
})
```

### 3. 切换会话时清空

`Workbench.vue` 监听 `currentSessionId` 变化时，重置 `recommendCandidates = []`。

### 4. 历史会话恢复卡片

`getMessages` 加载历史后，反向遍历找最近一条 `candidates` 非空的 assistant 消息，赋值给 `recommendCandidates`。

---

## §3 分维度评分与透明化

### 改动文件
- `backend/app/agent/prompts.py`
- `backend/app/services/search_service.py`
- `backend/app/models/chat.py`（candidates 字段结构）
- `frontend/src/types/candidate.ts`
- `frontend/src/components/candidate/CandidateCard.vue`

### 1. `SCORE_PROMPT` 改为返回 JSON

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

### 2. `_llm_score` 改为 `_llm_score_multi`

- 解析 JSON，返回 `{skill, experience, education, salary, overall, reason}` 字典
- `overall` 由 LLM 给出（综合判断），失败时按 `0.3*skill + 0.3*experience + 0.2*education + 0.2*salary` 加权计算
- LLM 调用失败兜底：4 维度全部回退 `rerank_score*100`，`reason="基于语义相似度匹配"`
- 强制 `response_format={"type":"json_object"}`（与简历提取一致）

### 3. candidates 字段结构升级

```python
# search_service.py _enrich_candidates 输出
{
    "candidate_id": "...",
    "resume_id": "...",
    "name": "...",
    "score": 78,                    # 综合分（向后兼容）
    "score_detail": {               # 新增
        "skill": 85,
        "experience": 70,
        "education": 90,
        "salary": 60
    },
    "reason": "技能高度匹配，但薪资期望偏高",  # 复用原 reason 字段
    # ... 其他字段不变
}
```

### 4. 前端展示

- `CandidateCard` 类型新增 `score_detail?: { skill, experience, education, salary }`
- 卡片 UI：保留总分大字 + 星级；新增 4 个维度小条形图（或 4 个小胶囊），hover 显示维度名
- 评分理由 `reason` 现有字段，已在卡片底部展示，无需改结构

### 5. 向后兼容

- 老数据 `score_detail` 缺失时，前端仅显示总分，不显示维度明细
- 后端 `score` 字段保留，不破坏现有 API 契约

---

## §4 会话标题改为首个问题

### 改动文件
- `backend/app/services/agent_service.py`
- `backend/app/models/chat.py`
- `frontend/src/views/Workbench.vue`
- `frontend/src/components/chat/ChatPanel.vue`
- `frontend/src/api/sse.ts`
- `frontend/src/stores/chat.ts`

### 1. 创建会话时不再写死标题

`create_session(user_id, title="新会话")` 保留默认值作为占位，实际标题在首条消息发送后由后端自动更新。

### 2. `_save_message` 自动更新标题

```python
async def _save_message(self, session_id, user_msg, assistant_msg, query):
    # 检查是否首条消息
    session = await self.sessions_coll.find_one({"session_id": session_id}, {"messages": 1})
    update = {
        "$push": {"messages": {"$each": [user_msg, assistant_msg], "$slice": -20}},
        "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
    }
    # 首条消息自动更新标题
    if not session.get("messages"):
        update["$set"]["title"] = query[:20].strip() or "新会话"
    await self.sessions_coll.update_one({"session_id": session_id}, update)
```

### 3. SSE `done` 事件返回标题

当标题更新时，`done` 事件 payload 增加 `title` 字段：
```python
yield _sse_event("done", {
    "message_id": assistant_msg["message_id"],
    "response": assistant_msg["content"],
    "title": new_title  # 新增，仅首条消息时非 None
})
```

### 4. 前端同步

- `sse.ts` 的 `onDone` handler 增加 `title` 参数透传
- `ChatPanel.vue` 在 `onDone` 中若收到 `title`，调用 `chatStore.updateSessionTitle(sessionId, title)`
- `chatStore` 新增 `updateSessionTitle(sessionId, title)` 方法更新 `sessions` 数组中对应项
- `SessionList.vue` 无需改动，已通过 `s.title` 渲染

### 5. 历史会话加载

`getSessions` 已返回 title 字段，无需额外处理。

---

## §5 错误处理与测试

### 1. 错误处理

- **意图识别失败**：`intent_node` LLM 调用异常 → 兜底 `qa`（而非 `chitchat`），用 `QA_PROMPT` 通用回答
- **检索返回空**：仍 yield `candidates` 空数组事件，前端右侧显示"未找到匹配候选人"提示，不清空上一次卡片（按 §2 逻辑）
- **评分 LLM 失败**：4 维度全部回退 `rerank_score×100`，`reason="基于语义相似度匹配"`，不抛异常
- **评分 JSON 解析失败**：尝试提取数字兜底为单一分数，4 维度赋同值；仍失败则全 0 + `reason="评分暂不可用"`
- **标题更新失败**：`_save_message` 中标题更新异常不阻塞消息保存，记录日志，标题保留"新会话"
- **SSE 流式中途异常**：沿用现有 `yield _sse_event("error", {...})` 兜底

### 2. 测试覆盖

**后端单元测试**（遵循现有 mock 模式，避免 `AsyncMock` 陷阱）：
- `test_intent_node_qa`：qa 意图分类
- `test_send_message_stream_qa_branch`：qa 分支不触发检索，走 `QA_PROMPT`
- `test_llm_score_multi_json_parse`：正常 JSON 解析
- `test_llm_score_multi_fallback_rerank`：LLM 失败回退 rerank_score
- `test_llm_score_multi_fallback_zero`：JSON 解析失败全 0 兜底
- `test_save_message_updates_title_on_first`：首条消息更新标题
- `test_save_message_no_title_update_on_subsequent`：非首条不更新标题
- `test_retrieve_empty_yields_candidates_event`：检索为空仍 yield candidates 事件

**前端单元测试**（Vitest + @vue/test-utils）：
- `test_recommend_candidates_update_only_on_nonempty`：watch 仅在非空时更新
- `test_recommend_candidates_preserved_on_chitchat`：chitchat 响应不清空卡片
- `test_switch_session_clears_recommend`：切换会话清空卡片
- `test_restore_candidates_from_history`：历史会话恢复最近一次卡片
- `test_candidate_card_score_detail_render`：score_detail 维度展示
- `test_candidate_card_score_detail_missing`：老数据无 score_detail 仅显示总分
- `test_session_title_update_on_done`：done 事件携带 title 时更新会话标题

### 3. 集成验证（手动）

- 输入"推荐前端工程师" → 右侧出现卡片 + 4 维度评分
- 追问"谢谢" → 卡片保留，右侧不变
- 问"HR 怎么筛选候选人" → 走 qa 分支，不返回卡片，不清空已有卡片
- 新建会话发首条消息 → 会话列表标题更新为问题前 20 字
- 切换到历史会话 → 右侧恢复该会话最近一次推荐卡片

---

## 改动文件清单

| 层级 | 文件 | 改动内容 |
|---|---|---|
| 后端 | `backend/app/agent/prompts.py` | INTENT_PROMPT 改 5 类；新增 QA_PROMPT；SCORE_PROMPT 改 JSON |
| 后端 | `backend/app/agent/nodes.py` | intent_node 白名单加 qa，兜底改 qa |
| 后端 | `backend/app/services/agent_service.py` | qa 分支；检索空仍 yield candidates；_save_message 首条更新标题；done 事件带 title |
| 后端 | `backend/app/services/search_service.py` | _llm_score → _llm_score_multi；candidates 增加 score_detail |
| 后端 | `backend/app/models/chat.py` | candidates 字段结构注释更新 |
| 后端 | `backend/tests/...` | 8 个新单元测试 |
| 前端 | `frontend/src/utils/constant.ts` | INTENT_TYPES 加 qa: '通用问答' |
| 前端 | `frontend/src/types/candidate.ts` | CandidateCard 加 score_detail? |
| 前端 | `frontend/src/views/Workbench.vue` | watch 仅非空更新；切换会话清空；历史恢复卡片 |
| 前端 | `frontend/src/components/chat/ChatPanel.vue` | onDone 透传 title |
| 前端 | `frontend/src/components/candidate/CandidateCard.vue` | 渲染 score_detail 维度 |
| 前端 | `frontend/src/api/sse.ts` | onDone handler 加 title 参数 |
| 前端 | `frontend/src/stores/chat.ts` | 新增 updateSessionTitle 方法 |
| 前端 | `frontend/tests/...` | 7 个新单元测试 |

## 不做的事（YAGNI）

- 不引入 7 类细分意图（方案 B 已否决）
- 不保留黑盒分数仅加理由（方案 C 已否决）
- 不提供会话重命名 API（首条消息自动命名已满足需求）
- 不重构 agent_graph 状态机（当前 service 层内联逻辑工作正常）
- 不改 MessageBubble 的候选人缩略展示（仅 Workbench 右栏卡片需改）
