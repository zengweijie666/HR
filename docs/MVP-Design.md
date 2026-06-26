# TalentSense HR 简历推荐系统 - v2.5 弱化增强版方案

**版本**：v2.5（基于v3.0技术栈 + EduRAG实战验证技术，弱化复杂功能 + 体验增强）
**日期**：2026-06-26
**定位**：在v2.0(HRCopilot)已跑通的基础上重构，复用EduRAG验证过的RAG技术，砍掉v3.0最难落地的功能，补上实用新功能

---

## 〇、项目参考与技术复用

### 参考项目1：EduRAG (Itcast_qa_system) — 已验证的RAG技术
| 技术 | EduRAG实现 | 复用到HR项目 |
|-----|-----------|------------|
| Query改写（策略选择） | `strategy_selector.py` — LLM选4种策略 | ✅ 保留，复用策略选择逻辑 |
| HyDE假设文档检索 | `new_rag_system.py` — `_retrieve_with_hyde` | ✅ 保留 |
| 子查询分解检索 | `new_rag_system.py` — `_retrieve_with_subqueries` | ✅ 保留 |
| 回溯问题检索 | `new_rag_system.py` — `_retrieve_with_backtracking` | ✅ 保留 |
| BGE-M3混合检索 | `vector_store.py` — Dense+Sparse, WeightedRanker(1.0,0.7) | ✅ 保留 |
| BGE-Reranker精排 | `vector_store.py` — CrossEncoder.predict | ✅ 保留 |
| 父子块分层切分 | `document_processor.py` — 子块300入库,还原父块1200 | ✅ 保留（简历也适用） |
| BERT查询分类 | `query_classifier.py` — 通用/专业二分类 | ✅ 简化为LLM意图识别（不训练BERT） |
| RapidOCR | `edu_ocr.py` — paddle/onnxruntime双引擎 | ✅ 保留单引擎（PDF/DOCX为主） |
| DashScope流式 | `new_main.py` — OpenAI兼容,stream=True | ✅ 保留 |
| 延迟加载 | `@property`首次查询初始化模型 | ✅ 保留（节省启动内存） |
| Redis缓存 | BM25分词缓存+QA缓存 | ✅ 保留查询缓存 |
| 多轮对话历史 | MySQL conversations表,最近5轮 | ✅ 改为MongoDB存储 |

### 参考项目2：HRCopilot (v2.0) — 已有基础设施
| 已有能力 | 实现位置 | 复用方式 |
|---------|---------|---------|
| Docker全栈9服务 | `docker-compose.yml` | ✅ 直接复用（Milvus/MongoDB/Redis/MinIO/Nginx） |
| FastAPI后端 | `backend/app/main.py` | ✅ 复用框架，重构业务层 |
| Vue3+Element Plus前端 | `frontend/src/` | ✅ 复用框架，重构页面 |
| LangGraph状态机 | `domains/agent/graph.py` | ✅ 保留，简化为5节点 |
| SSE流式传输 | `api/chat.py` + `stores/chat.ts` | ✅ 直接复用 |
| 简历解析+bbox | `domains/resume/parser/` | ✅ 保留解析，简化bbox（不做高亮遮罩） |
| PII脱敏 | `domains/resume/quality/pii.py` | ✅ 简化为脱敏展示 |
| 去重 | `domains/resume/quality/dedup.py` | ✅ 保留自动去重 |
| JWT认证 | `api/auth.py` + `api/deps.py` | ✅ 保留简单认证 |
| PDF.js预览 | `components/resume/ResumePreview.vue` | ✅ 保留预览，砍掉bbox高亮 |

---

## 一、核心策略：弱化什么、保留什么、新增什么

### 1.1 弱化清单（只砍真正复杂且收益低的）

| v3.0复杂功能 | 难度 | v2.5处理方式 | 理由 |
|-------------|------|-------------|------|
| bbox高亮遮罩（PDF.js Canvas绘制） | 极高 | **砍掉**，保留PDF预览但不做高亮 | bbox高亮前端Canvas绘制2周，收益有限；保留预览即可 |
| LayoutLMv3 版面预处理 | 高 | **砍掉** | 版面分析模型部署复杂，LLM结构化提取已够用 |
| Guardrails溯源校验 + 公平性检查 | 高 | **砍掉** | 溯源校验依赖chunk_id绑定，公平性检查非核心 |
| HITL 60秒超时降级机制 | 中高 | **砍掉**，直接追问 | 超时降级链+MongoCheckpointer中断恢复太复杂 |
| OpenTelemetry全链路Tracing | 中高 | **砍掉**，用loguru | OTel部署+采样+存储重，logging够用 |
| Prometheus + Grafana监控 | 中 | **砍掉** | 非核心，后续需要再加 |
| MongoCheckpointer会话持久化 | 中 | **简化**为MongoDB直接存对话历史 | Checkpointer版本兼容问题，直接存更简单 |
| LLM主备降级链（Qwen→DeepSeek→规则） | 中 | **简化**为单LLM + tenacity重试 | 主备降级需配置多API，单LLM+重试够用 |
| 时效衰减freshness_score预计算 | 低 | **砍掉** | 非核心，后续需要再加 |
| 去重审核队列（人工确认） | 低 | **砍掉**，自动去重即可 | 审核队列需额外UI，自动合并够用 |
| PII AES-256加密 | 中 | **简化**为字符串脱敏展示 | 加密需密钥管理，脱敏展示（138****1234）够用 |
| 领域分层5个域 | 中 | **简化**为3层（api/services/core） | 5域过度设计，3层足够清晰 |
| LangGraph 8节点 | 中 | **简化为5节点** | 砍掉feedback/guardrail/finalize独立节点 |
| 8个独立Prompt文件 | 低 | **集中为1文件** | 集中管理更简单，改Prompt不用跳文件 |
| 双OCR模型投票（Paddle+Easy） | 中 | **简化为RapidOCR单引擎** | EduRAG已验证RapidOCR够用 |
| 三级解析降级链 | 低 | **简化为两级**（PyMuPDF/docx → OCR） | Unstructured依赖重，两级够用 |
| LangSmith Tracing | 低 | **砍掉** | 非核心，loguru够用 |
| 三层数据备份（Milvus+Mongo+Redis） | 中 | **砍掉**，保留MongoDB mongodump | 备份脚本复杂，单库备份够用 |

### 1.2 保留清单（EduRAG已验证 + v2.0已有的核心技术）

| 保留功能 | 技术实现 | 来源 | 说明 |
|---------|---------|------|------|
| ✅ BGE-M3混合检索 | Dense(1024)+Sparse, WeightedRanker | EduRAG `vector_store.py` | 两个项目都验证过 |
| ✅ BGE-Reranker精排 | CrossEncoder `predict` | EduRAG `vector_store.py` | 已验证有效 |
| ✅ Query改写（HyDE/子查询/回溯） | LLM选策略→改写→检索 | EduRAG `strategy_selector.py` | **核心差异化能力，必须保留** |
| ✅ 父子块分层切分 | 子块入库,检索还原父块 | EduRAG `document_processor.py` | 提升检索质量 |
| ✅ LangGraph状态机 | 5节点简化版 | HRCopilot `graph.py` | 保留状态机架构，简化节点 |
| ✅ SSE流式输出 | StreamingResponse+AsyncOpenAI | HRCopilot `chat.py` | v2.0已验证 |
| ✅ LLM可解释评分 | LLM生成评分+自然语言理由 | 新实现 | 不绑定chunk_id，但给理由 |
| ✅ 简历去重 | phone_hash + email_hash | HRCopilot `dedup.py` | 保留自动去重 |
| ✅ PII脱敏展示 | 手机号/邮箱星号替换 | HRCopilot `pii.py` | 不加密，但展示脱敏 |
| ✅ Vue3+Element Plus | Composition API | HRCopilot `frontend/` | 保留前后端分离 |
| ✅ JWT认证 | 简单用户登录 | HRCopilot `auth.py` | 保留基础认证 |
| ✅ Redis缓存 | 查询缓存+增删改清缓存 | HRCopilot `cache.py` | 保留缓存层 |
| ✅ MongoDB | 简历元数据+对话历史 | HRCopilot | 保留文档数据库 |
| ✅ MinIO | 原始简历文件存储 | HRCopilot | 保留对象存储 |
| ✅ PDF.js简历预览 | 前端渲染PDF（不做高亮） | HRCopilot `ResumePreview.vue` | 保留预览，砍bbox高亮 |
| ✅ RapidOCR | paddle/onnxruntime | EduRAG `edu_ocr.py` | 图片简历OCR |
| ✅ 延迟加载 | @property首次查询初始化模型 | EduRAG `new_rag_system.py` | 节省启动内存 |
| ✅ Docker全栈 | 9服务编排 | HRCopilot `docker-compose.yml` | 直接复用 |

### 1.3 新增清单（体验增强，开发快、价值高）

| 新增功能 | 难度 | 开发时间 | 业务价值 | 实现方式 |
|---------|------|---------|---------|---------|
| 📧 **自动发邮件** | ⭐⭐ | 1天 | ⭐⭐⭐⭐⭐ | FastAPI后端用`aiosmtplib`异步发邮件，LLM生成HTML推荐报告+Excel附件 |
| 📊 **Excel导出** | ⭐ | 半天 | ⭐⭐⭐⭐⭐ | `openpyxl`生成候选人列表Excel，前端一键下载 |
| 🏷️ **标签收藏系统** | ⭐ | 1天 | ⭐⭐⭐⭐ | MongoDB存标签，前端候选人卡片支持打标签/收藏/按标签筛选 |
| 📋 **JD岗位匹配** | ⭐⭐ | 1天 | ⭐⭐⭐⭐⭐ | 粘贴JD文本→LLM提取要求→向量检索匹配，复用现有检索+改写能力 |
| 💬 **面试问题生成** | ⭐⭐ | 半天 | ⭐⭐⭐⭐ | 基于候选人简历，LLM生成针对性面试问题（按技能/项目分类） |
| 📈 **数据看板** | ⭐ | 半天 | ⭐⭐⭐⭐ | 前端ECharts展示：简历总数、技能分布、年限分布、学历分布 |
| 🔍 **相似候选人推荐** | ⭐⭐ | 半天 | ⭐⭐⭐ | 查看候选人详情时，用其简历向量检索相似背景的人 |
| 📝 **面试评价记录** | ⭐ | 半天 | ⭐⭐⭐ | HR在候选人卡片写评价，存MongoDB，详情页展示 |

---

## 二、技术栈（保留v3.0 + EduRAG验证技术，Docker已就绪）

| 组件 | 选型 | 状态 | 说明 |
|-----|------|------|------|
| Web框架 | FastAPI 0.115+ | ✅ 已部署 | 异步支持SSE |
| 向量数据库 | Milvus 2.4+ | ✅ Docker已部署 | Dense+Sparse混合索引 |
| 业务数据库 | MongoDB 7.0 | ✅ Docker已部署 | 简历元数据、对话历史 |
| 缓存 | Redis 7.0+ | ✅ Docker已部署 | 查询缓存、Session |
| 对象存储 | MinIO | ✅ Docker已部署 | 简历文件存储 |
| 嵌入模型 | BGE-M3 | ✅ 模型已下载 | Dense(1024)+Sparse, EduRAG已验证 |
| 重排序模型 | BGE-Reranker-v2-m3 | ✅ 模型已下载 | CrossEncoder, EduRAG已验证 |
| RAG框架 | LangChain 0.3+ | ✅ 可复用 | 异步RAG链 |
| Agent框架 | LangGraph 0.2+ | ✅ 简化使用 | 5节点状态机（非8节点） |
| LLM客户端 | AsyncOpenAI | ✅ 可复用 | DashScope兼容,异步非阻塞 |
| 前端框架 | Vue3 + TS | ✅ 可复用 | Composition API |
| UI组件库 | Element Plus | ✅ 可复用 | 企业级组件 |
| PDF预览 | PDF.js | ✅ 可复用 | 简历预览（不做bbox高亮） |
| OCR | RapidOCR | ✅ EduRAG已验证 | onnxruntime引擎 |
| 图表库 | ECharts | 🆕 新增 | 数据看板可视化 |
| 邮件库 | aiosmtplib | 🆕 新增 | 异步发邮件 |
| Excel库 | openpyxl | ✅ 已有 | Excel导出 |

---

## 三、架构设计（简化3层，非5域）

### 3.1 简化分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端交互层 (Vue3 + Element Plus)              │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│   │ 对话面板  │ │候选人卡片 │ │简历管理   │ │ 数据看板/标签/JD │ │
│   │ (SSE流式)│←→│(动态联动) │ │(上传/预览)│ │ (新增功能页)     │ │
│   └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SSE / HTTP
┌──────────────────────────▼──────────────────────────────────────┐
│                  API 层 (FastAPI 薄路由)                         │
│   参数校验 + 调用 service + 统一异常处理 + SSE流式编排           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                  Service 层 (业务逻辑)                           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐  │
│  │resume_svc  │ │search_svc │ │ agent_svc  │ │ enhance_svc   │  │
│  │解析/去重/  │ │混合检索/  │ │LangGraph   │ │邮件/导出/标签/│  │
│  │脱敏/CRUD   │ │改写/Rerank│ │5节点状态机 │ │JD匹配/面试题  │  │
│  │            │ │/缓存      │ │            │ │               │  │
│  └───────────┘ └───────────┘ └───────────┘ └───────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                  Core 层 (基础设施)                              │
│  database(Milvus/Mongo/Redis/MinIO) / config / llm_client /    │
│  embedding(BGE-M3+Reranker) / logger / exceptions / prompts    │
└─────────────────────────────────────────────────────────────────┘
```

**与v3.0的区别**：
- v3.0：5个领域（resume/search/agent/observability/shared），领域间禁止横向依赖
- v2.5：3层（api/services/core），简单直接，service之间可以互相调用
- 砍掉 observability 域（Tracing/降级/监控），用 loguru 替代
- 把新增的增强功能集中到 enhance_svc，不散落各处

### 3.2 目录结构

```
backend/app/
├── api/                          # API路由层
│   ├── auth.py                   # JWT认证
│   ├── resumes.py                # 简历上传/列表/详情/删除
│   ├── chat.py                   # 对话推荐(SSE) + 会话管理
│   ├── search.py                 # 直接检索接口
│   ├── candidates.py             # 候选人对比/导出/标签
│   ├── email.py                  # 🆕 邮件发送接口
│   ├── jd_match.py                # 🆕 JD匹配接口
│   ├── dashboard.py              # 🆕 数据看板接口
│   └── deps.py                   # 依赖注入
│
├── services/                     # 业务逻辑层
│   ├── resume_service.py         # 简历解析/去重/脱敏/CRUD
│   ├── search_service.py         # 混合检索/Query改写/Reranker/缓存
│   ├── agent_service.py          # LangGraph对话(5节点)
│   ├── email_service.py          # 🆕 邮件发送+报告生成
│   ├── export_service.py         # 🆕 Excel导出
│   ├── tag_service.py            # 🆕 标签/收藏管理
│   ├── jd_match_service.py       # 🆕 JD解析+匹配(复用search)
│   ├── interview_service.py      # 🆕 面试问题生成+评价记录
│   └── dashboard_service.py      # 🆕 统计聚合
│
├── agent/                        # Agent核心(简化版LangGraph)
│   ├── graph.py                  # LangGraph图定义(5节点)
│   ├── state.py                  # AgentState
│   ├── nodes.py                  # 5个节点(合一文件<300行)
│   └── prompts.py                # Prompt集中管理(1文件)
│
├── core/                         # 基础设施
│   ├── database.py               # Milvus/MongoDB/Redis连接
│   ├── minio_client.py           # MinIO文件操作
│   ├── llm_client.py             # AsyncOpenAI + tenacity重试
│   ├── embedding.py              # BGE-M3嵌入(延迟加载)
│   ├── reranker.py               # BGE-Reranker(延迟加载)
│   ├── vector_store.py           # Milvus混合检索(复用EduRAG)
│   ├── strategy_selector.py      # Query改写策略选择(复用EduRAG)
│   ├── config.py                 # 配置管理
│   ├── logger.py                 # loguru日志(替代OpenTelemetry)
│   └── exceptions.py             # 统一异常
│
├── models/                       # Pydantic数据模型
│   ├── resume.py
│   ├── chat.py
│   └── candidate.py
│
└── main.py                       # FastAPI入口

frontend/src/
├── views/
│   ├── Workbench.vue             # 工作台(对话+候选人)
│   ├── ResumeList.vue            # 简历列表管理
│   ├── ResumeDetail.vue          # 简历详情+预览+相似推荐
│   ├── Dashboard.vue             # 🆕 数据看板
│   └── Settings.vue              # 🆕 邮件配置/系统设置
├── components/
│   ├── chat/                     # 对话组件
│   ├── resume/                   # 简历卡片/预览
│   ├── candidate/                # 候选人卡片/对比
│   └── common/                   # 通用组件
└── ...
```

---

## 四、Agent简化设计（5节点状态机 vs v3.0的8节点）

### v3.0 的8节点（太复杂）
```
intent → {chitchat | retrieve | deep_query}
retrieve → rerank → feedback → {guardrail | finalize}
deep_query → {finalize | retrieve}
```

### v2.5 的5节点（够用）
```
intent → {chitchat | retrieve_rank | detail}
retrieve_rank → clarify → respond
```

| 节点 | 职责 | 实现要点 |
|------|------|---------|
| **intent** | 识别意图：闲聊/搜索/详情/对比 | LLM一次调用返回意图类型（复用EduRAG策略选择思路） |
| **retrieve_rank** | Query改写→混合检索→Reranker→LLM评分 | 复用EduRAG的strategy_selector + vector_store + reranker |
| **clarify** | 召回不足时生成追问问题 | 简单追问，不做HITL超时降级 |
| **detail** | 基于last_candidates回答详情/对比 | LLM针对性回答 |
| **respond** | 生成最终响应 | 闲聊直接回复；推荐输出候选人+理由 |

**砍掉的节点**：
- ❌ feedback（HITL超时降级）→ 简化为clarify节点直接追问
- ❌ guardrail（溯源校验+公平性检查）→ 砍掉
- ❌ finalize（单独的输出节点）→ 合并到respond
- ❌ deep_query独立节点 → 合并到detail

```python
# v2.5 AgentState（简化版）
class AgentState(TypedDict):
    messages: list[dict]           # 对话历史
    user_query: str                # 当前输入
    session_id: str
    intent: str                    # chitchat/search/detail/compare
    strategy: str                  # Query改写策略(直接/HyDE/子查询/回溯)
    filters: dict                  # 提取的筛选条件
    query_rewrites: list[str]      # 改写后的query
    candidates: list[dict]         # 检索到的候选人
    ranked: list[dict]             # Reranker+LLM评分排序后
    last_candidates: list[dict]    # 上轮推荐(支持"第一个候选人")
    clarification: str             # 追问问题
    response: dict                 # 最终响应
    trace_id: str
```

---

## 五、检索链路设计（复用EduRAG核心技术）

### 5.1 检索流程（核心差异化能力）

```
用户Query
    │
    ▼
┌─────────────────────┐
│ 策略选择(LLM)        │  复用EduRAG strategy_selector.py
│ 直接/HyDE/子查询/回溯 │
└──────────┬──────────┘
           │
    ┌──────┼──────┬──────┐
    │      │      │      │
  直接   HyDE  子查询  回溯
    │      │      │      │
    │   LLM生成   LLM拆解 LLM简化
    │   假设答案   子查询   问题
    │      │      │      │
    └──────┴──────┴──────┘
           │
           ▼
┌─────────────────────┐
│ BGE-M3编码           │  Dense(1024)+Sparse
│ (延迟加载)           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Milvus混合检索       │  WeightedRanker(1.0, 0.7)
│ Top-20子块           │  复用EduRAG vector_store.py
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 还原父文档           │  Small-to-Big (子块300→父块1200)
│ 去重                 │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ BGE-Reranker精排     │  CrossEncoder.predict
│ Top-10              │  复用EduRAG vector_store.py
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Python标量过滤        │  薪资/学历/年限硬条件
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ LLM评分+推荐理由     │  0-100分 + 自然语言理由
│ Top-K输出            │
└─────────────────────┘
```

### 5.2 从EduRAG复用的核心代码

| EduRAG文件 | 复用内容 | HR项目位置 |
|-----------|---------|-----------|
| `rag_qa/core/strategy_selector.py` | Query改写策略选择逻辑 | `core/strategy_selector.py` |
| `rag_qa/core/vector_store.py` | Milvus混合检索+BGE-Reranker | `core/vector_store.py` |
| `rag_qa/core/document_processor.py` | 父子块分层切分 | `services/resume_service.py`内 |
| `rag_qa/core/prompts.py` | HyDE/子查询/回溯Prompt模板 | `agent/prompts.py`内 |
| `rag_qa/edu_document_loaders/edu_ocr.py` | RapidOCR封装 | `core/ocr.py` |
| `rag_qa/core/new_rag_system.py` | 延迟加载+流式生成模式 | `services/agent_service.py`参考 |

**关键适配点**：
- EduRAG是教育问答（文档→知识库），HR是简历推荐（简历→候选人库）
- 父子块切分用于简历：子块=工作经历/项目/技能等片段，父块=完整简历段落
- Query改写用于HR场景：如"找个Java大佬" → HyDE生成"5年Java后端开发经验，熟悉Spring生态" → 检索

---

## 六、新增功能详细设计

### 6.1 📧 自动发邮件

**后端接口**：
```
POST /api/v1/email/send-recommendation
Body: {
    "to_email": "HR@company.com",
    "candidates": [...],
    "query": "5年Java开发",
    "include_excel": true
}
```

**实现流程**：
1. LLM生成HTML邮件正文（候选人卡片式排版）
2. `openpyxl`生成Excel附件
3. `aiosmtplib`异步发送邮件
4. SMTP配置存MongoDB（settings集合），前端Settings页可配置

### 6.2 📊 Excel导出

```
POST /api/v1/candidates/export
Body: { "candidates": [...], "format": "excel" }
Response: 文件流下载
```

### 6.3 🏷️ 标签收藏系统

**MongoDB resumes集合新增字段**：
```javascript
{
    "tags": ["已面试", "重点关注"],
    "is_favorite": true,
    "notes": "面试表现良好，技术扎实"
}
```

**接口**：
- `PUT /api/v1/resumes/{id}/tags` - 更新标签
- `PUT /api/v1/resumes/{id}/favorite` - 收藏/取消收藏
- `PUT /api/v1/resumes/{id}/notes` - 更新评价
- `GET /api/v1/resumes?tag=已面试` - 按标签筛选

### 6.4 📋 JD岗位匹配

```
POST /api/v1/jd/match
Body: { "jd_text": "岗位描述文本...", "top_k": 10 }
```

**流程**：
1. LLM从JD文本提取结构化要求（技能/年限/学历/职责）
2. 用JD文本做Query改写（复用strategy_selector）+ 向量检索
3. Python过滤（年限/学历硬条件）
4. BGE-Reranker精排 + LLM评分排序
5. 返回匹配候选人+匹配分析

**核心优势**：JD匹配本质就是"把JD当query"的检索+改写+精排，完全复用现有search能力。

### 6.5 💬 面试问题生成

```
POST /api/v1/candidates/{id}/interview-questions
```

LLM基于候选人简历，按维度生成面试问题：
- 技术深度：针对技能栈出题
- 项目经验：针对项目经历追问
- 系统设计：基于级别出设计题
- 行为面试：STAR方法

### 6.6 📈 数据看板

```
GET /api/v1/dashboard/stats
```

返回聚合数据，前端ECharts渲染：
- 简历总数、本周新增
- 技能Top-20分布（柱状图）
- 工作年限分布（饼图）
- 学历分布（饼图）
- 薪资范围分布（柱状图）
- 标签分布（已面试/待定/淘汰占比）

### 6.7 🔍 相似候选人推荐

```
GET /api/v1/candidates/{id}/similar?top_k=5
```

用该候选人简历的向量，在Milvus里检索最相似的Top-5（排除自己）。

---

## 七、数据模型（简化版）

### MongoDB resumes集合

```javascript
{
    "_id": ObjectId,
    "resume_id": "res_xxx",
    "candidate_id": "cand_xxx",
    "basic_info": {
        "name": "张三",
        "phone_masked": "138****1234",
        "phone_hash": "sha256...",
        "email_masked": "zhang***@xx.com",
        "email_hash": "sha256...",
        "gender": "男",
        "age": 30,
        "location": "北京"
    },
    "education": "本科",
    "education_level": 1,               // 0专科 1本科 2硕士 3博士
    "work_years": 5,
    "skills": ["Java", "Spring Boot", "MySQL"],
    "work_experience": [...],
    "education_detail": [...],
    "summary": "5年Java后端开发经验...",
    "expected_salary": { "min": 20, "max": 30 },
    "file_info": {
        "file_id": "minio_id",
        "file_name": "张三_简历.pdf",
        "file_type": "pdf"
    },
    "parse_info": {
        "parse_status": "completed",
        "parse_time": "2026-06-26T10:00:00Z"
    },
    // 🆕 v2.5新增字段
    "tags": [],
    "is_favorite": false,
    "notes": "",
    // 砍掉的v3.0字段
    // "source_chunks": [...]    // 不保留bbox坐标
    // "freshness": {...}         // 不做时效衰减
    "created_at": "2026-06-26T10:00:00Z",
    "updated_at": "2026-06-26T10:00:00Z"
}
```

### Milvus Collection（保留混合索引）

```python
fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
    FieldSchema(name="candidate_id", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=1024),
    FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
    FieldSchema(name="salary_min", dtype=DataType.INT64),
    FieldSchema(name="salary_max", dtype=DataType.INT64),
    FieldSchema(name="education_level", dtype=DataType.INT8),
    FieldSchema(name="work_years", dtype=DataType.INT64),
    FieldSchema(name="skills_text", dtype=DataType.VARCHAR, max_length=2000),
    FieldSchema(name="parent_id", dtype=DataType.VARCHAR, max_length=64),     # 父子块关联
    FieldSchema(name="parent_content", dtype=DataType.VARCHAR, max_length=4000), # 父块内容
]
# 索引: dense=IVF_FLAT/IP, sparse=SPARSE_INVERTED_INDEX/IP
# 检索: WeightedRanker(1.0, 0.7) 复用EduRAG配置
```

---

## 八、开发排期（2-3周）

| 阶段 | 天数 | 任务 | 交付物 |
|-----|------|------|-------|
| **Phase 1: 基础重构** | Day 1-2 | 搭建3层架构骨架 + core基础设施 + 从EduRAG迁移vector_store/strategy_selector + Docker对接 | 项目骨架跑通，Milvus/MongoDB/Redis/MinIO连接正常 |
| **Phase 2: 简历解析** | Day 3-4 | PDF/DOCX解析(PyMuPDF+python-docx) + RapidOCR + LLM结构化提取 + 父子块切分 + 去重 + 脱敏 + Milvus索引 + MinIO存储 | 简历上传全链路跑通 |
| **Phase 3: 检索+Agent** | Day 5-7 | BGE-M3混合检索 + Query改写(策略选择) + BGE-Reranker精排 + LangGraph 5节点状态机 + SSE流式 | 对话推荐核心跑通 |
| **Phase 4: 前端核心** | Day 8-10 | Vue3工作台(对话+候选人卡片) + 简历列表 + 简历上传 + PDF预览(不做高亮) | 前端核心页面可用 |
| **Phase 5: 新增功能** | Day 11-14 | 📧邮件 + 📊Excel + 🏷️标签 + 📋JD匹配 + 💬面试题 + 📈看板 + 🔍相似推荐 | 全部新增功能上线 |
| **Phase 6: 联调优化** | Day 15 | 端到端测试 + Prompt优化 + 错误处理 + 部署 | 可演示的完整系统 |

---

## 九、与v3.0的功能对比

| 功能模块 | v3.0 | v2.5 | 差异说明 |
|---------|------|------|---------|
| 简历解析 | 三级降级链+双OCR+bbox | PyMuPDF+python-docx+RapidOCR(单引擎) | 砍掉双OCR投票和bbox高亮 |
| 向量检索 | 混合索引+HyDE+Query改写+多路召回 | **混合索引+Query改写(HyDE/子查询/回溯)** | ✅ 保留EduRAG验证的Query改写 |
| 精排 | BGE-Reranker+LLM多维评分 | **BGE-Reranker+LLM评分** | ✅ 保留Reranker |
| 父子块 | 无 | **子块入库+父块还原** | ✅ 从EduRAG复用 |
| Agent | LangGraph 8节点+HITL+Guardrails | LangGraph 5节点 | 砍掉HITL/Guardrails/反馈重排 |
| 可解释性 | match_claims绑定chunk_id+bbox高亮 | LLM自然语言理由 | 砍掉溯源高亮，保留理由 |
| 可观测性 | OpenTelemetry+Prometheus+降级链 | loguru日志 | 砍掉Tracing/监控/降级链 |
| 会话持久化 | MongoCheckpointer | MongoDB直接存 | 简化Checkpointer |
| 权限 | RBAC三层 | JWT简单认证 | 砍掉RBAC |
| PII | AES-256加密 | 字符串脱敏 | 简化加密 |
| 📧发邮件 | ❌ | ✅ | **新增** |
| 📊Excel导出 | P2优先级 | ✅ 核心 | **提升优先级** |
| 🏷️标签收藏 | ❌ | ✅ | **新增** |
| 📋JD匹配 | ❌ | ✅ | **新增** |
| 💬面试题 | ❌ | ✅ | **新增** |
| 📈数据看板 | ❌ | ✅ | **新增** |
| 🔍相似推荐 | ❌ | ✅ | **新增** |

---

## 十、快速启动

```bash
# Docker环境已就绪（复用HRCopilot的docker-compose.yml）
# 1. 启动基础设施
docker-compose up -d  # Milvus/MongoDB/Redis/MinIO

# 2. 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. 前端
cd frontend
npm install
npm run dev
```

---

**总结**：v2.5保留v3.0技术栈和Docker环境，**复用EduRAG验证过的Query改写+BGE-Reranker+混合检索核心技术**，砍掉bbox高亮、HITL降级、Guardrails、OpenTelemetry等最复杂功能，新增自动发邮件、Excel导出、标签收藏、JD匹配、面试题生成、数据看板等实用增强功能。2-3周可交付。
