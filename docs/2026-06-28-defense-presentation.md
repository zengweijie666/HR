# TalentSense HR 答辩文档

> 课程项目答辩 · 演讲稿 + PPT 大纲 · 时长 15-20 分钟

---

## 答辩信息

| 项目 | 内容 |
|------|------|
| 项目名称 | TalentSense HR — 基于 AI 的智能简历推荐与招聘辅助全栈系统 |
| 项目类型 | 课程项目（全栈开发 + AI 应用） |
| 技术栈 | FastAPI + Vue3 + MongoDB + Milvus + Redis + MinIO + BGE-M3 + LangGraph + Docker |
| 代码规模 | 后端 ~11000 行 Python / 前端 ~8500 行 TypeScript |
| 测试规模 | 405 个测试（后端 272 + 前端 133）全部通过 |
| 版本 | v3.0.0 |
| 答辩时长 | 15-20 分钟 |

---

## PPT 大纲（共 19 页）

| 页码 | 标题 | 时长 |
|------|------|------|
| P1 | 封面 | 30s |
| P2 | 目录 | 20s |
| P3 | 项目背景与目标 | 1.5min |
| P4 | 项目概览（功能矩阵） | 1min |
| P5 | 全栈技术架构 | 1.5min |
| P5.5 | 核心数据流全景图 | 1min |
| P6 | 后端三层架构 | 1min |
| P7 | 前端架构与设计系统 | 1min |
| P8 | **核心技术1：AI 检索流水线** | 2min |
| P9 | **核心技术1：4 维度透明评分** | 1.5min |
| P10 | **核心技术2：Agent 工作流** | 2min |
| P11 | **核心技术2：5 类意图识别** | 1min |
| P12 | **核心技术2：SSE 流式响应** | 1min |
| P13 | **核心技术3：RBAC 权限体系** | 1min |
| P14 | **核心技术3：邮件模板系统** | 1min |
| P15 | 工程质量保障（测试体系） | 1.5min |
| P16 | **生产级运维：Docker 部署 + 可观测性** | 1.5min |
| P17 | 项目亮点与创新点 | 1min |
| P18 | 难点与解决方案 | 1min |
| P19 | 总结与展望 / Q&A | 1min |

---

## 演讲稿

### P1 · 封面（30s）

> 各位老师、同学好。我今天答辩的项目是 **TalentSense HR —— 基于 AI 的智能简历推荐与招聘辅助全栈系统**。
>
> 这个项目解决的核心问题是：HR 面对海量简历时，传统关键词检索无法理解自然语言需求，也无法跨字段语义匹配。我尝试用大语言模型 + 向量检索 + Agent 工作流，构建一套对话式智能招聘系统。
>
> 接下来用大约 18 分钟，从项目背景、架构设计、三大核心技术、工程质量与运维四个维度展开介绍。

---

### P2 · 目录（20s）

> 答辩分为五个部分：项目背景与目标、系统架构、三大核心技术、工程质量与生产级运维、总结与展望。
>
> 其中核心技术部分将重点介绍 AI 检索流水线、Agent 工作流、全栈工程能力这三个方向，最后还会介绍项目的 Docker 化部署与可观测性体系。

---

### P3 · 项目背景与目标（1.5min）

> **传统招聘系统的三个痛点：**
>
> 第一，**关键词检索死板**。HR 输入"5 年经验的前端工程师"，传统系统只能按字段精确匹配，无法理解"前端"包含 Vue/React/JavaScript 等语义关联。
>
> 第二，**简历处理效率低**。DOCX/PDF 简历格式混乱、表格嵌套、扫描版图片，人工录入平均每份 5-10 分钟。
>
> 第三，**评分标准黑箱**。系统给出的匹配度分数没有解释，HR 无法判断为什么这个候选人 85 分，那个 60 分。
>
> **TalentSense HR 的三个目标：**
>
> 1. 用 BGE-M3 向量化简历，支持自然语言语义检索
> 2. 用 LLM 自动解析简历结构化字段，从 DOCX/PDF 到 MongoDB 落库全流程自动化
> 3. 用 4 维度透明评分（技能/经验/学历/薪资）+ 推荐理由，让 HR 看懂每个分数
>
> 整个系统覆盖了从简历上传、智能解析、语义检索、对话推荐、JD 匹配、面试辅助、邮件通知到数据看板的招聘全链路。

---

### P4 · 项目概览（1min）

> 项目实现了 **22 个功能验收点（F01-F22）**，覆盖 10 大业务模块。
>
> | 模块 | 核心功能 |
> |------|---------|
> | 认证管理 | 邮箱+密码登录、RBAC 双角色、注册审批 |
> | 简历管理 | 上传解析、标签/收藏/备注、批量上传、覆盖更新 |
> | 候选人检索 | 自然语言语义检索、Hybrid + Reranker |
> | 智能对话 | 5 类意图识别、SSE 流式、多轮会话 |
> | JD 匹配 | LLM 解析 JD + 检索精排 + 匹配理由 |
> | 面试辅助 | AI 生成面试题、保存评价 |
> | 候选人对比 | 横向对比、相似推荐 |
> | 邮件通知 | 4 个预置模板 + 自定义 + SMTP 配置 |
> | 数据看板 | 7 维度可视化：招聘漏斗/入库趋势/技能/学历/薪资/经验/面试结果 |
> | 用户管理 | admin 后台管理用户、审批、启禁用 |
>
> 此外还实现了 **404 统一处理** 与 **Excel 导出**。

---

### P5 · 全栈技术架构（1.5min）

> 这是整个系统的全栈架构图。
>
> ```
> ┌────────────────────────────────────────────────────────┐
> │              前端 (frontend/) Vue3 + TS                │
> │   Element Plus · Pinia · Vue Router · ECharts · SSE    │
> ├────────────────────────────────────────────────────────┤
> │              HTTP / SSE 通信层                          │
> ├────────────────────────────────────────────────────────┤
> │              后端 (backend/) FastAPI                   │
> │   三层架构 api → services → core                       │
> │   LangGraph Agent · 统一响应 {code,message,data}       │
> │   Prometheus 指标 · 结构化日志 · Sentry 错误追踪       │
> ├────────────────────────────────────────────────────────┤
> │  MongoDB  │  Redis  │  Milvus  │  MinIO  │  LLM(通义)  │
> ├────────────────────────────────────────────────────────┤
> │              Docker Compose 一键部署                   │
> │   7 个容器编排 · 健康检查 · 数据持久化 · MinIO自初始化  │
> └────────────────────────────────────────────────────────┘
> ```
>
> **技术选型理由：**
>
> - **后端 FastAPI**：原生 async 支持，适合 LLM 流式调用与 MongoDB 异步驱动 motor
> - **MongoDB**：简历字段灵活（技能数组、工作经历嵌套），文档型数据库无需 schema 迁移
> - **Milvus**：专为向量检索设计，支持稠密+稀疏混合检索
> - **Redis**：Token 黑名单 + 检索结果缓存（5 分钟 TTL）
> - **MinIO**：简历原始文件对象存储，支持预签名 URL 预览
> - **BGE-M3**：开源中文向量化模型，同时输出稠密+稀疏向量
> - **通义千问 qwen-plus**：OpenAI 兼容接口，支持 JSON 模式输出结构化评分

---

### P5.5 · 核心数据流全景图（补充页）

> 以下是系统 4 条核心数据链路的完整流转图，展示用户输入如何流经各模块，以及每个模块内部调用了哪些技术组件。
>
> ```mermaid
> flowchart TB
>     %% ===== 链路1: 简历上传解析 =====
>     subgraph L1["🔗 链路1：简历上传解析"]
>         direction TB
>         U1["👤 用户上传<br/>DOCX / PDF / 图片"] --> A1["API<br/>POST /resumes/upload"]
>         A1 --> S1["ResumeService.upload"]
>         S1 --> M1[("MinIO<br/>存储原始文件")]
>         S1 --> DB1a[("MongoDB<br/>insert 占位 parsing")]
>         DB1a --> P1["后台异步 _parse_and_index"]
>         P1 --> T1["文本提取<br/>PyMuPDF / python-docx<br/>—— OCR降级: RapidOCR"]
>         T1 --> LLM1["LLM 结构化解析<br/>qwen-plus · JSON模式"]
>         LLM1 --> RG1["正则兜底 + 去重检查<br/>phone/email hash"]
>         RG1 --> CK1["父子块切分<br/>split_parent_child"]
>         CK1 --> EM1["🔒 BGE-M3 编码<br/>dense + sparse 向量"]
>         EM1 --> VS1[("Milvus<br/>写入向量")]
>         VS1 --> DB1b[("MongoDB<br/>update 结构化 completed")]
>     end
> 
>     %% ===== 链路2: 语义检索 =====
>     subgraph L2["🔍 链路2：语义检索"]
>         direction TB
>         U2["👤 HR 自然语言查询<br/>'5年前端工程师'"] --> A2["API<br/>POST /search"]
>         A2 --> S2["SearchService.search"]
>         S2 --> RC[("Redis<br/>读缓存(5min TTL)")]
>         RC -- "未命中" --> ST["策略选择器<br/>direct/decompose/semantic"]
>         ST --> RW["查询改写<br/>多改写提升召回"]
>         RW --> LOOP["对每个改写查询循环"]
>         LOOP --> EM2["🔒 BGE-M3 编码"]
>         EM2 --> VS2[("Milvus<br/>Hybrid检索<br/>dense×1.0 + sparse×0.7")]
>         VS2 --> DEDUP["chunk_id 去重"]
>         DEDUP --> RR["🔒 BGE-Reranker 精排<br/>cross-encoder 重排序"]
>         RR --> DB2[("MongoDB<br/>批量拉取候选人元数据")]
>         DB2 --> LLM2["LLM 4维度评分<br/>skill/exp/edu/salary<br/>asyncio.gather 并发"]
>         LLM2 --> RC2[("Redis<br/>写缓存")]
>         RC2 --> R2["返回候选人卡片列表<br/>按 overall 降序"]
>     end
> 
>     %% ===== 链路3: 智能对话 =====
>     subgraph L3["💬 链路3：智能对话（Agent工作流）"]
>         direction TB
>         U3["👤 用户消息<br/>'推荐前端工程师'"] --> A3["API<br/>POST /chat/messages · SSE"]
>         A3 --> S3["AgentService.send_message_stream"]
>         S3 --> HIST[("MongoDB<br/>加载最近10条历史")]
>         HIST --> N1["节点1: 意图识别<br/>LLM 分类 5类<br/>chitchat/search/detail/compare/qa"]
>         N1 -->|"yield SSE intent"| N2{意图判断}
>         N2 -->|"search/compare/detail"| N3["节点2: 检索+精排<br/>复用 SearchService.search"]
>         N3 -->|"yield SSE<br/>retrieval→rank→candidates"| N4["节点3: LLM 流式回答<br/>qwen-plus chat_stream"]
>         N2 -->|"chitchat/qa"| N4
>         N4 -->|"yield SSE token ×N"| N5[("MongoDB<br/>保存消息+更新会话标题")]
>         N5 -->|"yield SSE done"| R3["前端实时渲染<br/>token流 + 候选人卡片"]
>     end
> 
>     %% ===== 链路4: JD匹配 =====
>     subgraph L4["📄 链路4：JD匹配"]
>         direction TB
>         U4["👤 HR 粘贴JD文本"] --> A4["API<br/>POST /jd/match"]
>         A4 --> S4["JdMatchService.match_jd"]
>         S4 --> LLM4a["LLM 解析JD<br/>提取 title/skills/years/salary"]
>         LLM4a --> EM4["🔒 BGE-M3 编码"]
>         EM4 --> VS4[("Milvus<br/>Hybrid检索")]
>         VS4 --> RR4["🔒 BGE-Reranker 精排"]
>         RR4 --> DB4[("MongoDB<br/>拉取候选人元数据")]
>         DB4 --> LLM4b["LLM 生成匹配理由<br/>串行 · 每个候选人"]
>         LLM4b --> R4["返回匹配结果<br/>match_score + reason"]
>     end
> 
>     %% ===== 共享基础设施层 =====
>     subgraph INFRA["⚙️ 共享基础设施"]
>         direction LR
>         I1[("MongoDB<br/>简历/会话/用户/评价")]
>         I2[("Redis<br/>缓存/Token黑名单")]
>         I3[("Milvus<br/>向量库")]
>         I4[("MinIO<br/>文件存储")]
>         I5["🔒 BGE-M3<br/>向量化模型"]
>         I6["🔒 BGE-Reranker<br/>精排模型"]
>         I7["🤖 qwen-plus<br/>LLM 通义千问"]
>     end
> 
>     %% 跨链路标注（虚线表示共享组件）
>     EM1 -.-> I5
>     EM2 -.-> I5
>     EM4 -.-> I5
>     RR -.-> I6
>     RR4 -.-> I6
>     LLM1 -.-> I7
>     LLM2 -.-> I7
>     N1 -.-> I7
>     N4 -.-> I7
>     LLM4a -.-> I7
>     LLM4b -.-> I7
> ```
>
> **4 条链路对比：**
>
> | 链路 | 入口 | 核心组件调用顺序 | 特色 |
> |------|------|-----------------|------|
> | 简历解析 | `POST /resumes/upload` | MinIO → 文本提取(+OCR降级) → LLM解析 → 去重 → BGE-M3 → Milvus → MongoDB | 全流程自动化，OCR兜底 |
> | 语义检索 | `POST /search` | Redis缓存 → 策略选择 → 查询改写 → [BGE-M3 → Milvus Hybrid]×N → Reranker → MongoDB → LLM评分 → Redis | 多改写召回 + 双层精排 |
> | 智能对话 | `POST /chat/messages` | 意图识别LLM → [检索+精排] → LLM流式回答 → SSE推送 → MongoDB | Agent动态路由 + SSE实时 |
> | JD匹配 | `POST /jd/match` | LLM解析JD → BGE-M3 → Milvus → Reranker → MongoDB → LLM匹配理由 | 无LLM评分，rerank_score直接定分 |

---

### P6 · 后端三层架构（1min）

> 后端严格遵循 **api → services → core** 三层架构：
>
> ```
> ┌─────────────────────────────────────────────────┐
> │            API 层 (app/api)                     │
> │   11 个路由模块 · 请求校验 · 依赖注入 · 统一响应 │
> ├─────────────────────────────────────────────────┤
> │          Services 层 (app/services)             │
> │   14 个 service · 业务编排 · LLM/检索/DB 调用    │
> ├─────────────────────────────────────────────────┤
> │            Core 层 (app/core)                   │
> │   MongoDB · Redis · LLM · Embedding · 向量库     │
> │   Logger · Metrics · Health · Config            │
> └─────────────────────────────────────────────────┘
> ```
>
> **工程规范：**
>
> 1. 所有接口统一前缀 `/api/v1/[module]`，统一响应格式 `{code, message, data, trace_id}`
> 2. 每个文件开头写元信息（文件名/创建时间/作者/功能描述），每个函数写文档注释标明入参出参
> 3. 核心逻辑和对外接口都有 try...except 兜底，记录日志并返回合理状态码
> 4. 配置分离：敏感信息走 `.env`，禁止硬编码

---

### P7 · 前端架构与设计系统（1min）

> 前端采用 **Views → Components → Stores/API** 单向数据流。
>
> **关键设计：**
>
> - **Axios 拦截器**：请求注入 `Authorization`，响应剥离 `{code, message, data}` 外层，业务代码只处理 data
> - **Token 失效处理**：响应业务码 1002 自动清空 token 跳转登录页
> - **SSE 流式封装**：用 `fetch + ReadableStream` 实现 POST 请求 + 8 种事件分发
> - **Pinia 状态管理**：auth/chat/resume/app 四个 store，auth 状态持久化到 localStorage
> - **路由守卫**：`meta.requireAdmin` 控制管理员页面，`beforeEach` 全局守卫校验登录态
>
> **设计系统**：采用自研 **Editorial Tech** 设计风格 —— 深墨绿主色（#0f3d3a）+ 琥珀金强调色（#c8a45c）+ Fraunces 衬线标题字体 + grain 纹理质感，区别于常见 Element Plus 默认蓝色风格。

---

### P8 · 核心技术1：AI 检索流水线（2min）

> 这是项目的第一个核心技术点 —— **Hybrid 向量检索 + Reranker 精排** 的完整流水线。
>
> ```
> 用户查询
>     ↓
> 策略选择器（direct/decompose/semantic）← 基于 query + history
>     ↓
> 查询改写（多改写提升召回）
>     ↓
> BGE-M3 编码（同时输出稠密 + 稀疏向量）
>     ↓
> Milvus Hybrid 检索（稠密*1.0 + 稀疏*0.7 加权融合）
>     ↓
> 去重（chunk_id 去重）
>     ↓
> BGE-Reranker-v2-m3 精排（cross-encoder 重排序）
>     ↓
> MongoDB 拉取候选人元数据
>     ↓
> LLM 4 维度评分（JSON 模式）
>     ↓
> 返回候选人卡片列表（按 overall 降序）
> ```
>
> **为什么用 Hybrid 检索？**
>
> - **稠密向量** 捕捉语义相似性（"前端" ≈ "Vue/React"）
> - **稀疏向量** 捕捉关键词匹配（"Java" 必须精确命中）
> - 两者加权融合（1.0 : 0.7）兼顾召回率与精确率
>
> **为什么用 Reranker 二次精排？**
>
> 向量检索是双塔模型（query 和 doc 独立编码），精度有限。Reranker 是 cross-encoder（query 和 doc 拼接编码），精度更高但速度慢。所以先用向量检索召回 20 条，再用 Reranker 精排取 Top 10。
>
> **缓存策略**：检索结果按 `query + filters + top_k` 作为 key 缓存到 Redis，TTL 5 分钟，相同查询直接命中缓存跳过整个流水线。

---

### P9 · 核心技术1：4 维度透明评分（1.5min）

> 这是项目针对"评分黑箱"痛点的核心创新 —— **4 维度透明评分**。
>
> **传统评分**：单一分数，HR 不知道为什么 85 分。
>
> **TalentSense 评分**：
>
> | 维度 | 含义 | 评分依据 |
> |------|------|---------|
> | skill | 技能匹配度 | 候选人技能与需求关键词重合度 |
> | experience | 工作经验匹配度 | 年限与岗位级别匹配 |
> | education | 学历匹配度 | 学历层次与岗位要求匹配 |
> | salary | 薪资匹配度 | 期望薪资与市场水平合理性 |
> | overall | 综合分 | 4 维度加权或 LLM 直接给分 |
> | reason | 推荐理由 | 一句话说明为什么匹配/不匹配 |
>
> **实现细节：**
>
> 1. LLM 用 `response_format={"type": "json_object"}` 强制 JSON 输出，避免解析失败
> 2. system prompt 明确禁止返回 null，每个维度必须有 0-100 的数值
> 3. **两级兜底**：
>    - LLM 调用失败（网络/超时）→ 4 维度全部回退 `rerank_score * 100`
>    - LLM 返回但 JSON 解析失败 → 全 0 + reason="评分暂不可用"
> 4. **overall 兜底**：LLM 没给 overall 时按 `0.3*skill + 0.3*experience + 0.2*education + 0.2*salary` 加权计算
>
> **前端展示**：候选人卡片除星级评分外，新增 4 维度彩色进度条（技能紫/经验绿/学历黄/薪资粉），HR 一眼看出候选人强项与短板。

---

### P10 · 核心技术2：Agent 工作流（2min）

> 这是项目的第二个核心技术点 —— 基于 **LangGraph 的 Agent 工作流**。
>
> ```
> 用户输入
>     ↓
> ┌───────────────────────────────────┐
> │   意图识别节点（LLM 分类 5 类）    │
> └───────────────────────────────────┘
>     ↓
> ┌───────┬───────┬───────────┬───────┐
> ↓       ↓       ↓           ↓       ↓
> chitchat  search  detail/    compare  qa
>                  compare
> ↓       ↓       ↓           ↓       ↓
> CHITCHAT  检索+精排  检索+精排  检索+精排  QA_PROMPT
> PROMPT    +评分     +评分     +评分    直接回答
> ↓       ↓       ↓           ↓       ↓
> └───────┴───────┴───────────┴───────┘
>                 ↓
>         LLM 流式回答（SSE token 推送）
>                 ↓
>         保存消息 + 首条消息更新会话标题
>                 ↓
>         done 事件（携带 title）
> ```
>
> **为什么用 Agent 而不是固定流程？**
>
> 不同意图需要不同的处理路径：闲聊不需要检索，QA 不需要检索但需要知识回答，检索类意图才走完整的检索+评分流水线。Agent 通过意图识别动态路由，避免无效计算。
>
> **LangGraph 的优势：**
>
> - 节点之间通过 State 共享数据（query/history/candidates/intent_type）
> - 支持条件路由（基于 intent_type 分发到不同处理分支）
> - 可观测性（每个节点的输入输出都可日志追踪）
>
> **关键决策**：service 层直接调用节点函数（`intent_node` / `retrieve_rank_node`），而不是通过 `graph.invoke()`。这样可以在 SSE 流式响应中精细控制每个事件的产出时机。

---

### P11 · 核心技术2：5 类意图识别（1min）

> 意图识别是 Agent 工作流的入口，决定了后续走哪条处理路径。
>
> | 意图 | 触发场景 | 处理路径 |
> |------|---------|---------|
> | chitchat | 闲聊/打招呼（"你好"/"谢谢"） | CHITCHAT_PROMPT 直接回答 |
> | search | 搜索/推荐候选人（"推荐前端工程师"） | 检索+精排+评分 |
> | detail | 查询某候选人详情（"张三的简历"） | 检索+定位候选人+详细介绍 |
> | compare | 对比候选人（"对比张三和李四"） | 检索+横向对比 |
> | qa | HR 知识/系统使用/通用问答 | QA_PROMPT 直接回答 |
>
> **设计要点：**
>
> 1. **qa 意图兜底**：意图识别失败或返回非 5 类时，兜底为 qa 而非 chitchat，确保用户问题总能得到有意义的回答
> 2. **历史上下文**：意图识别传入最近 5 条历史消息，避免上下文断裂（如用户先问"推荐前端"，再问"第二个怎么样"应识别为 detail）
> 3. **Prompt 约束**：明确告诉 LLM "只返回意图名"，避免解释性输出
>
> **推荐卡片智能保留**：chitchat/qa 意图保留既有推荐卡片不覆盖，仅 search/compare/detail 意图才更新卡片（含空结果），避免追问时卡片消失。

---

### P12 · 核心技术2：SSE 流式响应（1min）

> 对话接口使用 **Server-Sent Events** 实时推送，提升用户体验。
>
> **8 种事件类型：**
>
> | 事件 | 时机 | 数据 |
> |------|------|------|
> | intent | 意图识别完成 | `{intent, strategy}` |
> | rewrite | 查询改写完成 | `{query, rewrites}` |
> | retrieval | 检索完成 | `{count, candidate_ids}` |
> | rank | 精排完成 | `{ranked: [{candidate_id, score}]}` |
> | candidates | 候选人卡片 | `CandidateCard[]` |
> | token | LLM 流式 token | `{delta}` |
> | done | 全部完成 | `{message_id, response, title}` |
> | error | 异常 | `{code, message}` |
>
> **为什么选 SSE 而不是 WebSocket？**
>
> - SSE 是单向推送，足够 LLM 流式场景
> - 基于 HTTP，无需升级协议，穿过代理/CDN 更友好
> - FastAPI 原生支持 `StreamingResponse`
>
> **前端实现**：用 `fetch + ReadableStream` 而非 `EventSource`，因为 `EventSource` 只支持 GET，而发送消息是 POST 请求。手动解析 `event: xxx\ndata: xxx\n\n` 格式的事件块。
>
> **会话标题自动生成**：首条消息后端用 `query[:20]` 自动更新会话标题，通过 done 事件的 `title` 字段回传前端同步，避免所有会话都叫"新会话"。

---

### P13 · 核心技术3：RBAC 权限体系（1min）

> 这是项目的第三个核心技术点 —— **全栈工程能力**，首先是 RBAC 权限体系。
>
> **双角色模型：admin / hr**
>
> ```
> 注册申请 → pending ──admin 审批──→ approved ──禁用──→ disabled
>              │                       ↑──启用──┘
>              └──admin 直接开号（status=approved）
> ```
>
> | 模块 | admin | hr |
> |------|-------|-----|
> | 工作台/对话/简历库/JD 匹配/数据看板 | ✅ | ✅ |
> | 简历删除 | ✅ | ❌ |
> | SMTP 邮件配置 | ✅ | ❌ |
> | 用户管理 | ✅ | ❌ |
>
> **双层校验：**
>
> - **后端**：`app/api/deps.py` 提供 `get_current_user` 与 `require_admin` 依赖；admin only 接口直接 `Depends(require_admin)` 返回 403 (code=1003)
> - **前端**：路由 `meta.requireAdmin = true` + 全局 `beforeEach` 守卫；菜单项 `v-if="authStore.user?.role === 'admin'"` 控制显隐
>
> **状态机校验**：
> - `status === 'pending'` 返回 401 (code=1006) 提示待审批
> - `status === 'disabled'` 返回 401 (code=1007) 提示已禁用
>
> **管理员自动初始化**：后端 lifespan 启动时检查 admin 账号是否存在，不存在则按 `.env` 配置自动创建，旧库自动回填 email/name 字段。

---

### P14 · 核心技术3：邮件模板系统（1min）

> 邮件系统覆盖招聘全流程通知场景，支持模板 + 自定义两种发送模式。
>
> **4 个预置模板：**
>
> | 模板 | 变量 |
> |------|------|
> | 面试邀请 | candidate_name / position / interview_time / company / address |
> | Offer 通知 | candidate_name / position / salary / company |
> | 拒绝通知 | candidate_name / position / company |
> | 进度通知 | candidate_name / status / company |
>
> **技术细节：**
>
> 1. **Jinja2 沙箱渲染**：`SandboxedEnvironment` + `StrictUndefined` + `autoescape=True`，仅允许 `{{ var }}` 变量替换，禁用 `{% %}` 控制结构，防止模板注入攻击
> 2. **变量自动提取**：前端用正则 `\{\{\s*(\w+)\s*\}\}` 从模板正文提取变量名，自动生成变量填写表单
> 3. **SMTP 加密存储**：密码 base64 加密入库，支持 SSL/TLS（465）与 STARTTLS（587）
> 4. **密码留空不覆盖**：设置页保存配置时密码留空表示不修改原密码（支持仅改主机/端口场景）
> 5. **预置模板只读**：4 个预置模板标记 `is_builtin=True`，不可编辑删除，仅 admin 可管理自定义模板
> 6. **异步发送**：用 `aiosmtplib` 异步发送，不阻塞 API 响应
>
> **联动设计**：简历详情页"发送邮件"按钮直接打开 `SendEmailDialog`，预填候选人姓名/职位/公司/薪资/面试时间变量，HR 无需手动复制粘贴。

---

### P15 · 工程质量保障（1.5min）

> 这是项目工程能力的核心体现 —— **405 个测试全部通过**。
>
> | 类型 | 数量 | 覆盖范围 |
> |------|------|---------|
> | 后端单元/集成测试 | 240 | API/Services/Core/Agent/Utils 各层 |
> | 后端 E2E 测试 | 32 | 端到端招聘闭环业务流程 |
> | 前端单元/组件测试 | 133 | API/Stores/Router/Components/Views |
> | **合计** | **405** | **全部通过** |
>
> **后端 E2E 测试 —— 32 步招聘闭环：**
>
> 这是我最自豪的工程实践。32 个测试用例串成一个完整的业务闭环：
>
> ```
> 登录(3步) → 简历管理(9步) → 检索(1步) → 对话(3步) → JD 匹配(1步)
>          → 面试(3步) → 对比(2步) → 导出邮件(3步) → 看板(1步) → 协议校验(1步)
> ```
>
> 数据在 9 个 API 路由间真实流转：上传的简历被检索到、被推荐、被对比、被发邮件、被导出。
>
> **自建 FakeMongoDB / FakeRedis**：为了不依赖真实 MongoDB，我自建了内存数据库，支持 `$set`/`$push`/`$each`/`$slice`/`$in`/`$gte`/`$lte`/`$regex`/`$or`/`$and` 等 MongoDB 操作符。
>
> **ExitStack 管理 24 个 patch**：规避 Python 静态嵌套块限制，动态注入 mock。
>
> **测试驱动开发（TDD）**：所有新功能先写测试再写实现，每个 bug 修复先复现再修复。

---

### P16 · 生产级运维：Docker 部署 + 可观测性（1.5min）

> 这是项目从"能跑"到"能上线"的关键一步 —— **Docker 一键部署 + 完整可观测性体系**。

**Docker 化部署：**

> ```
> docker-compose up -d  →  7 个容器自动编排启动
> ┌──────────┬──────────┬──────────┬──────────┬──────────┐
> │ MongoDB  │  Redis   │  MinIO   │  Milvus  │  etcd    │
> ├──────────┴──────────┼──────────┴──────────┴──────────┤
> │    Backend (FastAPI) │      Frontend (Nginx + Vue)    │
> └─────────────────────┴────────────────────────────────┘
> ```
>
> - **多阶段构建**：前端 Node 20 构建 → Nginx 运行；后端 Python 3.12-slim 精简镜像
> - **服务编排**：docker-compose 统一管理 7 个容器，含依赖顺序、健康检查、数据持久化
> - **MinIO 自初始化**：minio-init 容器自动创建 bucket，无需手动操作
> - **Nginx 反向代理**：前端静态资源 + `/api` 代理后端 + Gzip 压缩

**可观测性体系：**

> | 层面 | 方案 | 端点 |
> |------|------|------|
> | 结构化日志 | loguru JSON 格式 + trace_id 全链路追踪 | 日志文件 |
> | Prometheus 指标 | QPS/延迟/在途请求/简历解析/LLM 调用 | `/metrics` |
> | 深度健康检查 | 并发探测 MongoDB/Redis/MinIO/Milvus 连通性 | `/health/ready` |
> | Sentry 错误追踪 | 未捕获异常自动上报 + 性能追踪 | 可选开关 |
> | 前端错误监控 | JS 错误/Promise rejection/资源错误自动上报 | `POST /api/v1/monitor/error` |
>
> **关键设计：**
>
> 1. **日志环境区分**：DEBUG 环境彩色人类可读格式，生产环境 JSON 结构化输出（Loki/ELK 友好）
> 2. **trace_id 全链路**：请求中间件注入 trace_id，贯穿日志/响应头/前端错误上报
> 3. **健康检查超时保护**：每个依赖探测 3s 超时，避免单个依赖卡住整个就绪检查
> 4. **前端错误节流**：500ms 节流防止刷屏，`keepalive: true` 确保页面卸载时不丢失

---

### P17 · 项目亮点与创新点（1min）

> 总结项目 6 大亮点：
>
> **1. Hybrid 检索 + Reranker 双层精排**
> 稠密+稀疏向量加权融合提升召回，cross-encoder 精排提升精度，兼顾速度与准确率。
>
> **2. 4 维度透明评分体系**
> 行业首创的 skill/experience/education/salary 4 维度评分 + 推荐理由，让 HR 看懂每个分数，解决黑箱问题。
>
> **3. 5 类意图 Agent 动态路由**
> LangGraph Agent 根据意图动态选择处理路径，闲聊/qa 跳过检索，检索类才走完整流水线，避免无效计算。
>
> **4. 全栈 RBAC + 邮件模板系统**
> 双角色权限双层校验 + Jinja2 沙箱模板渲染 + SMTP 加密存储，达到生产级安全标准。
>
> **5. Docker 一键部署 + 可观测性体系**
> docker-compose 编排 7 个容器一键启动；结构化日志 + Prometheus 指标 + 深度健康检查 + Sentry 错误追踪 + 前端错误监控，达到生产级运维标准。
>
> **6. 405 个测试 + 32 步 E2E 闭环**
> 测试覆盖率行业领先，E2E 测试自建 FakeMongoDB 实现真实数据流转，确保功能正确性。

---

### P18 · 难点与解决方案（1min）

> 项目开发过程中遇到三个主要难点：
>
> **难点1：BGE-M3 依赖问题**
> FlagEmbedding 1.2.11 存在两个 bug：`trainer.py` 缺少 `typing.Optional` 导入；reranker 导入未守护 `peft` 依赖。
> **解决**：本地 patch 修复源码，不修改 site-packages，通过 `sys.path` 优先加载本地修复版。
>
> **难点2：Milvus 序列化错误**
> BGEM3FlagModel.encode 返回 numpy 类型，Milvus protobuf 序列化报错。
> **解决**：在 `vector_store.py` 中统一转换 `numpy.float32 → float`、`numpy.ndarray → list`。
>
> **难点3：模块级 MongoDB 初始化导致连接失败**
> service 类在模块导入时初始化 collection，但此时 FastAPI lifespan 尚未连接 MongoDB。
> **解决**：将 6 个 service 类的 collection 访问改为 `@property` 延迟初始化，首次访问时才获取 `MongoDB.db.xxx`。
>
> **难点4：LLM 评分 JSON 解析失败**
> LLM 偶尔返回非 JSON 格式（带解释文字）导致 `json.loads` 崩溃。
> **解决**：两级 try/except —— LLM 调用失败回退 rerank_score，JSON 解析失败全 0 兜底，确保评分接口永不崩溃。

---

### P19 · 总结与展望 / Q&A（1min）

> **项目总结：**
>
> TalentSense HR 实现了一套完整的 AI 智能招聘全栈系统，覆盖招聘全链路 22 个功能点，核心技术包括 Hybrid 向量检索、4 维度透明评分、LangGraph Agent 工作流、全栈 RBAC 权限体系。代码规模约 19500 行，405 个测试全部通过，Docker 一键部署 + 完整可观测性体系，达到生产级工程质量。
>
> **个人收获：**
>
> 1. 全栈开发能力：FastAPI + Vue3 + MongoDB + Milvus 全栈技术栈实战
> 2. AI 工程能力：LLM 应用开发、向量检索、Agent 工作流、Prompt Engineering
> 3. 工程规范能力：TDD 测试驱动、三层架构、统一响应格式、配置分离
> 4. 问题解决能力：依赖冲突、序列化错误、模块初始化时序等真实工程问题
>
> **未来展望：**
>
> 1. **多模态简历解析**：支持扫描版 PDF OCR（已集成 RapidOCR）+ 图片简历识别
> 2. **主动学习优化**：根据 HR 点击/收藏行为优化检索排序权重
> 3. **面试辅助增强**：基于候选人简历生成个性化面试题 + 评价模板
> 4. **GPU 推理加速**：当前 Docker 部署已就绪，后续可接入 GPU 节点加速 BGE-M3/Reranker 推理
>
> 感谢老师与同学聆听，欢迎提问。

---

## 答辩问答准备（Q&A）

### 可能被问到的问题与回答

**Q1：为什么选 BGE-M3 而不是 OpenAI text-embedding-3？**

> BGE-M3 是开源中文向量化模型，同时输出稠密+稀疏向量，适合中文简历场景且无需付费 API 调用。OpenAI 模型只输出稠密向量，且中文效果不如专门训练的 BGE 系列。

**Q2：4 维度评分的权重 0.3/0.3/0.2/0.2 怎么来的？**

> 这是兜底加权（LLM 没给 overall 时使用），参考了招聘行业常见权重：技能和经验更重要（各 0.3），学历和薪资权重略低（各 0.2）。实际优先使用 LLM 直接给出的 overall 分数。

**Q3：为什么用 LangGraph 而不是直接 if-else 分支？**

> LangGraph 提供了 State 管理、节点路由、可观测性等基础设施。虽然当前流程可以用 if-else 实现，但 LangGraph 便于后续扩展（如增加工具调用节点、循环重试节点），且节点之间的 State 共享让数据流更清晰。

**Q4：测试用了 mock，如何保证真实环境可用？**

> 三个层面保障：1) E2E 测试自建 FakeMongoDB 支持 MongoDB 操作符，数据在 9 个路由间真实流转；2) 已在真实 MongoDB + Milvus 环境验证 8 个核心接口；3) service 类用 `@property` 延迟初始化解决了 mock 与真实环境的初始化时序差异。

**Q5：SSE 流式响应如何处理 LLM 调用失败的兜底？**

> 三层兜底：1) LLM 流式调用异常时 `full_response = "抱歉，生成回复时出错"`；2) 整个 send_message_stream 用 try/except 包裹，异常时 yield error 事件；3) 消息保存失败不阻塞响应，至少保证 done 事件能产出。

**Q6：RBAC 为什么只设计 admin/hr 两个角色？**

> 招聘场景角色相对简单：HR 是主要使用者，admin 负责系统管理。如果未来需要更细粒度（如"简历审核员"、"面试官"），可以在 role 字段扩展，依赖注入框架 `require_role("reviewer")` 即可支持。

**Q7：Milvus 为什么存 resume_id 而不是 candidate_id？**

> 历史原因：早期简历模型没有 candidate_id 字段，直接用 resume_id 作为唯一标识。后续为支持简历覆盖更新引入了 candidate_id（同一候选人多份简历共享），但 Milvus 中字段名仍是 candidate_id 实际存 resume_id，通过 chunk_map 映射转换。这是一个待重构的技术债。

**Q8：邮件模板为什么用 Jinja2 沙箱而不是直接字符串替换？**

> 直接字符串替换（`str.replace`）无法处理变量缺失、HTML 转义等问题。Jinja2 沙箱模式提供：1) `autoescape=True` 自动 HTML 转义防 XSS；2) `StrictUndefined` 变量缺失报错而非静默；3) `SandboxedEnvironment` 禁用危险操作（如 `{% %}` 控制结构）防止模板注入。

**Q9：项目最难的 part 是什么？**

> 不是单个技术点，而是**全栈整合**。后端三层架构、前端组件设计、AI 模型调用、向量数据库、对象存储、消息队列、权限校验、邮件发送 —— 把这些组件整合成一个流畅的系统，且每个组件都有测试覆盖，是最难的。E2E 测试的 32 步闭环就是为了验证整合的正确性。

**Q10：如果重做这个项目，你会怎么改进？**

> 1) **Milvus 字段命名规范化**：candidate_id 字段直接存 candidate_id，避免 chunk_map 映射；2) **评分权重可配置**：把 0.3/0.3/0.2/0.2 抽到 .env 或数据库，admin 可调；3) **前端组件库抽离**：CandidateCard 等组件可抽离为独立 npm 包复用；4) **GPU 推理加速**：当前 Docker 部署已就绪，但 BGE-M3/Reranker 在 CPU 上推理较慢，后续可接入 GPU 节点。

---

## 答辩演示流程建议（可选现场演示）

若答辩包含现场演示，建议按以下流程展示（约 3-5 分钟）：

1. **登录**（30s）：用 .env 中配置的 ADMIN_EMAIL / ADMIN_PASSWORD 登录，展示邮箱登录方式
2. **简历上传**（1min）：上传一份 DOCX 简历，展示后台解析流程（状态从 parsing → ready）
3. **工作台对话**（1.5min）：
   - 输入"推荐前端工程师"→ 展示 SSE 流式 token + 4 维度评分卡片
   - 追问"第二个候选人怎么样"→ 展示卡片保留 + 意图切换为 detail
   - 问"系统怎么用"→ 展示 qa 意图直接回答
4. **JD 匹配**（1min）：粘贴一段 JD 文本，展示匹配结果与理由
5. **数据看板**（30s）：展示 7 维度图表（招聘漏斗、入库趋势、技能/学历/薪资/经验分布、面试结果）
6. **用户管理**（30s）：展示 admin 创建用户、审批注册申请

---

## 文档版本

| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| v1.0 | 2026-06-28 | TalentSense Team | 初版答辩文档 |
| v2.0 | 2026-06-28 | TalentSense Team | 新增 P16 生产级运维（Docker+可观测性）；更新测试数量至 405；更新数据看板至 7 维度 |
| v2.1 | 2026-06-28 | TalentSense Team | 新增 P5.5 核心数据流全景图（Mermaid），展示4条链路从用户输入到模块到技术组件的完整流转 |
