"""
文件名: app/main.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: FastAPI 应用入口，负责路由挂载、启动事件、全局异常处理、可观测性集成
"""
import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from bson import ObjectId

from app.core.config import settings
from app.core.response import error, CODE, HTTP_MAP
from app.core.exceptions import BizError
from app.core.logger import logger, bind_trace_id, bind_request_context, clear_request_context


def _init_sentry():
    """可选初始化 Sentry，SENTRY_DSN 非空时启用"""
    dsn = settings.SENTRY_DSN.strip()
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=0.1,
            environment="production" if not settings.DEBUG else "development",
            release=settings.APP_NAME,
            integrations=[
                StarletteIntegration(transaction_style="url"),
                FastApiIntegration(transaction_style="url"),
                LoggingIntegration(event_level="ERROR"),
            ],
            send_default_pii=False,
        )
        logger.info(f"Sentry 已启用 traces_sample_rate={settings.SENTRY_TRACES_SAMPLE_RATE}")
    except Exception as e:
        logger.warning(f"Sentry 初始化失败（忽略）: {e}")


class MongoJSONEncoder(json.JSONEncoder):
    """MongoDB ObjectId JSON 序列化兜底"""

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


def _dumps(obj) -> str:
    """统一序列化，自动转 ObjectId 为字符串"""
    return json.dumps(obj, cls=MongoJSONEncoder, ensure_ascii=False)


class MongoJSONResponse(JSONResponse):
    """自定义 JSONResponse，支持 ObjectId 序列化"""

    def render(self, content) -> bytes:
        return _dumps(content).encode("utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """生命周期：启动/关闭事件

    - 连接 MongoDB / Redis
    - 预热 Milvus Collection（避免首次解析时才连接/建表失败被吞掉）
    - 异步线程池预热 BGE-M3/Reranker/OCR 模型（不阻塞事件循环）
    - 预热 MinIO 连接
    - 重置上次异常中断遗留的 parsing 状态为 failed
    """
    from app.core.database import MongoDB, RedisClient
    await MongoDB.connect()
    await RedisClient.connect()
    try:
        from app.core.milvus_client import milvus_client
        await asyncio.to_thread(milvus_client.ensure_collection)
        logger.info("Milvus Collection 已就绪")
    except Exception as e:
        logger.warning(f"Milvus 预热失败，简历解析相关接口将不可用: {e}")

    def _preload_models():
        """线程池中同步预热所有模型，避免阻塞事件循环"""
        try:
            from app.core.embedding import embedding_model
            _ = embedding_model.model
            logger.info("BGE-M3 模型已预热")
        except Exception as e:
            logger.warning(f"BGE-M3 预热失败: {e}")
        try:
            from app.core.reranker import reranker_model
            _ = reranker_model.model
            logger.info("BGE-Reranker 模型已预热")
        except Exception as e:
            logger.warning(f"BGE-Reranker 预热失败: {e}")
        try:
            from app.core.ocr import ocr_engine
            _ = ocr_engine.engine
            logger.info("RapidOCR 引擎已预热")
        except Exception as e:
            logger.warning(f"RapidOCR 预热失败: {e}")
        try:
            from app.core.minio_client import minio_client
            _ = minio_client.client
            logger.info("MinIO 客户端已预热")
        except Exception as e:
            logger.warning(f"MinIO 预热失败: {e}")

    preload_task = asyncio.create_task(asyncio.to_thread(_preload_models))

    try:
        from app.core.database import MongoDB
        if MongoDB.db is not None:
            await MongoDB.db.resumes.create_index("user_id")
            await MongoDB.db.resumes.create_index("parse_info.parse_status")
            await MongoDB.db.resumes.create_index([("created_at", -1)])
            await MongoDB.db.resumes.create_index([("education_level", 1), ("work_years", 1)])
            await MongoDB.db.chat_sessions.create_index([("user_id", 1), ("updated_at", -1)])
            await MongoDB.db.chat_messages.create_index("session_id")
            await MongoDB.db.email_templates.create_index("template_id", unique=True)
            await MongoDB.db.frontend_errors.create_index([("created_at", -1)])
            await MongoDB.db.frontend_errors.create_index([("user_id", 1), ("created_at", -1)])
            logger.info("MongoDB 索引已就绪")
    except Exception as e:
        logger.warning(f"MongoDB 索引创建失败（可能已存在）: {e}")

    try:
        from app.services.auth_service import AuthService
        admin_username = settings.ADMIN_USERNAME
        exists = await MongoDB.db.users.find_one({"username": admin_username})
        if exists:
            need_backfill = {}
            if not exists.get("email"):
                need_backfill["email"] = settings.ADMIN_EMAIL
            if not exists.get("name"):
                need_backfill["name"] = "管理员"
            if need_backfill:
                need_backfill["updated_at"] = datetime.now(timezone.utc).isoformat()
                await MongoDB.db.users.update_one(
                    {"username": admin_username}, {"$set": need_backfill}
                )
                logger.info(f"管理员账号 {admin_username} 已回填字段: {list(need_backfill.keys())}")
            else:
                logger.info(f"管理员账号 {admin_username} 已存在")
        else:
            user_id = f"u_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc).isoformat()
            await MongoDB.db.users.insert_one({
                "user_id": user_id,
                "username": admin_username,
                "password_hash": AuthService.hash_password(settings.ADMIN_PASSWORD),
                "email": settings.ADMIN_EMAIL,
                "name": "管理员",
                "role": "admin",
                "status": "approved",
                "created_at": now,
                "updated_at": now,
            })
            logger.info(f"管理员账号 {admin_username} 已自动创建")
    except Exception as e:
        logger.warning(f"管理员初始化失败: {e}")
    try:
        from app.core.email_templates_seed import seed_builtin_templates
        await seed_builtin_templates(MongoDB.db)
        logger.info("预置邮件模板已就绪")
    except Exception as e:
        logger.warning(f"预置邮件模板初始化失败: {e}")
    try:
        await MongoDB.db.resumes.update_many(
            {"parse_info.parse_status": "parsing"},
            {"$set": {"parse_info.parse_status": "failed"}},
        )
    except Exception as e:
        logger.warning(f"重置遗留 parsing 状态失败: {e}")
    logger.info("应用启动完成（模型在后台预热中）")
    yield
    try:
        await asyncio.wait_for(preload_task, timeout=5)
    except Exception:
        pass
    await MongoDB.disconnect()
    clear_request_context()
    logger.info("应用已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version="2.6.0",
    lifespan=lifespan,
    default_response_class=MongoJSONResponse,
)

_init_sentry()

from app.core.metrics import setup_metrics
setup_metrics(app)


def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    """注入 trace_id + 绑定请求上下文 + 记录请求耗时/访问日志"""
    tid = request.headers.get("X-Trace-Id") or f"trace_{uuid.uuid4().hex[:16]}"
    bind_trace_id(tid)
    client_ip = _get_client_ip(request)
    bind_request_context(path=request.url.path, client_ip=client_ip)

    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Trace-Id"] = tid
        response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"

        if request.url.path in ("/health", "/metrics"):
            return response

        if status_code >= 500:
            logger.error(
                f"{request.method} {request.url.path} -> {status_code} ({elapsed_ms:.1f}ms) ip={client_ip}"
            )
        elif elapsed_ms > 1000:
            logger.warning(
                f"慢请求: {request.method} {request.url.path} -> {status_code} ({elapsed_ms:.1f}ms) ip={client_ip}"
            )
        elif status_code >= 400:
            logger.info(
                f"{request.method} {request.url.path} -> {status_code} ({elapsed_ms:.1f}ms) ip={client_ip}"
            )
        else:
            logger.debug(
                f"{request.method} {request.url.path} -> {status_code} ({elapsed_ms:.1f}ms)"
            )
        return response
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception(f"请求异常: {request.method} {request.url.path} ({elapsed_ms:.1f}ms): {exc}")
        raise
    finally:
        clear_request_context()


@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError):
    """业务异常处理"""
    bind_trace_id(request.headers.get("X-Trace-Id"))
    logger.warning(f"业务异常: code={exc.code} msg={exc.message} path={request.url.path}")
    return MongoJSONResponse(
        status_code=HTTP_MAP.get(exc.code, 500),
        content=error(exc.code, exc.message, exc.data),
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    """未捕获异常兜底"""
    bind_trace_id(request.headers.get("X-Trace-Id"))
    logger.exception(f"未捕获异常: {request.method} {request.url.path} - {exc}")
    dsn = settings.SENTRY_DSN.strip()
    if dsn:
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except Exception:
            pass
    return MongoJSONResponse(
        status_code=500,
        content=error(CODE.SERVER_ERROR, "服务器内部错误"),
    )


from app.core.health import router as health_router
app.include_router(health_router, tags=["健康检查"])

from app.api import auth
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["认证"])
from app.api import resumes
app.include_router(resumes.router, prefix=f"{settings.API_V1_PREFIX}/resumes", tags=["简历"])
from app.api import search
app.include_router(search.router, prefix=f"{settings.API_V1_PREFIX}/search", tags=["检索"])
from app.api import chat
app.include_router(chat.router, prefix=f"{settings.API_V1_PREFIX}/chat", tags=["对话"])
from app.api import candidates
app.include_router(candidates.router, prefix=f"{settings.API_V1_PREFIX}/candidates", tags=["候选人"])
from app.api import email
app.include_router(email.router, prefix=f"{settings.API_V1_PREFIX}/email", tags=["邮件"])
from app.api import jd_match
app.include_router(jd_match.router, prefix=f"{settings.API_V1_PREFIX}/jd", tags=["JD 匹配"])
from app.api import interview
app.include_router(interview.router, prefix=f"{settings.API_V1_PREFIX}/interview", tags=["面试"])
from app.api import dashboard
app.include_router(dashboard.router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["看板"])
from app.api import users
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["用户管理"])
from app.api import monitor
app.include_router(monitor.router, prefix=f"{settings.API_V1_PREFIX}/monitor", tags=["前端监控"])
