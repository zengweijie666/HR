# TalentSense HR

> 基于 AI 的智能简历推荐与招聘辅助系统（全栈）

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4-42b883.svg)](https://vuejs.org/)
[![Tests](https://img.shields.io/badge/tests-290%20passed-brightgreen.svg)](#测试)
[![Version](https://img.shields.io/badge/version-2.5.0-orange.svg)](#)

---

## 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [架构设计](#架构设计)
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
| 认证管理 | 用户登录、Token 刷新、当前用户、登出 | F01-F02 |
| 简历管理 | 上传解析、列表查询、详情查看、标签/收藏/备注、过滤、预览、删除 | F03-F10 |
| 候选人检索 | 自然语言语义检索、Hybrid 检索 + Reranker 精排 | F11 |
| 智能对话 | 多轮对话会话、SSE 流式响应、对话历史 | F12-F13 |
| JD 匹配 | LLM 解析 JD、检索 + 精排、匹配理由生成 | F14 |
| 面试辅助 | AI 生成面试题、保存面试评价、查询评价 | F15-F16 |
| 候选人对比 | 多候选人横向对比、相似推荐 | F17-F18 |
| 邮件通知 | 候选人邮件发送、SMTP 配置查询 | F19 |
| 数据看板 | 候选人统计、技能分布、学历分布、薪资分布 | F20 |
| 数据导出 | 候选人列表 Excel 导出 | F21 |
| 404 处理 | 统一 404 响应 | F22 |

### 技术亮点

- **Hybrid 检索**：BGE-M3 同时输出稠密 + 稀疏向量，加权融合提升召回
- **Reranker 精排**：BGE-Reranker-v2-m3 对初筛结果二次排序
- **LangGraph Agent**：意图识别 → 工具选择 → 执行 → 回答的工作流编排
- **PII 脱敏**：手机号/邮箱/身份证入库前自动脱敏与哈希
- **简历去重**：基于手机号 + 邮箱哈希的多维度查重
- **统一响应格式**：`{code, message, data, trace_id}` 全链路追踪
- **SSE 流式**：对话接口使用 Server-Sent Events 实时推送 token
- **Editorial Tech 设计**：深墨绿 + 琥珀金配色，Fraunces 衬线标题，grain 纹理质感

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
用户输入 → 意图识别节点 → 工具选择节点 → 工具执行节点 → 回答生成节点
                ↓               ↓               ↓
            search          resume_detail    list_resumes
                              chat           ...
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

## 目录结构

```
HR/
├── backend/                          # 后端代码
│   ├── app/
│   │   ├── main.py                   # FastAPI 入口，路由挂载与生命周期
│   │   ├── api/                      # API 路由层（9 个路由模块）
│   │   │   ├── auth.py               # 认证
│   │   │   ├── resumes.py            # 简历管理
│   │   │   ├── search.py             # 检索
│   │   │   ├── chat.py               # 对话
│   │   │   ├── candidates.py         # 候选人
│   │   │   ├── email.py              # 邮件
│   │   │   ├── jd_match.py           # JD 匹配
│   │   │   ├── interview.py          # 面试
│   │   │   ├── dashboard.py          # 看板
│   │   │   └── deps.py               # 公共依赖（鉴权等）
│   │   ├── services/                 # 业务逻辑层（12 个 service）
│   │   ├── core/                     # 基础设施层
│   │   ├── agent/                    # LangGraph Agent
│   │   └── utils/                    # 工具函数
│   ├── tests/                        # 测试代码（184 个测试）
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
│   │   ├── router/                   # Vue Router + 登录守卫
│   │   ├── views/                    # 页面（8 个）
│   │   │   ├── Login.vue             # 登录页（杂志封面级）
│   │   │   ├── Layout.vue            # 主布局
│   │   │   ├── Workbench.vue         # 工作台（对话+推荐）
│   │   │   ├── ResumeList.vue        # 简历列表
│   │   │   ├── ResumeDetail.vue      # 简历详情
│   │   │   ├── Dashboard.vue       # 数据看板
│   │   │   ├── JdMatch.vue           # JD 匹配
│   │   │   └── Settings.vue          # 设置
│   │   ├── components/               # 业务组件（14 个）
│   │   │   ├── common/               # EmptyState / LoadingOverlay
│   │   │   ├── resume/               # ResumeCard / FilterBar / UploadDialog / ResumePreview
│   │   │   ├── chat/                 # ChatPanel / MessageBubble / SessionList / StreamIndicator
│   │   │   ├── candidate/            # CandidateCard / CandidateCompare / TagInput
│   │   │   └── dashboard/            # ChartWidget
│   │   ├── utils/                    # 工具函数
│   │   └── styles/variables.scss     # 设计系统（Editorial Tech）
│   ├── tests/                        # 前端测试（106 个）
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
    └── plans/                        # 开发计划
        ├── 2026-06-26-backend-development-plan.md
        └── 2026-06-26-frontend-development-plan.md
```

## 快速开始

### 环境要求

- **Python >= 3.11**（推荐 3.12）+ **uv** 包管理器
- **Node.js >= 18** + **npm**
- **MongoDB 6.0+** / **Redis 6.0+** / **Milvus 2.4+** / **MinIO**

### 1. 克隆项目

```bash
git clone <repo-url>
cd HR
```

### 2. 后端启动

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

### 3. 前端启动

```bash
cd frontend
npm install

# 启动开发服务器（已配置 /api 代理到后端 8000 端口）
npm run dev
```

前端启动后访问：http://localhost:5173/

### 4. 前后端对接启动（推荐）

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

### 5. 默认登录账号

预置 HR 用户（需在后端 `.env` 中配置或通过初始化脚本创建）：
- 用户名：`admin`
- 密码：`admin123`

### 6. 运行测试

```bash
# 后端全量测试（184 个）
cd backend
.venv\Scripts\python.exe -m pytest

# 后端 E2E 测试（32 步招聘闭环）
.venv\Scripts\python.exe -m pytest tests/e2e/ -v

# 前端全量测试（106 个）
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

| 模块 | 前缀 | 主要接口 |
|------|------|---------|
| 认证 | `/api/v1/auth` | POST `/login` · POST `/refresh` · GET `/me` · POST `/logout` |
| 简历 | `/api/v1/resumes` | POST `` (上传) · GET `` (列表) · GET `/{resume_id}` · PATCH `/{resume_id}` · DELETE `/{resume_id}` · GET `/{resume_id}/preview` |
| 检索 | `/api/v1/search` | POST `` (自然语言检索) |
| 对话 | `/api/v1/chat` | POST `/sessions` · POST `/sessions/{session_id}/messages` (SSE) · GET `/sessions` · DELETE `/sessions/{session_id}` |
| 候选人 | `/api/v1/candidates` | POST `/compare` · GET `/{resume_id}/similar` · POST `/export` |
| 邮件 | `/api/v1/email` | POST `/send` · GET `/config` · PUT `/config` |
| JD 匹配 | `/api/v1/jd` | POST `` (JD 匹配) |
| 面试 | `/api/v1/interview` | POST `/questions` · POST `/notes` · GET `/notes/{resume_id}` |
| 看板 | `/api/v1/dashboard` | GET `/stats` |

完整接口字段与示例见 [`docs/API-Design.md`](docs/API-Design.md) 与 Swagger 文档。

### 前端 API 层设计

- **Axios 拦截器**：请求拦截注入 `Authorization: Bearer <token>`；响应拦截剥离 `{code, message, data}` 外层，业务代码只处理 `data`
- **Token 失效处理**：响应 `code === 1002` 时自动清空 token 并跳转登录页
- **SSE 流式**：用 `fetch + ReadableStream` 实现，支持 POST 请求与 8 种事件分发（intent/rewrite/retrieval/rank/token/candidates/done/error）

## 测试

### 测试规模

| 类型 | 数量 | 说明 |
|------|------|------|
| 后端单元/集成测试 | 152 | 覆盖 API / Services / Core / Agent / Utils 各层 |
| 后端 E2E 测试 | 32 | 端到端招聘闭环业务流程 |
| 前端单元/组件测试 | 106 | 覆盖 API / Stores / Router / Components / Views |
| **合计** | **290** | **全部通过** |

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
| 26 | 看板统计 | 候选人/技能/学历/薪资分布 |
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
- [后端开发计划](docs/plans/2026-06-26-backend-development-plan.md)
- [前端开发计划](docs/plans/2026-06-26-frontend-development-plan.md)

---

## License

Private © TalentSense Team
