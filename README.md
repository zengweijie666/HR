# TalentSense HR

> 基于 AI 的智能简历推荐与招聘辅助系统后端

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-184%20passed-brightgreen.svg)](#测试)
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

TalentSense HR 是一套面向 HR 的智能招聘辅助系统后端，依托大语言模型（LLM）、向量检索、Reranker 精排与 Agent 工作流，实现从简历入库、智能解析、语义检索、JD 匹配、对话式推荐到面试辅助的全链路数字化招聘闭环。

系统以「简历推荐」为核心，融合 Hybrid 向量检索（BGE-M3 稠密+稀疏）与 BGE-Reranker 精排，并通过 LangGraph Agent 实现自然语言对话式交互，帮助 HR 从海量简历中高效定位合适候选人。

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

## 技术栈

### 后端核心
- **Python 3.12** + **uv** 包管理
- **FastAPI 0.115** Web 框架
- **Pydantic 2.9** 数据校验
- **uvicorn** ASGI 服务器

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

### 工具链
- **pytest + pytest-asyncio** — 测试框架
- **loguru** — 结构化日志
- **python-jose + passlib** — JWT 认证
- **aiosmtplib** — 异步邮件发送
- **openpyxl** — Excel 导出

## 架构设计

### 三层架构

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
│   │   │   ├── auth_service.py
│   │   │   ├── resume_service.py
│   │   │   ├── search_service.py
│   │   │   ├── agent_service.py      # 对话 Agent 编排
│   │   │   ├── candidate_service.py  # 对比/相似推荐
│   │   │   ├── jd_match_service.py
│   │   │   ├── interview_service.py
│   │   │   ├── email_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── export_service.py     # Excel 导出
│   │   │   └── tag_service.py        # 标签/收藏/备注
│   │   ├── core/                     # 基础设施层
│   │   │   ├── config.py             # 配置（pydantic-settings）
│   │   │   ├── database.py           # MongoDB + Redis 连接
│   │   │   ├── cache.py              # Redis 缓存封装
│   │   │   ├── llm_client.py         # LLM 客户端
│   │   │   ├── embedding.py          # BGE-M3 向量化
│   │   │   ├── reranker.py           # BGE-Reranker 精排
│   │   │   ├── vector_store.py       # Milvus 向量库
│   │   │   ├── milvus_client.py      # Milvus 连接管理
│   │   │   ├── minio_client.py       # MinIO 文件操作
│   │   │   ├── ocr.py                # OCR 引擎
│   │   │   ├── strategy_selector.py  # 检索策略选择
│   │   │   ├── response.py           # 统一响应格式
│   │   │   ├── exceptions.py         # 业务异常定义
│   │   │   └── logger.py             # 日志（loguru）
│   │   ├── agent/                    # LangGraph Agent
│   │   │   ├── graph.py              # 工作流图定义
│   │   │   ├── nodes.py              # 节点实现
│   │   │   ├── state.py              # 状态定义
│   │   │   └── prompts.py            # 提示词
│   │   └── utils/                    # 工具函数
│   │       ├── chunker.py            # 简历切片
│   │       ├── dedup.py              # 简历去重
│   │       ├── pii.py                # PII 脱敏
│   │       └── salary.py             # 薪资解析
│   ├── tests/                        # 测试代码（184 个测试）
│   │   ├── api/                      # API 层测试
│   │   ├── services/                 # Service 层测试
│   │   ├── core/                     # Core 层测试
│   │   ├── agent/                    # Agent 测试
│   │   ├── utils/                    # 工具函数测试
│   │   ├── e2e/                      # 端到端集成测试
│   │   │   ├── conftest.py           # E2E fixtures（FakeMongoDB 等）
│   │   │   ├── fake_infra.py         # 内存 MongoDB/Redis 模拟
│   │   │   └── test_recruitment_flow.py  # 32 步招聘闭环测试
│   │   └── test_integration.py       # 集成测试
│   ├── .env.example                  # 环境变量模板
│   ├── .gitignore
│   ├── pyproject.toml                # 项目元信息
│   ├── pytest.ini                    # pytest 配置
│   └── requirements.txt              # 依赖清单（锁定版本）
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

- **Python >= 3.11**（推荐 3.12）
- **uv** 包管理器
- **MongoDB 6.0+**
- **Redis 6.0+**
- **Milvus 2.4+**
- **MinIO**

### 1. 克隆项目

```bash
git clone <repo-url>
cd HR
```

### 2. 创建虚拟环境并安装依赖

```bash
cd backend
uv venv .venv --python 3.12
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
uv pip install -r requirements.txt
```

### 3. 下载模型

下载 BGE-M3 与 BGE-Reranker-v2-m3 模型到 `backend/models/`：

```
backend/
└── models/
    ├── bge-m3/
    └── bge-reranker-v2-m3/
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入实际的 LLM_API_KEY、数据库连接等
```

### 5. 启动开发服务器

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：
- API 入口：http://localhost:8000/api/v1
- 健康检查：http://localhost:8000/health
- Swagger 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc

### 6. 运行测试

```bash
# 运行全量测试（184 个）
.venv\Scripts\python.exe -m pytest

# 仅运行单元/集成测试
.venv\Scripts\python.exe -m pytest tests/ --ignore=tests/e2e

# 仅运行 E2E 测试
.venv\Scripts\python.exe -m pytest tests/e2e/ -v

# 运行指定模块测试
.venv\Scripts\python.exe -m pytest tests/api/test_auth_api.py -v
```

## 配置说明

所有配置通过 `.env` 文件管理，禁止硬编码。完整配置项见 [`backend/.env.example`](backend/.env.example)：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `APP_NAME` | 应用名称 | TalentSense HR |
| `API_V1_PREFIX` | API 前缀 | /api/v1 |
| `MONGO_URI` | MongoDB 连接串 | mongodb://localhost:27017 |
| `MONGO_DB` | MongoDB 库名 | talentsense |
| `REDIS_URL` | Redis 连接串 | redis://localhost:6379/0 |
| `MILVUS_HOST` / `MILVUS_PORT` | Milvus 地址 | localhost:19530 |
| `MILVUS_COLLECTION` | Milvus 集合名 | resumes |
| `MINIO_ENDPOINT` | MinIO 地址 | localhost:9000 |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO 凭证 | minioadmin / minioadmin |
| `MINIO_BUCKET` | MinIO 桶名 | resumes |
| `LLM_API_KEY` | LLM API Key | （必填） |
| `LLM_BASE_URL` | LLM 接口地址 | 通义千问兼容模式 |
| `LLM_MODEL` | LLM 模型名 | qwen-plus |
| `JWT_SECRET` | JWT 签名密钥 | （生产必改） |
| `JWT_ALGORITHM` | JWT 算法 | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效期 | 60 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 有效期 | 7 |
| `BGE_M3_PATH` | BGE-M3 模型路径 | ./models/bge-m3 |
| `BGE_RERANKER_PATH` | BGE-Reranker 模型路径 | ./models/bge-reranker-v2-m3 |
| `HYBRID_DENSE_WEIGHT` | 稠密向量权重 | 1.0 |
| `HYBRID_SPARSE_WEIGHT` | 稀疏向量权重 | 0.7 |
| `RETRIEVE_TOP_K` | 初筛召回数 | 20 |
| `RERANK_TOP_K` | 精排返回数 | 10 |

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
| 候选人 | `/api/v1/candidates` | POST `/compare` · GET `/{resume_id}/similar` |
| 邮件 | `/api/v1/email` | POST `/send` · GET `/config` |
| JD 匹配 | `/api/v1/jd` | POST `` (JD 匹配) |
| 面试 | `/api/v1/interview` | POST `/questions` · POST `/notes` · GET `/notes/{resume_id}` |
| 看板 | `/api/v1/dashboard` | GET `/stats` |

完整接口字段与示例见 [`docs/API-Design.md`](docs/API-Design.md) 与 Swagger 文档。

## 测试

### 测试规模

| 类型 | 数量 | 说明 |
|------|------|------|
| 单元测试 | 152 | 覆盖 API / Services / Core / Agent / Utils 各层 |
| E2E 测试 | 32 | 端到端招聘闭环业务流程 |
| **合计** | **184** | **全部通过** |

### E2E 测试覆盖（32 步招聘闭环）

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

### E2E 技术实现

- **FakeMongoDB / FakeRedis**：自建内存数据库，支持 `$set`/`$push`/`$each`/`$slice`/`$in`/`$gte`/`$lte`/`$regex`/`$or`/`$and` 等操作符，使数据在 9 个 API 路由间真实流转
- **ExitStack 管理 24 个 patch**：规避 Python 静态嵌套块限制
- **直接修改类属性**：解决 service 模块已绑定原类引用的 patch 失效问题
- **SSE 流式采集**：用 `TestClient.stream` + `iter_text` 采集并解析 `event:`/`data:` 行

## 开发规范

### 工程约定

- **包管理**：统一使用 uv，启动用 `.venv\Scripts\python.exe`
- **依赖锁定**：`requirements.txt` 锁定全部版本
- **配置分离**：禁止硬编码敏感信息，统一走 `.env`
- **统一响应格式**：`{code, message, data, trace_id}`
- **API 前缀**：所有路由遵循 `/api/v1/[module]` 约定
- **三层架构**：api → services → core，模块职责单一

### 代码规范

- 每个文件开头必须写元信息（文件名/创建时间/作者/功能描述）
- 每个函数和类必须写文档注释，标明入参、出参及核心逻辑
- 核心逻辑和对外接口必须有 `try...except` 异常捕获与兜底返回
- 关键步骤、运行状态、报错信息必须写入日志

### 测试规范

- 每个模块必须附带单元测试（`test_模块名.py`）
- motor collection 的 `find()`/`aggregate()` 同步返回 cursor，测试中用 `MagicMock()` 而非 `AsyncMock()`
- 404 错误用 `status_code` 断言，不额外添加 404 handler
- 提交前必须全量测试通过

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
