# RAG 增强设计

> 日期: 2026-06-29
> 状态: 已确认，待实施

## 背景与目标

当前 RAG 流程为：策略改写 → 多路 Dense+Sparse 召回 → chunk 去重 → Reranker 精排 → 简历级去重 → 硬过滤 → LLM 评分 → 分数截断。

**痛点**：
1. 复杂多条件查询（如"3年经验后端工程师会Python和Docker 30K以内"）作为整体查询向量相似度被稀释，召回率低
2. 仅 Dense+Sparse 两路召回，skills 写法差异导致漏召回（如 NLP/BERT 问题）
3. 同一简历多个 chunks 命中后只取最高分 chunk，LLM 评分信息不完整

**目标**：在"召回→精排→压缩"全链路增强，质量优先（允许延迟增加 2-4 秒）。

## 整体架构

```
用户查询
   ↓
[模块1] Query Decomposition（LLM 拆解）
   ↓ 输出: 主查询 + 子查询列表 + 结构化子条件
   ↓
[模块2] Multi-Route Retrieval（多路召回）
   ├─ Route A: 主查询 Dense+Sparse Hybrid（语义召回）
   ├─ Route B: 子查询独立 hybrid_search（子条件召回）
   └─ Route C: MongoDB 结构化精确匹配（硬匹配保底）
   ↓ 合并 chunk_id 去重
   ↓
Reranker 精排（现有）→ 简历级去重（现有）
   ↓
[模块3] Context Compression（LLM 压缩）
   ↓ 同一简历多个 chunks → 合并为单一精炼 context（≤500 字）
   ↓
硬过滤 + LLM 评分（现有）→ 返回
```

**核心思路**：召回阶段"宽进"（多路+子条件），精排后"压缩"（去冗余），让 LLM 评分基于精炼 context，提升质量。

## 模块1：查询分解（Query Decomposition）

### 现状

`strategy_selector` 的 `subquery` 策略已有 LLM 拆解，但只生成多个查询字符串，**没有拆成结构化子条件**，导致"3年经验"这种条件只能靠向量相似度匹配，无法做硬过滤保底。

### 增强

新增 `query_decompose` 节点，LLM 输出结构化 JSON：

```json
{
  "main_query": "后端工程师 会Python和Docker 3年经验 30K以内",
  "sub_queries": [
    "后端工程师 Python Docker",
    "3年经验后端开发",
    "Python Docker 微服务"
  ],
  "structured_filters": {
    "required_skills": ["python", "docker"],
    "work_years_min": 3,
    "salary_max": 30,
    "job_type": "后端"
  }
}
```

### 关键决策

- `sub_queries` 用于多路召回（模块2 Route B），每个子查询独立检索
- `structured_filters` 合并到现有 `filters`，走硬过滤保底
- LLM 失败时回退到现有 `strategy_selector`，保证兜底
- **替代 `filter_extract_node`**：合并为一个节点，避免两次 LLM 调用（模块1 是 `filter_extract_node` 的超集）

### 子查询数量限制

最多 3 个，避免 LLM 拆出 5+ 个导致检索爆炸。

## 模块2：多路召回（Multi-Route Retrieval）

### 现状

`search_service.search()` 只用 `strategy_selector` 改写后的多个查询做 Dense+Sparse hybrid_search，每路相同。多条件查询时，"3年经验 Python Docker"作为一个整体查询，向量相似度会被稀释，召回率低。

### 增强

召回分 3 路，合并去重后送 Reranker。

```
Route A: 主查询 hybrid_search（现有逻辑，语义召回）
         └─ 用 main_query 做 Dense+Sparse 检索，retrieve_per_query 条

Route B: 子查询独立 hybrid_search（新增，子条件召回）
         └─ 对每个 sub_query 独立 hybrid_search，每个 retrieve_per_query/N 条
         └─ 解决多条件被向量稀释问题

Route C: MongoDB 结构化精确匹配保底（新增，硬匹配召回）
         └─ 按 structured_filters 在 MongoDB 直接查 skills/work_years/edu 匹配的简历
         └─ 取前 N 条的 resume_id，从 Milvus 拉这些简历的 chunks
         └─ 解决向量检索漏召回问题（如 skills 写法差异）
```

### 合并策略

- 三路 chunks 按 `chunk_id` 去重合并
- Route C 拉的 chunks 赋 `rerank_score=0` 兜底（让 Reranker 重新打分，避免无分）
- 合并后总数仍受 `retrieve_per_query` 上限控制，避免过多

### 关键决策

1. Route C 需要：前面 NLP/BERT 问题就是向量召回漏了，结构化保底能兜住
2. Route B 子查询数量限制 3 个
3. Route C 的 MongoDB 查询走现有 `resumes_coll`，按 skills 子串 + work_years/edu 范围查

### 与现有的关系

- 替换 `search_service.search()` 中的"多改写检索"循环（第 124-131 行）
- `strategy_selector` 保留（简单查询仍走 direct/hyde/backtracking），模块1 的查询分解是新策略 `decompose`，由 strategy_selector 路由进入

## 模块3：上下文压缩（Context Compression）

### 现状痛点

同一简历多个 chunks 命中后，`_enrich_candidates` 对每个简历只取一个 chunk（按 `rerank_score` 最高），但这个 chunk 可能只是技能列表片段，遗漏了项目经验、工作年限等关键评分依据。LLM 评分时 `parent_content` 单一，信息不完整。

### 增强

Reranker 精排后、硬过滤前，对同一简历的多个 chunks 做合并压缩。

```
精排后 chunks（按 resume_id 分组）
   ↓
对每个 resume_id 的 chunks：
   ├─ 取 rerank_score 最高的 chunk 作为主 context
   ├─ 从其他 chunks 的 parent_content 中提取非重复信息片段
   └─ LLM 压缩为单一精炼 context（≤500 字）
   ↓
输出: 每个 resume_id 一个 compressed_context
```

### 压缩策略

- **LLM 压缩 prompt**：输入多个 chunks 的 parent_content + 原始 query，输出聚焦于 query 相关性的精炼摘要（技能匹配点、经验匹配点、项目匹配点）
- **长度限制**：压缩后 ≤500 字（控制 LLM 评分输入 token）
- **保底**：LLM 压缩失败时回退到"取 rerank_score 最高的 chunk"（现有逻辑）

### 关键决策

1. 只对命中 ≥2 chunks 的简历压缩（单 chunk 不浪费 LLM 调用）
2. 压缩后 `parent_content` 字段替换为 `compressed_context`，传入 `_enrich_candidates` 的 `chunk_map`
3. 压缩是**并发执行**（`asyncio.gather`），多简历并行压缩，总耗时≈单次 LLM 调用

### 与现有的关系

- 替换 `_enrich_candidates` 中 `chunk_map` 的构建逻辑（现在只取最高分 chunk，改为取压缩后的 context）
- 在 `retrieve_rank_node` 或 `search_service.search()` 精排后插入压缩步骤

## 延迟影响

| 模块 | 增量 | 说明 |
|------|------|------|
| 模块1 查询分解 | +1 次 LLM（~2s） | 替代 filter_extract_node，不额外增加 |
| 模块2 多路召回 | +0s | Route B/C 与 Route A 并发 |
| 模块3 上下文压缩 | +1 次 LLM（~2s，并发） | 多简历并行压缩 |
| **总计** | **+4s** | 符合质量优先预期 |

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `app/agent/prompts.py` | 修改 | 新增 QUERY_DECOMPOSE_PROMPT、CONTEXT_COMPRESS_PROMPT |
| `app/agent/nodes.py` | 修改 | 新增 query_decompose_node、context_compress_node；filter_extract_node 合并进 query_decompose_node |
| `app/agent/graph.py` | 修改 | 新增 decompose 策略路由、context_compress 节点 |
| `app/core/strategy_selector.py` | 修改 | 新增 decompose 策略 |
| `app/services/search_service.py` | 修改 | 多路召回逻辑、压缩 context 传入 |
| `app/services/jd_match_service.py` | 可选修改 | JD 匹配复用多路召回 |
| `tests/agent/test_nodes.py` | 新增 | 查询分解、上下文压缩单测 |
| `tests/services/test_search_service.py` | 新增 | 多路召回、压缩集成测试 |

## 兜底机制

- 模块1 LLM 失败 → 回退 `strategy_selector` 现有策略
- 模块2 Route C MongoDB 查询失败 → 跳过，不影响 Route A/B
- 模块3 LLM 压缩失败 → 回退取最高分 chunk（现有逻辑）
- 所有 LLM 调用有 try/except + 日志，不阻断主流程

## 测试要点

- 查询分解：复杂多条件查询能正确拆出 sub_queries + structured_filters
- 多路召回：三路结果合并去重正确，Route C 兜底有效
- 上下文压缩：多 chunk 简历压缩为单一 context，单 chunk 不压缩
- 兜底：各模块 LLM 失败时回退正确
- 延迟：总增量 ≤4s
