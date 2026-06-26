# TalentSense HR 简历推荐系统 - 后端开发文档

**版本**：v2.5
**日期**：2026-06-26
**对接文档**：[API-Design.md](./API-Design.md)（接口契约）、[MVP-Design.md](./MVP-Design.md)（需求设计）

> 后端实现严格遵循 [API-Design.md](./API-Design.md) 中定义的端点、请求/响应结构与枚举值。本文档描述实现细节、目录结构、核心模块设计与关键技术点。

---

## 一、技术栈与依赖

| 组件 | 选型 | 版本 | 用途 |
|------|------|------|------|
| Web 框架 | FastAPI | 0.115+ | 异步路由、SSE、依赖注入 |
| ASGI | Uvicorn | 0.30+ | 开发/部署服务器 |
| 向量库 | Milvus | 2.4+ | Dense+Sparse 混合索引 |
| 业务库 | MongoDB | 7.0 | 简历元数据、对话历史、配置 |
| 缓存 | Redis | 7.0+ | 查询缓存、Token 黑名单 |
| 对象存储 | MinIO | - | 原始简历文件 |
| 嵌入模型 | BGE-M3 | - | Dense(1024)+Sparse |
| 重排模型 | BGE-Reranker-v2-m3 | - | CrossEncoder |
| RAG 框架 | LangChain | 0.3+ | 异步 RAG 链 |
| Agent | LangGraph | 0.2+ | 5 节点状态机 |
| LLM 客户端 | AsyncOpenAI | - | DashScope 兼容 |
| OCR | RapidOCR | - | onnxruntime 引擎 |
| PDF 解析 | PyMuPDF | - | PDF 文本提取 |
| DOCX 解析 | python-docx | - | DOCX 文本提取 |
| 邮件 | aiosmtplib | - | 异步发邮件 |
| Excel | openpyxl | - | Excel 导出 |
| 重试 | tenacity | - | LLM 调用重试 |
| 日志 | loguru | - | 替代 OpenTelemetry |
| 认证 | python-jose | - | JWT 生成/校验 |

---

## 二、目录结构与职责

```
backend/
├── app/
│   ├── main.py                       # FastAPI 入口，挂载路由，启动事件
│   ├── api/                          # 【API 层】薄路由，仅参数校验+调用 service
│   │   ├── __init__.py
│   │   ├── deps.py                   # 依赖注入：get_current_user / get_db
│   │   ├── auth.py                   # 认证路由 → auth_service
│   │   ├── resumes.py                # 简历路由 → resume_service
│   │   ├── chat.py                   # 对话路由(SSE) → agent_service
│   │   ├── search.py                 # 检索路由 → search_service
│   │   ├── candidates.py             # 候选人路由 → export/tag/similar
│   │   ├── email.py                  # 邮件路由 → email_service
│   │   ├── jd_match.py               # JD 匹配路由 → jd_match_service
│   │   └── dashboard.py              # 看板路由 → dashboard_service
│   │
│   ├── services/                     # 【Service 层】业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py           # JWT 生成/校验、Token 黑名单
│   │   ├── resume_service.py         # 解析/去重/脱敏/CRUD/父子块切分
│   │   ├── search_service.py         # 混合检索/Query改写/Reranker/缓存
│   │   ├── agent_service.py          # LangGraph 5节点 + SSE 流式编排
│   │   ├── email_service.py          # 邮件发送+HTML报告生成
│   │   ├── export_service.py         # Excel 导出
│   │   ├── tag_service.py            # 标签/收藏/评价
│   │   ├── jd_match_service.py       # JD 解析+匹配(复用 search)
│   │   ├── interview_service.py      # 面试题生成+评价记录
│   │   └── dashboard_service.py      # 统计聚合
│   │
│   ├── agent/                        # Agent 核心
│   │   ├── __init__.py
│   │   ├── graph.py                  # LangGraph 图定义(5节点)
│   │   ├── state.py                  # AgentState TypedDict
│   │   ├── nodes.py                  # 5 节点实现(<300行)
│   │   └── prompts.py                # Prompt 集中管理(1文件)
│   │
│   ├── core/                         # 【Core 层】基础设施
│   │   ├── __init__.py
│   │   ├── config.py                 # Pydantic Settings 配置
│   │   ├── database.py               # MongoDB/Redis 连接管理
│   │   ├── milvus_client.py          # Milvus 连接+Collection 初始化
│   │   ├── minio_client.py           # MinIO 文件上传/下载/预签名
│   │   ├── llm_client.py             # AsyncOpenAI + tenacity 重试
│   │   ├── embedding.py              # BGE-M3 嵌入(@property 延迟加载)
│   │   ├── reranker.py               # BGE-Reranker(@property 延迟加载)
│   │   ├── vector_store.py           # Milvus 混合检索(复用 EduRAG)
│   │   ├── strategy_selector.py      # Query 改写策略选择(复用 EduRAG)
│   │   ├── ocr.py                    # RapidOCR 封装(复用 EduRAG)
│   │   ├── cache.py                  # Redis 查询缓存装饰器
│   │   ├── logger.py                 # loguru 日志配置
│   │   ├── exceptions.py             # 统一异常定义
│   │   └── response.py               # 统一响应封装(JSONResponse)
│   │
│   ├── models/                       # Pydantic 数据模型(对应 API 文档)
│   │   ├── __init__.py
│   │   ├── common.py                 # ApiResponse/PageQuery/PageResult
│   │   ├── auth.py                   # LoginRequest/TokenResponse/UserInfo
│   │   ├── resume.py                 # ResumeListItem/ResumeDetail/UploadResponse
│   │   ├── chat.py                   # SessionCreate/ChatMessage/SSEEvent
│   │   ├── candidate.py              # CandidateCard/ExportRequest/SimilarResponse
│   │   ├── email.py                  # EmailRequest/EmailConfig
│   │   ├── jd.py                     # JdMatchRequest/MatchAnalysis
│   │   ├── interview.py              # InterviewQuestion/InterviewNote
│   │   └── dashboard.py              # DashboardStats
│   │
│   └── utils/
│       ├── pii.py                    # 手机号/邮箱脱敏(138****1234)
│       ├── dedup.py                  # phone_hash+email_hash 去重
│       ├── chunker.py                # 父子块切分(子300/父1200)
│       └── salary.py                 # 薪资字符串解析("20-30K"→{min:20,max:30})
│
├── requirements.txt
├── Dockerfile
└── .env.example                      # 环境变量模板
```

### 2.1 三层职责边界

| 层 | 职责 | 禁止 |
|----|------|------|
| **API 层** (`api/`) | 参数校验(Pydantic)、调用 service、统一响应封装、SSE 流编排 | ❌ 写业务逻辑、❌ 直接操作数据库 |
| **Service 层** (`services/`) | 业务逻辑、调用 core 基础设施、service 间可互相调用 | ❌ 处理 HTTP 请求/响应 |
| **Core 层** (`core/`) | 基础设施连接、通用工具(检索/嵌入/重排/缓存/日志) | ❌ 包含业务逻辑 |

---

## 三、Core 层基础设施实现

### 3.1 配置管理 `core/config.py`

使用 Pydantic Settings 读取环境变量：

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 服务
    APP_NAME: str = "TalentSense HR"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "talentsense"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "resumes"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "resumes"

    # LLM (DashScope 兼容 OpenAI)
    LLM_API_KEY: str
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-plus"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 模型路径
    BGE_M3_PATH: str = "./models/bge-m3"
    BGE_RERANKER_PATH: str = "./models/bge-reranker-v2-m3"

    # 检索参数
    HYBRID_DENSE_WEIGHT: float = 1.0
    HYBRID_SPARSE_WEIGHT: float = 0.7
    RETRIEVE_TOP_K: int = 20
    RERANK_TOP_K: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
```

### 3.2 数据库连接 `core/database.py`

```python
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect(cls):
        cls.client = AsyncIOMotorClient(settings.MONGO_URI)
        cls.db = cls.client[settings.MONGO_DB]
        # 创建索引
        await cls.db.resumes.create_index("resume_id", unique=True)
        await cls.db.resumes.create_index("candidate_id")
        await cls.db.resumes.create_index("phone_hash")
        await cls.db.resumes.create_index("email_hash")
        await cls.db.resumes.create_index("tags")
        await cls.db.resumes.create_index("is_favorite")
        await cls.db.chat_sessions.create_index("session_id", unique=True)
        await cls.db.chat_sessions.create_index([("user_id", 1), ("updated_at", -1)])

    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()

class RedisClient:
    pool: redis.ConnectionPool = None

    @classmethod
    async def connect(cls):
        cls.pool = redis.ConnectionPool.from_url(settings.REDIS_URL)

    @classmethod
    def get_client(cls) -> redis.Redis:
        return redis.Redis(connection_pool=cls.pool)
```

**MongoDB 集合设计**：

| 集合 | 用途 | 关键字段 |
|------|------|---------|
| `resumes` | 简历元数据 | resume_id, candidate_id, phone_hash, email_hash, tags, is_favorite |
| `chat_sessions` | 对话会话 | session_id, user_id, title, messages[], created_at |
| `email_config` | 邮件 SMTP 配置 | smtp_host, smtp_port, smtp_user, smtp_password_encrypted |
| `interview_notes` | 面试评价 | note_id, resume_id, interviewer, rating, result |

> `chat_sessions.messages` 内嵌消息数组（最近 5 轮），不单独建 messages 集合，简化查询。

### 3.3 Milvus 混合检索 `core/vector_store.py`（复用 EduRAG）

```python
from pymilvus import Collection, DataType, AnnSearchRequest, WeightedRanker

class VectorStore:
    """复用 EduRAG vector_store.py，适配 HR 简历场景"""

    def __init__(self):
        self._collection = None

    @property
    def collection(self) -> Collection:
        """延迟加载 Collection"""
        if self._collection is None:
            self._collection = self._init_collection()
        return self._collection

    def _init_collection(self) -> Collection:
        """初始化 Collection，字段见 MVP-Design.md 511-529"""
        # fields = [id, candidate_id, dense_vector(1024), sparse_vector,
        #           salary_min, salary_max, education_level, work_years,
        #           skills_text, parent_id, parent_content]
        # 索引: dense=IVF_FLAT/IP, sparse=SPARSE_INVERTED_INDEX/IP
        ...

    async def hybrid_search(self, query_dense, query_sparse, filters, top_k=20):
        """Dense+Sparse 混合检索，WeightedRanker(1.0, 0.7)"""
        dense_req = AnnSearchRequest(
            data=[query_dense], anns_field="dense_vector",
            param={"metric_type": "IP", "params": {"nprobe": 16}}, limit=top_k * 2
        )
        sparse_req = AnnSearchRequest(
            data=[query_sparse], anns_field="sparse_vector",
            param={"metric_type": "IP"}, limit=top_k * 2
        )
        results = self.collection.hybrid_search(
            reqs=[dense_req, sparse_req],
            rerank=WeightedRanker(settings.HYBRID_DENSE_WEIGHT, settings.HYBRID_SPARSE_WEIGHT),
            limit=top_k,
            expr=self._build_filter_expr(filters)  # 标量过滤
        )
        return self._parse_results(results)  # 还原父块内容
```

### 3.4 嵌入与重排（延迟加载）

`core/embedding.py` 与 `core/reranker.py` 均使用 `@property` 延迟初始化，避免启动时加载大模型占用内存：

```python
class EmbeddingModel:
    _model = None

    @property
    def model(self):
        if self._model is None:
            from FlagModel import FlagModel
            self._model = FlagModel(settings.BGE_M3_PATH, use_fp16=True)
        return self._model

    def encode(self, texts: list[str]) -> tuple[list, list]:
        """返回 (dense_vectors, sparse_vectors)"""
        embeddings = self.model.encode(texts, return_dense=True, return_sparse=True)
        return embeddings['dense'], embeddings['sparse']
```

### 3.5 Query 改写策略选择 `core/strategy_selector.py`（复用 EduRAG）

复用 EduRAG `strategy_selector.py` 的 LLM 策略选择逻辑，4 种策略：

| 策略 | 适用场景 | 实现来源 |
|------|---------|---------|
| `direct` | 明确具体 query（"Java 5年"） | 直接检索 |
| `hyde` | 模糊描述（"找个Java大佬"） | LLM 生成假设答案→检索（EduRAG `_retrieve_with_hyde`） |
| `subquery` | 复杂多条件（"Java且会Python，5年经验"） | LLM 拆解子查询→多路检索（EduRAG `_retrieve_with_subqueries`） |
| `backtracking` | 简化回溯（"刚说的那个会微服务的"） | LLM 简化历史问题→检索（EduRAG `_retrieve_with_backtracking`） |

```python
class StrategySelector:
    """复用 EduRAG strategy_selector.py"""

    async def select(self, query: str, history: list[dict]) -> str:
        """LLM 一次调用返回策略: direct/hyde/subquery/backtracking"""
        prompt = STRATEGY_SELECT_PROMPT.format(query=query, history=history[-5:])
        resp = await llm_client.chat([{"role": "user", "content": prompt}])
        return resp.strip().lower()

    async def rewrite(self, query: str, strategy: str, history: list[dict]) -> list[str]:
        """根据策略改写 query，返回改写后的 query 列表"""
        # direct: [query]
        # hyde: [LLM 生成的假设答案]
        # subquery: [LLM 拆解的子查询]
        # backtracking: [LLM 简化后的问题]
        ...
```

### 3.6 LLM 客户端 `core/llm_client.py`

```python
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def chat(self, messages: list[dict], stream: bool = False, **kwargs):
        """非流式或流式调用，tenacity 重试 3 次"""
        resp = await self.client.chat.completions.create(
            model=settings.LLM_MODEL, messages=messages, stream=stream, **kwargs
        )
        if not stream:
            return resp.choices[0].message.content
        return resp  # 流式返回 async generator

    async def chat_stream(self, messages: list[dict], **kwargs):
        """流式生成，yield token"""
        stream = await self.client.chat.completions.create(
            model=settings.LLM_MODEL, messages=messages, stream=True, **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

llm_client = LLMClient()
```

### 3.7 统一响应与异常 `core/response.py` / `core/exceptions.py`

```python
# core/response.py
def success(data=None, message="success"):
    return {"code": 0, "message": message, "data": data, "trace_id": get_trace_id()}

def error(code: int, message: str, data=None):
    return {"code": code, "message": message, "data": data, "trace_id": get_trace_id()}

# core/exceptions.py
class BizError(Exception):
    def __init__(self, code: int, message: str, data=None):
        self.code = code
        self.message = message
        self.data = data

# main.py 全局异常处理
@app.exception_handler(BizError)
async def biz_error_handler(request, exc: BizError):
    return JSONResponse(status_code=HTTP_MAP[exc.code], content=error(exc.code, exc.message, exc.data))
```

---

## 四、Service 层实现

### 4.1 简历服务 `services/resume_service.py`

**核心流程：上传 → 解析 → 去重 → 脱敏 → 父子块切分 → 入库**

```python
class ResumeService:
    async def upload(self, file: UploadFile, overwrite: bool = False) -> dict:
        """对应 API: POST /resumes/upload"""
        # 1. 保存到 MinIO
        file_id = await minio_client.upload(file)
        # 2. 异步触发解析（后台任务）
        resume_id = f"res_{uuid4().hex[:12]}"
        await self._parse_and_index(resume_id, file, file_id, overwrite)
        return {"resume_id": resume_id, "parse_status": "parsing", ...}

    async def _parse_and_index(self, resume_id, file, file_id, overwrite):
        """解析全链路（后台任务）"""
        try:
            # 1. 文件解析：PyMuPDF/docx → 文本，失败则 RapidOCR
            text = await self._extract_text(file)
            # 2. LLM 结构化提取
            structured = await self._llm_extract(text)
            # 3. PII 脱敏 + hash 去重
            masked = pii_mask(structured)
            dup = await self._check_duplicate(masked.phone_hash, masked.email_hash)
            if dup and not overwrite:
                await self._mark_duplicate(resume_id, dup)
                return
            # 4. 父子块切分（复用 EduRAG document_processor）
            child_chunks, parent_chunks = chunker.split(text, child_size=300, parent_size=1200)
            # 5. BGE-M3 编码子块
            dense, sparse = embedding.encode([c.content for c in child_chunks])
            # 6. 写入 Milvus（子块入库，parent_content 一起存）
            await vector_store.insert(child_chunks, dense, sparse, parent_chunks, resume_id)
            # 7. 写入 MongoDB 元数据
            await mongodb.db.resumes.insert_one({...})
        except Exception as e:
            await self._mark_failed(resume_id, str(e))
```

**文本提取降级链（两级，非三级）**：
```
PyMuPDF(PDF) / python-docx(DOCX) → 成功 → 用
                ↓ 失败/图片型
            RapidOCR(图片/PDF扫描件) → 用
```

**父子块切分**（复用 EduRAG `document_processor.py`）：
- 子块 300 字符入 Milvus（精确检索）
- 父块 1200 字符作为 `parent_content` 一起存（Small-to-Big 还原，提供完整上下文）

**去重逻辑**（`utils/dedup.py`）：
```python
def phone_hash(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()
# 上传时计算 phone_hash + email_hash，查 MongoDB，命中则 is_duplicate=true
```

**脱敏逻辑**（`utils/pii.py`）：
```python
def mask_phone(phone: str) -> str:
    return phone[:3] + "****" + phone[-4:]  # 138****1234
def mask_email(email: str) -> str:
    name, domain = email.split("@")
    return name[:3] + "***@" + domain  # zhang***@xx.com
```

### 4.2 检索服务 `services/search_service.py`

**对应 API：`POST /search`**，核心检索链路（MVP-Design.md 5.1）：

```python
class SearchService:
    async def search(self, query: str, strategy: str, filters: dict, top_k: int) -> dict:
        """对应 API: POST /search"""
        # 1. 缓存检查（Redis，key = hash(query+strategy+filters)）
        cache_key = f"search:{hash((query, strategy, str(filters), top_k))}"
        if cached := await redis.get(cache_key):
            return cached

        # 2. 策略选择（strategy=auto 时由 LLM 选，否则用指定策略）
        if strategy == "auto":
            strategy = await strategy_selector.select(query, history=[])
        # 3. Query 改写
        rewrites = await strategy_selector.rewrite(query, strategy, history=[])
        # 4. BGE-M3 编码改写后的 query
        dense, sparse = embedding.encode(rewrites)
        # 5. Milvus 混合检索 Top-20 子块
        chunks = await vector_store.hybrid_search(dense, sparse, filters, top_k=20)
        # 6. 还原父文档 + 去重（同一 resume_id 取最高分）
        candidates = self._dedup_and_restore(chunks)
        # 7. BGE-Reranker 精排 Top-10
        reranked = await reranker.rerank(query, candidates, top_k=10)
        # 8. Python 标量过滤（薪资/学历/年限硬条件）
        filtered = self._apply_filters(reranked, filters)
        # 9. LLM 评分 + 推荐理由（0-100 + 自然语言）
        scored = await self._llm_score(query, filtered[:top_k])
        # 10. 缓存结果（5 分钟）
        await redis.setex(cache_key, 300, result)
        return {"query_rewrite": rewrites[0], "strategy": strategy, "candidates": scored, "total": len(scored)}

    async def _llm_score(self, query, candidates):
        """LLM 对每个候选人打分 0-100 并生成推荐理由"""
        prompt = SCORE_PROMPT.format(query=query, candidates=candidates)
        result = await llm_client.chat([{"role": "user", "content": prompt}])
        return self._parse_score(result, candidates)
```

### 4.3 Agent 服务 `services/agent_service.py`（LangGraph 5 节点 + SSE）

**对应 API：`POST /chat/sessions/{session_id}/messages`（SSE 流式）**

```python
class AgentService:
    async def stream_chat(self, session_id: str, query: str, context: dict):
        """SSE 流式编排，yield SSE 事件"""
        # 1. 加载会话历史（MongoDB，最近 5 轮）
        history = await self._load_history(session_id)
        # 2. 构建 AgentState
        state = AgentState(
            messages=history, user_query=query, session_id=session_id,
            intent=None, strategy=None, filters=context.get("filters", {}),
            query_rewrites=[], candidates=[], ranked=[], last_candidates=self._last_candidates(history),
            clarification=None, response={}, trace_id=get_trace_id()
        )
        # 3. 运行 LangGraph 图，逐步 yield SSE 事件
        async for event in graph.astream(state, stream_mode="custom"):
            yield event  # 已封装为 SSE 事件格式
        # 4. 持久化对话（user + assistant 消息存 MongoDB）
        await self._save_messages(session_id, query, state.response)
```

### 4.4 邮件服务 `services/email_service.py`

```python
class EmailService:
    async def send_recommendation(self, request: EmailRequest) -> dict:
        """对应 API: POST /email/send-recommendation"""
        # 1. 查询候选人详情
        candidates = await resume_service.get_many(request.candidate_ids)
        # 2. LLM 生成 HTML 邮件正文（卡片式排版）
        html = await self._generate_html(request.query, candidates, request.remark)
        # 3. 生成 Excel 附件（复用 export_service）
        attachment = None
        if request.include_excel:
            attachment = await export_service.generate_excel(candidates)
        # 4. 读取 SMTP 配置
        config = await self._get_smtp_config()
        # 5. aiosmtplib 异步发送
        await self._send_email(config, request.to_email, request.subject, html, attachment)
        return {"message_id": ..., "status": "sent", "sent_at": ..., "recipient": request.to_email}

    async def _generate_html(self, query, candidates, remark):
        """LLM 生成候选人卡片式 HTML 邮件正文"""
        prompt = EMAIL_HTML_PROMPT.format(query=query, candidates=candidates, remark=remark)
        return await llm_client.chat([{"role": "user", "content": prompt}])
```

### 4.5 其他服务

| Service | 对应 API | 核心实现 |
|---------|---------|---------|
| `export_service.py` | `POST /candidates/export` | `openpyxl` 生成 Excel，StreamingResponse 返回 |
| `tag_service.py` | `PUT /resumes/{id}/tags`、`/favorite`、`/notes` | MongoDB 更新，清相关缓存 |
| `jd_match_service.py` | `POST /jd/match` | LLM 提取 JD 要求 → 调 `search_service.search()` → LLM 生成匹配分析 |
| `interview_service.py` | `POST /candidates/{id}/interview-questions`、`/interview-notes` | LLM 按维度生成题，评价存 MongoDB |
| `dashboard_service.py` | `GET /dashboard/stats` | MongoDB aggregation 聚合统计 |
| `auth_service.py` | `/auth/*` | JWT 生成，Redis 存 Token 黑名单 |

**JD 匹配复用 search**（关键设计）：
```python
class JdMatchService:
    async def match(self, jd_text: str, top_k: int, filters: dict) -> dict:
        # 1. LLM 提取 JD 结构化要求
        requirements = await self._parse_jd(jd_text)
        # 2. 用 JD 文本作为 query，复用 search_service
        result = await search_service.search(
            query=jd_text, strategy="auto",
            filters={**filters, **requirements.to_filters()}, top_k=top_k
        )
        # 3. LLM 生成匹配分析（matched_skills/missing_skills/reason）
        candidates = await self._analyze_match(requirements, result.candidates)
        return {"parsed_requirements": requirements, "candidates": candidates, "total": len(candidates)}
```

---

## 五、Agent 设计（LangGraph 5 节点）

### 5.1 AgentState（`agent/state.py`）

```python
from typing import TypedDict

class AgentState(TypedDict):
    messages: list[dict]           # 对话历史（最近5轮）
    user_query: str                # 当前输入
    session_id: str
    intent: str                    # chitchat/search/detail/compare
    strategy: str                  # direct/hyde/subquery/backtracking
    filters: dict                  # 提取的筛选条件
    query_rewrites: list[str]      # 改写后的 query
    candidates: list[dict]         # 检索到的候选人
    ranked: list[dict]             # Reranker+LLM 评分排序后
    last_candidates: list[dict]    # 上轮推荐(支持"第一个候选人")
    clarification: str             # 追问问题
    response: dict                 # 最终响应
    trace_id: str
```

### 5.2 图定义（`agent/graph.py`）

```python
from langgraph.graph import StateGraph, END

graph_builder = StateGraph(AgentState)

# 添加 5 节点
graph_builder.add_node("intent", intent_node)
graph_builder.add_node("retrieve_rank", retrieve_rank_node)
graph_builder.add_node("clarify", clarify_node)
graph_builder.add_node("detail", detail_node)
graph_builder.add_node("respond", respond_node)

# 入口
graph_builder.set_entry_point("intent")

# intent 条件分支
graph_builder.add_conditional_edges("intent", route_by_intent, {
    "chitchat": "respond",
    "search": "retrieve_rank",
    "detail": "detail",
    "compare": "detail"
})

# retrieve_rank → clarify（召回不足）或 respond（正常）
graph_builder.add_conditional_edges("retrieve_rank", route_after_retrieve, {
    "need_clarify": "clarify",
    "ok": "respond"
})

# clarify → END（等用户回答）
graph_builder.add_edge("clarify", END)

# detail → respond
graph_builder.add_edge("detail", "respond")

# respond → END
graph_builder.add_edge("respond", END)

graph = graph_builder.compile()
```

### 5.3 节点实现（`agent/nodes.py`）

每个节点通过 `StreamWriter` 推送 SSE 事件：

```python
from langgraph.config import get_stream_writer

async def intent_node(state: AgentState) -> dict:
    """意图识别：chitchat/search/detail/compare"""
    writer = get_stream_writer()
    # LLM 一次调用识别意图 + 提取筛选条件
    result = await llm_client.chat([
        {"role": "system", "content": INTENT_PROMPT},
        {"role": "user", "content": state["user_query"]}
    ])
    intent, filters = parse_intent(result)
    writer({"event": "intent", "data": {"intent": intent, "strategy": "auto"}})
    return {"intent": intent, "filters": {**state["filters"], **filters}}

async def retrieve_rank_node(state: AgentState) -> dict:
    """Query改写→混合检索→Reranker→LLM评分"""
    writer = get_stream_writer()
    # 1. 策略选择 + 改写
    strategy = await strategy_selector.select(state["user_query"], state["messages"])
    rewrites = await strategy_selector.rewrite(state["user_query"], strategy, state["messages"])
    writer({"event": "rewrite", "data": {"query": rewrites[0], "rewrites": rewrites}})
    # 2. 检索（复用 search_service 核心链路）
    candidates = await search_service._retrieve(rewrites, state["filters"])
    writer({"event": "retrieval", "data": {"count": len(candidates), "candidate_ids": [...]}})
    # 3. Reranker + LLM 评分
    ranked = await search_service._rank_and_score(state["user_query"], candidates)
    writer({"event": "rank", "data": {"ranked": [{"candidate_id": c["candidate_id"], "score": c["score"]} for c in ranked]}})
    return {"strategy": strategy, "query_rewrites": rewrites, "ranked": ranked, "last_candidates": ranked}

async def clarify_node(state: AgentState) -> dict:
    """召回不足时生成追问问题（不做HITL超时降级）"""
    question = await llm_client.chat([
        {"role": "system", "content": CLARIFY_PROMPT},
        {"role": "user", "content": f"用户需求：{state['user_query']}\n召回：{len(state['ranked'])}人"}
    ])
    return {"clarification": question, "response": {"content": question, "intent": "clarify"}}

async def detail_node(state: AgentState) -> dict:
    """基于 last_candidates 回答详情/对比"""
    result = await llm_client.chat([
        {"role": "system", "content": DETAIL_PROMPT},
        {"role": "user", "content": f"问题：{state['user_query']}\n候选人：{state['last_candidates']}"}
    ])
    return {"response": {"content": result, "intent": state["intent"], "candidates": state["last_candidates"]}}

async def respond_node(state: AgentState) -> dict:
    """生成最终响应，流式输出 token + 推送候选人卡片"""
    writer = get_stream_writer()
    if state["intent"] == "chitchat":
        async for token in llm_client.chat_stream([{"role": "user", "content": state["user_query"]}]):
            writer({"event": "token", "data": {"delta": token}})
        return {"response": {"content": "...", "intent": "chitchat"}}
    # search/detail/compare：推送候选人卡片 + 流式文本
    if state["ranked"] or state["last_candidates"]:
        candidates = state["ranked"] or state["last_candidates"]
        writer({"event": "candidates", "data": {"candidates": [to_card(c) for c in candidates]}})
    # LLM 流式生成推荐说明
    full_text = ""
    async for token in llm_client.chat_stream([...]):
        writer({"event": "token", "data": {"delta": token}})
        full_text += token
    message_id = f"msg_{uuid4().hex[:12]}"
    writer({"event": "done", "data": {"message_id": message_id, "response": full_text}})
    return {"response": {"message_id": message_id, "content": full_text, "intent": state["intent"], "candidates": state["ranked"]}}
```

### 5.4 Prompt 集中管理（`agent/prompts.py`）

```python
# 所有 Prompt 集中在 1 文件，改 Prompt 不跳文件

INTENT_PROMPT = """你是HR招聘助手意图识别器。判断用户意图：
- chitchat: 闲聊/问候
- search: 搜索/推荐候选人
- detail: 询问已推荐候选人的详情
- compare: 对比已推荐的候选人
同时提取筛选条件（education_min/work_years_min/salary_min/salary_max/skills）。
返回 JSON: {"intent": "...", "filters": {...}}
用户输入：{query}"""

HYDE_PROMPT = """基于以下招聘需求，生成一段假设的理想候选人简历描述...
需求：{query}"""

SCORE_PROMPT = """对以下候选人按需求匹配度打分(0-100)并给出推荐理由...
需求：{query}
候选人：{candidates}
返回 JSON 数组: [{"candidate_id": "...", "score": 95, "reason": "..."}]"""

EMAIL_HTML_PROMPT = """生成HTML格式候选人推荐邮件，卡片式排版..."""

# ... 其他 Prompt
```

---

## 六、API 层实现要点

### 6.1 路由注册（`main.py`）

```python
from fastapi import FastAPI
from app.api import auth, resumes, chat, search, candidates, email, jd_match, dashboard

app = FastAPI(title="TalentSense HR", version="2.5")

@app.on_event("startup")
async def startup():
    await MongoDB.connect()
    await RedisClient.connect()

@app.on_event("shutdown")
async def shutdown():
    await MongoDB.disconnect()

# 统一前缀 /api/v1
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["认证"])
app.include_router(resumes.router, prefix=f"{settings.API_V1_PREFIX}/resumes", tags=["简历"])
app.include_router(chat.router, prefix=f"{settings.API_V1_PREFIX}/chat", tags=["对话"])
app.include_router(search.router, prefix=f"{settings.API_V1_PREFIX}/search", tags=["检索"])
app.include_router(candidates.router, prefix=f"{settings.API_V1_PREFIX}/candidates", tags=["候选人"])
app.include_router(email.router, prefix=f"{settings.API_V1_PREFIX}/email", tags=["邮件"])
app.include_router(jd_match.router, prefix=f"{settings.API_V1_PREFIX}/jd", tags=["JD匹配"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["看板"])
```

### 6.2 依赖注入（`api/deps.py`）

```python
from fastapi import Depends, Header
from app.services.auth_service import AuthService

async def get_current_user(authorization: str = Header(...)) -> dict:
    """JWT 校验，返回用户信息"""
    if not authorization.startswith("Bearer "):
        raise BizError(1002, "Token 格式错误")
    token = authorization[7:]
    user = await AuthService.verify_token(token)
    if not user:
        raise BizError(1002, "Token 已过期，请重新登录")
    return user
```

### 6.3 SSE 流式接口示例（`api/chat.py`）

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.services.agent_service import AgentService

router = APIRouter()

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    body: ChatRequest,
    user: dict = Depends(get_current_user)
):
    async def event_stream():
        try:
            async for event in AgentService().stream_chat(session_id, body.query, body.context):
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
        except BizError as e:
            yield f"event: error\ndata: {json.dumps({'code': e.code, 'message': e.message})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
```

### 6.4 文件下载接口示例（`api/candidates.py`）

```python
@router.post("/export")
async def export_candidates(body: ExportRequest, user: dict = Depends(get_current_user)):
    excel_bytes = await ExportService().generate_excel(body.candidate_ids, body.fields)
    return StreamingResponse(
        iter([excel_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=candidates_{date.today()}.xlsx"}
    )
```

---

## 七、数据层实现

### 7.1 Milvus Collection 定义

```python
# core/milvus_client.py
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
    FieldSchema(name="parent_id", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="parent_content", dtype=DataType.VARCHAR, max_length=4000),
]
schema = CollectionSchema(fields, description="HR resumes hybrid index")
collection = Collection(settings.MILVUS_COLLECTION, schema)

# 索引
collection.create_index("dense_vector", {"index_type": "IVF_FLAT", "metric_type": "IP", "params": {"nlist": 1024}})
collection.create_index("sparse_vector", {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"})
collection.load()
```

### 7.2 过滤表达式构建

```python
def _build_filter_expr(filters: dict) -> str:
    """构建 Milvus 标量过滤表达式"""
    exprs = []
    if filters.get("education_min") is not None:
        exprs.append(f"education_level >= {filters['education_min']}")
    if filters.get("work_years_min") is not None:
        exprs.append(f"work_years >= {filters['work_years_min']}")
    if filters.get("salary_max") is not None:
        exprs.append(f"salary_min <= {filters['salary_max']}")
    return " and ".join(exprs)
```

### 7.3 Redis 缓存策略

| 缓存 Key | TTL | 用途 | 失效时机 |
|----------|-----|------|---------|
| `search:{hash}` | 5min | 检索结果缓存 | 简历增删改 |
| `resume:{resume_id}` | 10min | 简历详情缓存 | 简历更新/删除 |
| `dashboard:stats:{range}` | 10min | 看板统计缓存 | 简历增删改 |
| `token:blacklist:{token}` | Token 剩余有效期 | 登出 Token 黑名单 | 自然过期 |

---

## 八、与 API 文档的对接说明

后端实现严格遵循 [API-Design.md](./API-Design.md)：

| API 文档章节 | 后端实现位置 |
|-------------|-------------|
| 一、Auth | `api/auth.py` + `services/auth_service.py` |
| 二、Resumes | `api/resumes.py` + `services/resume_service.py` + `services/tag_service.py` |
| 三、Chat（SSE） | `api/chat.py` + `services/agent_service.py` + `agent/` |
| 四、Search | `api/search.py` + `services/search_service.py` |
| 五、Candidates | `api/candidates.py` + `services/export_service.py` + `services/tag_service.py` |
| 六、Email | `api/email.py` + `services/email_service.py` |
| 七、JD Match | `api/jd_match.py` + `services/jd_match_service.py` |
| 八、Interview | `api/candidates.py` + `services/interview_service.py` |
| 九、Dashboard | `api/dashboard.py` + `services/dashboard_service.py` |
| 数据模型 10.1-10.4 | `models/*.py`（Pydantic 模型与 API 文档完全一致） |

**对接要点**：
1. 所有接口响应必须使用 `core/response.success()` / `error()` 封装，保证 `code/message/data/trace_id` 四字段
2. SSE 事件类型必须与 [API-Design.md 0.5](./API-Design.md#05-sse-流式响应约定) 完全一致（intent/rewrite/retrieval/rank/token/candidates/done/error）
3. 枚举值（intent/strategy/education_level/parse_status）必须与 API 文档 0.6 节一致
4. 分页响应必须遵循 `{list, total, page, page_size, total_pages}` 结构
5. 简历详情字段名必须与 [ResumeDetail](./API-Design.md#102-resumedetail) 一致（前端依赖字段名渲染）

---

## 九、关键实现注意事项

### 9.1 延迟加载节省启动内存
BGE-M3（~2GB）和 BGE-Reranker（~1GB）使用 `@property` 首次调用时加载，FastAPI 启动不加载模型，启动快、内存可控。

### 9.2 异步全链路
- 所有 I/O（MongoDB/Redis/Milvus/MinIO/LLM）使用异步客户端
- LLM 流式输出使用 `AsyncOpenAI` 的 `stream=True`
- 邮件发送使用 `aiosmtplib`，不阻塞主流程

### 9.3 缓存失效策略
简历增删改时，主动清除相关 Redis 缓存：
```python
async def _invalidate_cache(resume_id: str):
    await redis.delete(f"resume:{resume_id}")
    await redis.delete("dashboard:stats:*")  # 通配清除看板缓存
    # search 缓存因 key 是 hash，难以精确清除，设置 5min 短 TTL 自然过期
```

### 9.4 错误处理
- LLM 调用失败：tenacity 重试 3 次，仍失败返回 `code=2002`
- 简历解析失败：标记 `parse_status=failed`，返回 `code=2001`
- 邮件发送失败：返回 `code=2004`，不重试（避免垃圾邮件）

### 9.5 日志规范（loguru 替代 OpenTelemetry）
```python
from loguru import logger
logger.bind(trace_id=trace_id).info("检索完成", query=query, count=len(candidates))
```
所有日志绑定 `trace_id`，与 API 响应的 `trace_id` 关联，便于问题排查。
