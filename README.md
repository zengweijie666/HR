# TalentSense HR

> 基于 AI 的智能简历推荐与招聘辅助系统（全栈）

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4-42b883.svg)](https://vuejs.org/)
[![Tests](https://img.shields.io/badge/tests-440%20passed-brightgreen.svg)](#测试)
[![Version](https://img.shields.io/badge/version-3.1.0-orange.svg)](#)

---

## 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [权限与角色（RBAC）](#权限与角色rbac)
- [邮件系统](#邮件系统)
- [技术栈](#技术栈)
- [架构设计](#架构设计)
- [性能优化](#性能优化)
- [Docker 部署](#docker-一键部署推荐)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [API 接口](#api-接口)
- [测试](#测试)
- [开发规范](#开发规范)
- [文档](#文档)

---

## 项目简介

TalentSense HR 是一套面向 HR 的智能招聘辅助全栈系统，依托大语言模型（LLM）、向量检索、Reranker 精排与 Agent 工作流，实现从简历入库、智能解析、语义检索、JD 匹配、对话式推荐到面试辅助的全链路数字化招聘闭环。

系统以「简历推荐」为核心，融合 Hybrid 向量检索（BGE-M3 稠密+稀疏）与 BGE-Reranker 精排，并通过 LangGraph Agent 实现自然语言对话式交互，帮助 HR 从海量简历中高效定位合适候选人。前端采用 Vue3 + TypeScript + Element Plus，以 Editorial Tech 设计美学（深墨绿主色 + 琥珀金强调色 + Fraunces 衬线标题）呈现精致专业的招聘工作台。

## 功能特性

### 核心业务模块（覆盖 22 个功能验收点 F01-F22）

| 模块 | 功能 | 验收点 |
|------|------|--------|
| 认证管理 | **邮箱+密码登录**、Token 刷新、当前用户、登出、注册申请、改密 | F01-F02 |
| 简历管理 | 上传解析、列表查询、详情查看、标签/收藏/备注、过滤、预览、删除 | F03-F10 |
| 候选人检索 | 自然语言语义检索、Hybrid 检索 + Reranker 精排 | F11 |
| 智能对话 | 多轮对话会话、SSE 流式响应、对话历史、5 类意图识别、上下文感知复用候选人、4 维度透明评分、会话标题自动生成 | F12-F13 |
| JD 匹配 | LLM 解析 JD、检索 + 精排、匹配理由生成 | F14 |
| 面试辅助 | AI 生成面试题、保存面试评价、查询评价 | F15-F16 |
| 候选人对比 | 多候选人横向对比、相似推荐 | F17-F18 |
| 邮件通知 | **模板发送（4 个预置+自定义）+ SMTP 配置 + 测试邮件** | F19 |
| 数据看板 | 7 维度可视化：招聘漏斗、入库趋势、技能/学历/薪资/经验分布、面试结果 | F20 |
| 数据导出 | 候选人列表 Excel 导出 | F21 |
| 404 处理 | 统一 404 响应 | F22 |
| 用户管理 | 用户列表/创建/审批/启禁用/重置密码/删除（admin only） | — |

### 技术亮点

- **Hybrid 检索**：BGE-M3 同时输出稠密 + 稀疏向量，加权融合提升召回
- **Reranker 精排**：BGE-Reranker-v2-m3 对初筛结果二次排序
- **LangGraph Agent**：意图识别 → 工具选择 → 执行 → 回答的工作流编排
- **PII 脱敏**：手机号/邮箱/身份证入库前自动脱敏与哈希
- **简历去重**：基于手机号 + 邮箱哈希的多维度查重
- **统一响应格式**：`{code, message, data, trace_id}` 全链路追踪
- **SSE 流式**：对话接口使用 Server-Sent Events 实时推送 token
- **Editorial Tech 设计**：深墨绿 + 琥珀金配色，Fraunces 衬线标题，grain 纹理质感
- **RBAC 权限**：admin / hr 双角色，FastAPI 依赖注入 + 前端路由守卫双层校验
- **邮箱登录**：登录统一使用邮箱+密码，注册/创建用户时 email/name 必填，users 表 email 唯一索引
- **邮件模板系统**：Jinja2 沙箱渲染（StrictUndefined + autoescape），4 个预置模板（面试邀请/Offer/拒绝/进度）+ 自定义模板，预置模板不可改删
- **SMTP 加密存储**：密码 base64 加密入库，支持 SSL/TLS（465）与 STARTTLS（587），密码留空保存时保留原值
- **管理员自动初始化**：后端启动时若 admin 账号不存在则自动创建（凭据走 `.env`），旧库自动回填 email/name 字段
- **5 类意图识别**：chitchat/search/detail/compare/qa，qa 兜底处理 HR 知识/系统使用/通用问答，避免误触检索
- **对话上下文感知**：compare/detail/qa 意图自动复用历史候选人列表，不触发重复检索；qa 意图将候选人数据注入 system prompt，使 LLM 能基于评分数据回答"为什么 A 比 B 分高"等问题
- **同义词扩展检索**：direct 策略新增 LLM 同义词扩展（如"NLP"→"BERT FastText Transformer 自然语言处理"），解决稠密向量对领域词与具体技术词相似度不足、BM25 无法跨词关联的问题
- **技能硬过滤**：从自然语言 query 正则提取 `required_skills`（如"有没有会html的"→`["html"]`、"会Python的工程师"→`["python"]`），在 Python 内存层对候选人 skills 做子串匹配硬过滤，确保只返回真正具备该技能的候选人；直接搜索 API 与 Agent 流程均生效
- **三重相关性过滤**：技能硬过滤（required_skills 子串匹配）+ 最低分数截断（overall ≥ 40）+ 简历级去重（按 resume_id 保留最高 rerank_score 的 chunk），避免不相关候选人挤占结果
- **姓名精确匹配**：候选人姓名匹配采用两轮算法（全名子串查找 + 歧义消除），短名是长名子串时保留长名，避免"李志"误匹配"李志鹏"
- **结构化对比分析**：COMPARE_PROMPT 驱动 5 维度对比（工作年限/核心技能/项目经验/学历/评分），强制解释评分差异原因
- **4 维度透明评分**：skill/experience/education/salary 4 维度评分 + overall 综合分 + reason 理由，overall 始终由代码加权计算（0.4×skill + 0.3×experience + 0.2×education + 0.1×salary）确保区分度，LLM JSON 模式输出，含两级兜底（LLM 失败回退 rerank_score，JSON 解析失败全 0）
- **推荐卡片智能保留**：chitchat/qa 意图保留既有推荐卡片，仅 search/compare/detail 意图覆盖（含空结果），避免追问时卡片消失
- **会话标题自动生成**：首条消息自动用 `query[:20]` 更新会话标题，done 事件携带 title 字段前端同步
- **模型异步预热**：BGE-M3 / Reranker / OCR / MinIO 在后台线程池加载，应用启动秒级就绪不阻塞
- **Redis 连接预热**：启动时 `PING` 强制建立 TCP 连接，消除首次请求 2s 延迟
- **请求计时中间件**：自动记录 >200ms 慢请求日志，响应头携带 `X-Response-Time`
- **LLM 评分并发化**：候选人评分用 `asyncio.gather` 并发执行，总耗时≈单次耗时
- **前端 Vite 优化**：依赖预构建 + 关键文件预热 + 代码分割（element-plus / vue-vendor 独立 chunk）
- **路由悬停预加载**：菜单 hover 时预加载路由组件，点击即开无延迟
- **页面切换无白屏**：去掉 transition `out-in` 模式，新旧页面并行过渡
- **Docker 一键部署**：docker-compose 编排 MongoDB/Redis/Milvus/MinIO/前后端7个服务，含健康检查、数据持久化、MinIO bucket自动初始化
- **可观测性体系**：结构化 JSON 日志（按DEBUG/生产自动切换格式）+ trace_id 全链路追踪 + Prometheus `/metrics` 指标端点 + `/health/ready` 深度健康检查（探测Mongo/Redis/MinIO/Milvus连通性）+ 可选 Sentry 错误追踪 + 前端JS错误/Promise rejection/资源加载错误自动上报

## 技术栈

### 后端
- **Python 3.12** + **uv** 包管理
- **FastAPI 0.115** Web 框架
- **Pydantic 2.9** 数据校验
- **uvicorn** ASGI 服务器

### 前端
- **Vue 3.4** + **TypeScript 5.0** + **Vite 5.0**
- **Element Plus 2.6** UI 组件库
- **Pinia 2.1** 状态管理
- **Vue Router 4.2** 路由 + 登录守卫
- **Axios 1.6** HTTP 客户端 + 拦截器统一剥离响应外层
- **ECharts 5.5** 数据可视化
- **Vitest** 单元测试
- **SCSS** + 自定义设计系统

### 数据存储
- **MongoDB**（motor 异步驱动）— 简历、用户、会话、面试评价等结构化数据
- **Redis** — Token 黑名单、缓存
- **Milvus**（pymilvus）— 向量数据库，存储简历切片向量
- **MinIO** — 简历原始文件对象存储

### AI 能力
- **OpenAI 兼容接口**（通义千问 qwen-plus）— LLM 对话与 JSON 结构化输出
- **FlagEmbedding BGE-M3** — 文本向量化（稠密 + 稀疏）
- **FlagEmbedding BGE-Reranker-v2-m3** — 检索结果精排
- **RapidOCR** — 扫描版 PDF / 图片 OCR
- **LangGraph 0.2** — Agent 工作流编排

## 权限与角色（RBAC）

系统采用 **admin / hr 双角色** 模型，通过后端依赖注入 + 前端路由守卫双层校验。

### 账号状态机

```
注册申请  →  pending  ──admin 审批──→  approved  ──禁用──→  disabled
   │                                    ↑──启用──┘
   └──admin 直接开号（status=approved）
```

### 角色权限矩阵

| 模块 | admin | hr |
|------|-------|-----|
| 工作台 / 对话 / 简历库 / JD 匹配 / 数据看板 | ✅ | ✅ |
| 简历删除 | ✅ | ❌ |
| SMTP 邮件配置（GET / PUT `/email/config`） | ✅ | ❌ |
| 用户管理（`/users` 全部接口） | ✅ | ❌ |
| 设置页（前端 `/settings` 路由） | ✅ | ❌ |

### 实现要点

- **后端**：`app/api/deps.py` 提供 `get_current_user` 与 `require_admin` 两个依赖；admin only 接口直接 `Depends(require_admin)` 返回 403 (code=1003)
- **前端**：路由 `meta.requireAdmin = true` + 全局 `beforeEach` 守卫；菜单项 `v-if="authStore.user?.role === 'admin'"` 控制显隐
- **管理员自动初始化**：后端 `lifespan` 启动时检查 `admin` 账号是否存在，不存在则按 `.env` 配置自动创建
- **登录态校验**：`status === 'pending'` 返回 401 (code=1006)；`status === 'disabled'` 返回 401 (code=1007)

## 邮件系统

系统提供完整的邮件通知能力，支持预置模板 + 自定义模板 + 变量渲染，覆盖面试邀请、Offer、拒绝、进度通知等招聘场景。

### 登录方式

- **邮箱 + 密码登录**：登录接口 `POST /api/v1/auth/login` 接收 `{email, password}`，按 email 查询用户
- **字段必填**：注册申请 `/auth/register` 与管理员创建用户 `/users` 的 `email` / `name` 字段均为必填
- **唯一约束**：MongoDB `users` 表对 `email` 字段建立唯一索引，注册/创建时检查重复
- **历史数据迁移**：后端启动时自动回填早期建库缺失 `email`/`name` 字段的 admin 账号

### 邮件模板

| 类型 | 分类 | 是否可改删 | 说明 |
|------|------|-----------|------|
| 面试邀请 | interview | 内置只读 | 含 `candidate_name`/`position`/`interview_time`/`company`/`address` 变量 |
| Offer 通知 | offer | 内置只读 | 含 `candidate_name`/`position`/`salary`/`company` 变量 |
| 拒绝通知 | reject | 内置只读 | 含 `candidate_name`/`position`/`company` 变量 |
| 进度通知 | progress | 内置只读 | 含 `candidate_name`/`status`/`company` 变量 |
| 自定义模板 | custom | 可增删改 | admin 可在邮件中心新建/编辑/删除 |

- **预置模板初始化**：后端 `lifespan` 启动时调用 `seed_builtin_templates` 自动插入 4 个预置模板（已存在则跳过）
- **Jinja2 沙箱渲染**：`SandboxedEnvironment` + `autoescape=True` + `StrictUndefined`，仅允许 `{{ var }}` 变量替换，禁用 `{% %}` 控制结构，防止模板注入
- **变量提取**：前端通过正则 `\{\{\s*(\w+)\s*\}\}` 自动从模板正文提取变量名，生成变量填写表单

### SMTP 配置

| 配置项 | 说明 |
|--------|------|
| `smtp_host` | SMTP 服务器地址（如 `smtp.qq.com`） |
| `smtp_port` | 端口（SSL/TLS 通常 465，STARTTLS 通常 587） |
| `smtp_user` | **发件人邮箱账号**（即发件人地址） |
| `smtp_password` | 密码或授权码（QQ/163/Gmail 需用授权码） |
| `use_ssl` | 加密方式：`true`=SSL/TLS（465），`false`=STARTTLS（587） |

- **密码加密存储**：SMTP 密码使用 base64 加密后存入 MongoDB `email_config` 集合
- **密码留空不覆盖**：设置页保存配置时密码留空表示不修改原密码（支持仅改主机/端口场景）
- **测试邮件**：设置页提供"发送测试邮件"功能，admin 可向指定邮箱发送一封测试邮件验证 SMTP 配置
- **错误反馈**：前端发送邮件后检查 `data.status` 字段，SMTP 失败时显示具体错误信息（如 `535 Authentication required`）

### 邮件发送流程

```
前端发送请求（template_id 或 custom_subject+custom_body 二选一）
    ↓
后端 EmailService.send_mail
    ↓
├─ 模板模式：EmailTemplateService.render_template(template_id, variables)
│   └─ Jinja2 沙箱渲染 subject + body
├─ 自定义模式：直接使用 custom_subject + custom_body
    ↓
_get_smtp_config → 读取并解密 SMTP 配置
    ↓
aiosmtplib.send（异步发送，use_tls=use_ssl）
    ↓
返回 {status: "success"|"error", message: "..."}
    ↓
前端检查 status，error 时 ElMessage.error 显示错误
```

### 邮件中心页（`/email`）

- **Tab 1 发送邮件**：模板模式（含变量填写+主题/正文预览）/ 自定义模式二选一
- **Tab 2 模板管理（admin only）**：列表/新建/编辑/删除，预置模板标记"内置"标签且不可改删
- **简历详情发邮件入口**：操作区"发送邮件"按钮打开 `SendEmailDialog`，预填 `candidate_name`/`position`/`company`/`salary`/`interview_time` 变量

## 架构设计

### 全栈架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 (frontend/)                          │
│   Vue3 + TS + Element Plus + Pinia + Vue Router              │
│   Axios 拦截器剥离 {code,message,data} · SSE 流式对话         │
├─────────────────────────────────────────────────────────────┤
│                    HTTP / SSE                                │
├─────────────────────────────────────────────────────────────┤
│                    后端 (backend/)                           │
│   FastAPI · 三层架构 api → services → core                   │
│   LangGraph Agent · 统一响应 {code,message,data,trace_id}    │
├─────────────────────────────────────────────────────────────┤
│   MongoDB   │   Redis   │   Milvus   │   MinIO   │   LLM    │
└─────────────────────────────────────────────────────────────┘
```

### 后端三层架构

```
┌─────────────────────────────────────────────────────────┐
│                    API 层 (app/api)                     │
│   路由定义 · 请求校验 · 依赖注入 · 统一响应              │
├─────────────────────────────────────────────────────────┤
│                  Services 层 (app/services)             │
│   业务逻辑编排 · LLM/检索/DB 调用 · 异常处理            │
├─────────────────────────────────────────────────────────┤
│                    Core 层 (app/core)                   │
│   数据库 · 缓存 · LLM · Embedding · 向量库 · 配置       │
└─────────────────────────────────────────────────────────┘
```

### 前端架构

```
┌─────────────────────────────────────────────────────────┐
│                    Views (views/)                        │
│   Login/Layout/Workbench/ResumeList/ResumeDetail/        │
│   Dashboard/JdMatch/Settings                            │
├─────────────────────────────────────────────────────────┤
│              Components (components/)                    │
│   common · resume · chat · candidate · dashboard         │
├─────────────────────────────────────────────────────────┤
│   Stores (Pinia)  │  API (axios+sse)  │  Router          │
│   auth/chat/      │  request 拦截器    │  登录守卫        │
│   resume/app      │  sse 流式封装      │                 │
├─────────────────────────────────────────────────────────┤
│              Design System (styles/)                    │
│   Editorial Tech · 深墨绿+琥珀金 · Fraunces+Manrope      │
└─────────────────────────────────────────────────────────┘
```

### Agent 工作流（app/agent）

```
用户输入 → 意图识别节点（5 类：chitchat/search/detail/compare/qa）
                ↓
        ┌───────┼───────┬───────────┐
        ↓       ↓       ↓           ↓
    chitchat  search  detail/    qa
              compare  compare
        ↓       ↓       ↓           ↓
    CHITCHAT  检索+精排  复用历史   复用历史
    PROMPT    +同义词扩展 candidates candidates
        ↓       ↓       ↓           ↓
        └───────┴───────┴───────────┘
                    ↓
            LLM 流式回答（SSE token 推送）
            search → SEARCH_RESPOND_PROMPT
            compare → COMPARE_PROMPT（5维度对比+评分解释）
            detail → DETAIL_PROMPT
            qa → QA_PROMPT（注入候选人数据作上下文）
                    ↓
            保存消息 + 首条消息更新会话标题
                    ↓
            done 事件（携带 title）
```

### 对话上下文感知机制

```
第1轮: "帮我找NLP工程师"
  → intent=search → 触发检索 → 返回候选人列表A
  → 候选人列表A保存到会话历史

第2轮: "对比李志鹏和温佳蕊"
  → intent=compare → 从历史提取候选人列表A
  → 姓名精确匹配（两轮算法+歧义消除）
  → 仅对比匹配到的候选人，不触发新检索
  → COMPARE_PROMPT 生成结构化对比

第3轮: "为什么李志鹏评分比温佳蕊高"
  → intent=qa → 从历史提取候选人列表A
  → 候选人评分数据注入 system prompt
  → LLM 基于实际评分维度解释差异，不触发新检索
```

### 数据流

```
简历上传 → MinIO 存储 → OCR/解析 → PII 脱敏 → MongoDB 元数据
                                    ↓
                              切片 + BGE-M3 编码 → Milvus 向量库
                                    ↓
检索请求 → 查询改写 → BGE-M3 编码 → Milvus Hybrid 检索
                                    ↓
                            BGE-Reranker 精排 → 返回候选人列表
```

## 性能优化

系统在启动速度、请求延迟、前端加载三个维度做了针对性优化，确保只有少量数据时也能秒级响应。

### 后端启动优化

| 优化项 | 说明 | 效果 |
|--------|------|------|
| 模型异步预热 | BGE-M3 / Reranker / OCR / MinIO 放入 `asyncio.to_thread` 后台线程池加载 | 应用启动从几十秒 → **秒级就绪**，模型在后台继续加载不阻塞 |
| Redis 连接预热 | 启动时执行 `PING` 命令强制建立 TCP 连接 | `/auth/me` 首次请求从 **2039ms → 4ms** |
| MongoDB 索引 | `resumes` 集合对 `user_id`/`parse_status`/`created_at`/`education_level+work_years` 建索引 | 简历列表查询稳定在 **5-15ms** |
| 请求计时中间件 | `trace_middleware` 记录每个请求耗时，>200ms 输出慢请求日志 | 响应头携带 `X-Response-Time`，便于排查 |

### 前端加载优化

| 优化项 | 说明 | 效果 |
|--------|------|------|
| Vite 依赖预构建 | `optimizeDeps.include` 预构建 vue/vue-router/pinia/element-plus | 首屏加载减少重复编译 |
| 关键文件预热 | `server.warmup.clientFiles` 预热 ResumeList/ResumeCard 等关键组件 | 点击简历库时组件已编译就绪 |
| 代码分割 | `manualChunks` 将 element-plus / vue-vendor 拆为独立 chunk | 缓存命中率提升，迭代发布时不失效 vendor 缓存 |
| 路由悬停预加载 | 菜单 `@mouseenter` 时调用 `router.resolve` 预加载组件 | 点击即开，无编译延迟 |
| 页面切换无白屏 | 去掉 transition `mode="out-in"`，缩短动画至 0.2s | 新旧页面并行过渡，消除白屏等待 |

### 检索评分并发化

候选人推荐流程中，多个候选人的 LLM 评分从串行改为 `asyncio.gather` 并发执行：

```python
# 优化前：串行，总耗时 = N × 单次耗时
for doc in docs:
    score_data = await self._llm_score_multi(query, doc, rerank_score)

# 优化后：并发，总耗时 ≈ 单次耗时
results = await asyncio.gather(*[_score_one(doc) for doc in docs])
```

## 目录结构

```
HR/
├── docker-compose.yml                # Docker 一键部署编排文件
├── .env.example                      # Docker 环境变量模板
├── .gitignore                        # Git 忽略规则
├── backend/                          # 后端代码
│   ├── Dockerfile                    # 后端 Docker 镜像构建
│   ├── .dockerignore                 # Docker 构建忽略
│   ├── app/
│   │   ├── main.py                   # FastAPI 入口，路由挂载与生命周期（含 admin 自动初始化）
│   │   ├── api/                      # API 路由层（10 个路由模块）
│   │   │   ├── auth.py               # 认证（含 register / change_password）
│   │   │   ├── resumes.py            # 简历管理（删除 admin only）
│   │   │   ├── search.py             # 检索
│   │   │   ├── chat.py               # 对话
│   │   │   ├── candidates.py         # 候选人
│   │   │   ├── email.py              # 邮件（SMTP 配置 admin only）
│   │   │   ├── jd_match.py           # JD 匹配
│   │   │   ├── interview.py          # 面试
│   │   │   ├── dashboard.py          # 看板
│   │   │   ├── users.py              # 用户管理（admin only）
│   │   │   ├── monitor.py            # 前端监控上报（错误/性能）
│   │   │   └── deps.py               # 公共依赖（get_current_user / require_admin）
│   │   ├── services/                 # 业务逻辑层（14 个 service，含 email_template_service）
│   │   ├── core/                     # 基础设施层（metrics/health/logger/config/database 等）
│   │   │   ├── logger.py             # loguru 结构化日志（DEBUG彩色/生产JSON）
│   │   │   ├── metrics.py            # Prometheus 指标（QPS/延迟/业务指标）+ 中间件
│   │   │   ├── health.py             # 深度健康检查（Mongo/Redis/MinIO/Milvus）
│   │   │   └── ...
│   │   ├── models/                   # Pydantic 数据模型（含 user.py RBAC 模型）
│   │   ├── agent/                    # LangGraph Agent
│   │   └── utils/                    # 工具函数
│   ├── tests/                        # 测试代码（307 个测试）
│   │   ├── api/                      # API 层测试
│   │   ├── services/                 # Service 层测试
│   │   ├── core/                     # Core 层测试
│   │   ├── agent/                    # Agent 测试
│   │   ├── utils/                    # 工具函数测试
│   │   ├── e2e/                      # 端到端集成测试（32 步招聘闭环）
│   │   └── test_integration.py       # 集成测试
│   ├── .env.example                  # 环境变量模板
│   ├── pyproject.toml                # 项目元信息
│   ├── pytest.ini                    # pytest 配置
│   └── requirements.txt              # 依赖清单（锁定版本）
├── frontend/                         # 前端代码
│   ├── Dockerfile                    # 前端 Docker 镜像构建（多阶段）
│   ├── nginx.conf                    # Nginx 配置（SPA路由+API代理+Gzip）
│   ├── .dockerignore                 # Docker 构建忽略
│   ├── src/
│   │   ├── main.ts                   # 应用入口
│   │   ├── App.vue                   # 根组件
│   │   ├── api/                      # API 调用层
│   │   │   ├── request.ts            # Axios 实例 + 拦截器
│   │   │   ├── sse.ts                # SSE 流式请求封装
│   │   │   └── [9 个业务模块].ts     # auth/resume/chat/...
│   │   ├── stores/                   # Pinia 状态管理
│   │   │   ├── auth.ts               # 登录态/Token
│   │   │   ├── chat.ts               # 会话/消息流
│   │   │   ├── resume.ts             # 简历列表/筛选
│   │   │   └── app.ts                # 全局 UI 状态
│   │   ├── types/                    # TypeScript 类型定义
│   │   ├── utils/                    # 工具函数
│   │   │   └── monitor.ts            # 前端错误监控（JS/Promise/资源错误上报+Web Vitals）
│   │   ├── router/                   # Vue Router + 登录守卫
│   │   ├── views/                    # 页面（10 个）
│   │   │   ├── Login.vue             # 登录页（邮箱+密码登录，含申请账号入口）
│   │   │   ├── Layout.vue            # 主布局（admin 菜单按角色显隐）
│   │   │   ├── Workbench.vue         # 工作台（对话+推荐）
│   │   │   ├── ResumeList.vue        # 简历列表
│   │   │   ├── ResumeDetail.vue      # 简历详情（含发邮件入口）
│   │   │   ├── Dashboard.vue         # 数据看板
│   │   │   ├── JdMatch.vue           # JD 匹配
│   │   │   ├── EmailCenter.vue       # 邮件中心（发送+模板管理）
│   │   │   ├── Settings.vue          # 设置（SMTP 配置+测试邮件，admin only）
│   │   │   └── UserList.vue          # 用户管理（admin only）
│   │   ├── components/               # 业务组件（15 个）
│   │   │   ├── common/               # EmptyState / LoadingOverlay
│   │   │   ├── resume/               # ResumeCard / FilterBar / UploadDialog / ResumePreview
│   │   │   ├── chat/                 # ChatPanel / MessageBubble / SessionList / StreamIndicator
│   │   │   ├── candidate/            # CandidateCard / CandidateCompare / TagInput
│   │   │   ├── email/                # SendEmailDialog
│   │   │   └── dashboard/            # ChartWidget
│   │   ├── utils/                    # 工具函数
│   │   └── styles/variables.scss     # 设计系统（Editorial Tech）
│   ├── tests/                        # 前端测试（133 个）
│   ├── .env.development              # 前端环境变量
│   ├── vite.config.ts                # Vite 配置（含 /api 代理）
│   ├── vitest.config.ts              # Vitest 配置
│   └── package.json                  # 依赖清单
└── docs/                             # 设计文档
    ├── Business-Requirements.md      # 业务需求
    ├── MVP-Design.md                 # MVP 设计
    ├── API-Design.md                 # API 设计
    ├── Backend-Design.md             # 后端设计
    ├── Frontend-Design.md            # 前端设计
    ├── Environment-Setup.md          # 环境搭建
    ├── specs/                        # 设计规范
    │   └── 2026-06-27-auth-rbac-design.md  # Auth + RBAC 设计
    └── plans/                        # 开发计划
        ├── 2026-06-26-backend-development-plan.md
        ├── 2026-06-26-frontend-development-plan.md
        └── 2026-06-27-auth-rbac.md   # Auth + RBAC 实施计划
```

## 快速开始

### 环境要求

**Docker 部署（推荐）：**
- Docker >= 20.10
- Docker Compose >= 2.0

**本地开发：**
- **Python >= 3.11**（推荐 3.12）+ **uv** 包管理器
- **Node.js >= 18** + **npm**
- **MongoDB 6.0+** / **Redis 6.0+** / **Milvus 2.4+** / **MinIO**

### 1. 克隆项目

```bash
git clone <repo-url>
cd HR
```

### 2. Docker 一键部署（推荐）

仅需安装 **Docker** 和 **Docker Compose**，无需手动配置 MongoDB/Redis/Milvus/MinIO 等基础设施。

```bash
# 1. 复制环境配置模板
cp .env.example .env

# 2. 编辑 .env，必填项：
#    - LLM_API_KEY：你的通义千问/OpenAI 兼容接口 API Key
#    - JWT_SECRET：改为随机字符串（生产环境）
#    - ADMIN_PASSWORD：管理员密码（可选）

# 3. 构建并启动所有服务（首次启动会自动下载模型，需几分钟）
docker-compose up -d --build

# 4. 查看启动进度
docker-compose logs -f backend
```

启动成功后访问：
- **前端入口**：http://localhost（Nginx 托管）
- **后端 API**：http://localhost:8000/api/v1
- **Swagger 文档**：http://localhost:8000/docs
- **MinIO 控制台**：http://localhost:9001（账号：minioadmin / minioadmin）

**服务说明：**

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend (Nginx) | 80 | 前端静态资源 + API 反向代理 |
| backend (FastAPI) | 8000 | 后端 API 服务 |
| MongoDB | 27017 | 主数据库 |
| Redis | 6379 | 缓存 / Token 黑名单 |
| MinIO | 9000/9001 | 对象存储（简历文件 + Milvus 数据） |
| Milvus | 19530 | 向量数据库 |
| etcd | — | Milvus 元数据（内部使用） |

**常用命令：**

```bash
docker-compose ps                    # 查看服务状态
docker-compose logs -f backend       # 查看后端日志
docker-compose restart backend       # 重启后端
docker-compose down                  # 停止所有服务（数据保留在 volume 中）
docker-compose down -v               # 停止并删除所有数据（慎用）
```

> 首次启动时 BGE-M3 和 BGE-Reranker 模型会自动下载到 Docker volume `model_data` 中（约 4-5GB），后续启动无需重新下载。如需挂载本地模型，可在 `docker-compose.yml` 的 backend service 添加：`- /your/local/models:/app/models`。

### 3. 本地开发启动

如需本地开发（不使用 Docker），按以下步骤启动：

#### 3.1 后端启动

```bash
cd backend
uv venv .venv --python 3.12
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
uv pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY、数据库连接等

# 下载 BGE-M3 与 BGE-Reranker 模型到 backend/models/

# 启动开发服务器
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后访问：
- API 入口：http://localhost:8000/api/v1
- 健康检查：http://localhost:8000/health
- Swagger 文档：http://localhost:8000/docs

#### 3.2 前端启动

```bash
cd frontend
npm install

# 启动开发服务器（已配置 /api 代理到后端 8000 端口）
npm run dev
```

前端启动后访问：http://localhost:5173/

#### 3.3 前后端对接启动（推荐开发方式）

**终端 1 - 启动后端：**

```bash
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**终端 2 - 启动前端：**

```bash
cd frontend
npm run dev
```

前端 `vite.config.ts` 已配置代理：`/api` → `http://localhost:8000`，浏览器访问 http://localhost:5173/ 即可使用完整功能，无需处理跨域。

### 4. 默认登录账号

后端启动时自动初始化管理员账号（凭据走 `.env`，可自定义）：
- **邮箱**：`a****@********`（由 `.env` 的 `ADMIN_EMAIL` 配置）
- 密码：`admin123`
- 角色：`admin`

登录使用**邮箱 + 密码**方式。其他用户需通过登录页"申请账号"入口提交注册申请（email/name 必填），由管理员审批后方可登录；管理员也可在「用户管理」页直接开号。

### 5. 运行测试

```bash
# 后端全量测试（307 个）
cd backend
.venv\Scripts\python.exe -m pytest

# 后端 E2E 测试（32 步招聘闭环）
.venv\Scripts\python.exe -m pytest tests/e2e/ -v

# 前端全量测试（133 个）
cd frontend
npm test
```

## 配置说明

### 后端配置

所有配置通过 `.env` 文件管理，禁止硬编码。完整配置项见 [`backend/.env.example`](backend/.env.example)：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `APP_NAME` | 应用名称 | TalentSense HR |
| `API_V1_PREFIX` | API 前缀 | /api/v1 |
| `MONGO_URI` | MongoDB 连接串 | mongodb://localhost:27017 |
| `MONGO_DB` | MongoDB 库名 | talentsense |
| `REDIS_URL` | Redis 连接串 | redis://localhost:6379/0 |
| `MILVUS_HOST` / `MILVUS_PORT` | Milvus 地址 | localhost:19530 |
| `MINIO_ENDPOINT` | MinIO 地址 | localhost:9000 |
| `LLM_API_KEY` | LLM API Key | （必填） |
| `LLM_BASE_URL` | LLM 接口地址 | 通义千问兼容模式 |
| `LLM_MODEL` | LLM 模型名 | qwen-plus |
| `JWT_SECRET` | JWT 签名密钥 | （生产必改） |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效期 | 60 |
| `BGE_M3_PATH` | BGE-M3 模型路径 | ./models/bge-m3 |
| `BGE_RERANKER_PATH` | BGE-Reranker 模型路径 | ./models/bge-reranker-v2-m3 |
| `HYBRID_DENSE_WEIGHT` | 稠密向量权重 | 1.0 |
| `HYBRID_SPARSE_WEIGHT` | 稀疏向量权重 | 0.7 |
| `RETRIEVE_TOP_K` | 初筛召回数 | 20 |
| `RERANK_TOP_K` | 精排返回数 | 10 |
| `ADMIN_USERNAME` | 自动初始化管理员用户名 | admin |
| `ADMIN_PASSWORD` | 自动初始化管理员密码 | admin123 |
| `ADMIN_EMAIL` | 自动初始化管理员邮箱（登录用） | admin@talentsense.com |

### 前端配置

前端配置通过 `.env.development` / `.env.production` 管理：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `VITE_API_BASE` | API 基础路径 | /api/v1 |
| `VITE_APP_TITLE` | 应用标题 | TalentSense HR |

## API 接口

所有接口统一前缀 `/api/v1`，统一响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "trace_id": "uuid"
}
```

### 路由模块总览

| 模块 | 前缀 | 主要接口 | 权限 |
|------|------|---------|------|
| 认证 | `/api/v1/auth` | POST `/login`（邮箱+密码） · POST `/refresh` · GET `/me` · POST `/logout` · POST `/register` · PUT `/password` | 公开 / 登录 |
| 简历 | `/api/v1/resumes` | POST `` (上传) · GET `` (列表) · GET `/{resume_id}` · PATCH `/{resume_id}` · DELETE `/{resume_id}` · GET `/{resume_id}/preview` | 登录 / 删除 admin |
| 检索 | `/api/v1/search` | POST `` (自然语言检索) | 登录 |
| 对话 | `/api/v1/chat` | POST `/sessions` · POST `/sessions/{session_id}/messages` (SSE) · GET `/sessions` · DELETE `/sessions/{session_id}` | 登录 |
| 候选人 | `/api/v1/candidates` | POST `/compare` · GET `/{resume_id}/similar` · POST `/export` | 登录 |
| 邮件 | `/api/v1/email` | POST `/send` · POST `/send-test` · GET `/config` · PUT `/config` · GET `/templates` · POST `/templates` · PUT `/templates/{id}` · DELETE `/templates/{id}` | 登录 / 配置+模板管理 admin |
| JD 匹配 | `/api/v1/jd` | POST `` (JD 匹配) | 登录 |
| 面试 | `/api/v1/interview` | POST `/questions` · POST `/notes` · GET `/notes/{resume_id}` | 登录 |
| 看板 | `/api/v1/dashboard` | GET `/stats` | 登录 |
| 用户管理 | `/api/v1/users` | GET `` · POST `` · GET `/{id}` · PUT `/{id}/approve` · PUT `/{id}/reject` · PUT `/{id}/status` · PUT `/{id}/password` · DELETE `/{id}` | admin |

完整接口字段与示例见 [`docs/API-Design.md`](docs/API-Design.md) 与 Swagger 文档。

### 前端 API 层设计

- **Axios 拦截器**：请求拦截注入 `Authorization: Bearer <token>`；响应拦截剥离 `{code, message, data}` 外层，业务代码只处理 `data`
- **Token 失效处理**：响应 `code === 1002` 时自动清空 token 并跳转登录页
- **SSE 流式**：用 `fetch + ReadableStream` 实现，支持 POST 请求与 8 种事件分发（intent/rewrite/retrieval/rank/token/candidates/done/error）

## 测试

### 测试规模

| 类型 | 数量 | 说明 |
|------|------|------|
| 后端单元/集成测试 | 275 | 覆盖 API / Services / Core / Agent / Utils 各层（含 users / RBAC / email_template / qa 意图 / 4 维度评分 / 同义词扩展 / 技能硬过滤 / 对比复用 / 姓名匹配 / 看板扩展） |
| 后端 E2E 测试 | 32 | 端到端招聘闭环业务流程（含邮箱登录/模板发送） |
| 前端单元/组件测试 | 133 | 覆盖 API / Stores / Router / Components / Views（含 4 维度评分卡 / 会话标题同步） |
| **合计** | **440** | **全部通过** |

### 后端 E2E 测试覆盖（32 步招聘闭环）

| 步骤 | 测试 | 覆盖功能 |
|------|------|---------|
| 01-03, 31 | 登录认证 | 正确/错误密码、获取当前用户、未授权访问 |
| 04-12, 27-29 | 简历管理 | 列表/上传/详情/404/标签/收藏/备注/过滤/预览/删除 |
| 13 | 候选人检索 | 自然语言语义检索 |
| 14-16, 30 | 对话会话 | 创建/SSE 流式/列表/删除 |
| 17 | JD 匹配 | LLM 解析 JD + 检索 + 匹配理由 |
| 18-20 | 面试管理 | 生成问题/保存评价/查询评价 |
| 21-22 | 候选人对比 | 横向对比/相似推荐 |
| 23-25 | 导出与邮件 | Excel 导出/邮件发送/配置查询 |
| 26 | 看板统计 | 招聘漏斗/入库趋势/技能/学历/薪资/经验/面试结果 |
| 32 | 协议校验 | 统一响应格式 |

### 后端 E2E 技术实现

- **FakeMongoDB / FakeRedis**：自建内存数据库，支持 `$set`/`$push`/`$each`/`$slice`/`$in`/`$gte`/`$lte`/`$regex`/`$or`/`$and` 等操作符，使数据在 9 个 API 路由间真实流转
- **ExitStack 管理 24 个 patch**：规避 Python 静态嵌套块限制
- **直接修改类属性**：解决 service 模块已绑定原类引用的 patch 失效问题

### 前端测试覆盖

- **API 层**：request 拦截器剥离、SSE 解析分发
- **Stores**：auth 登录态、chat 消息流、resume 列表筛选
- **Router**：登录守卫、未登录跳转
- **Components**：14 个组件渲染与事件测试
- **Views**：8 个页面视图挂载测试

## 开发规范

### 工程约定

- **后端包管理**：统一使用 uv，启动用 `.venv\Scripts\python.exe`
- **前端包管理**：使用 npm，锁定 `package.json` + `package-lock.json`
- **依赖锁定**：`requirements.txt` / `package.json` 锁定全部版本
- **配置分离**：禁止硬编码敏感信息，统一走 `.env`（后端）/ `.env.development`（前端）
- **统一响应格式**：`{code, message, data, trace_id}`
- **API 前缀**：所有路由遵循 `/api/v1/[module]` 约定
- **三层架构**：后端 api → services → core，模块职责单一
- **前端架构**：views → components → stores/api，单向数据流

### 代码规范

- 每个文件开头必须写元信息（文件名/创建时间/作者/功能描述）
- 每个函数和类必须写文档注释，标明入参、出参及核心逻辑
- 核心逻辑和对外接口必须有异常捕获与兜底返回
- 关键步骤、运行状态、报错信息必须写入日志
- 前端严格 TypeScript，禁止 `any`（除 ECharts option）

### 测试规范

- 每个模块必须附带单元测试
- 提交前必须全量测试通过
- 后端 motor collection 的 `find()`/`aggregate()` 同步返回 cursor，测试中用 `MagicMock()` 而非 `AsyncMock()`
- 前端测试用 `@vue/test-utils` + `vitest` + `msw` mock API

### Git 提交规范

```
feat: 完成XX模块
fix: 修复XX问题
test: 新增XX测试
docs: 更新XX文档
refactor: 重构XX逻辑
```

## 文档

- [业务需求](docs/Business-Requirements.md)
- [MVP 设计](docs/MVP-Design.md)
- [API 设计](docs/API-Design.md)
- [后端设计](docs/Backend-Design.md)
- [前端设计](docs/Frontend-Design.md)
- [环境搭建](docs/Environment-Setup.md)
- [Auth + RBAC 设计](docs/specs/2026-06-27-auth-rbac-design.md)
- [Auth + RBAC 实施计划](docs/plans/2026-06-27-auth-rbac.md)
- [邮箱登录 + 邮件模板实施计划](docs/plans/2026-06-27-email-login-and-templates.md)
- [简历筛选与脱敏优化设计](docs/specs/2026-06-27-resume-filters-and-unmask-design.md)
- [简历筛选与脱敏优化计划](docs/plans/2026-06-27-resume-filters-and-unmask.md)
- [工作台推荐与意图优化设计](docs/specs/2026-06-27-workbench-recommend-and-intent-design.md)
- [工作台推荐与意图优化计划](docs/plans/2026-06-27-workbench-recommend-and-intent.md)
- [UX 优化计划](docs/plans/2026-06-27-ux-optimization.md)
- [后端开发计划](docs/plans/2026-06-26-backend-development-plan.md)
- [前端开发计划](docs/plans/2026-06-26-frontend-development-plan.md)

---

## License

Private © TalentSense Team
