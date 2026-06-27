"""
文件名: app/main.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: FastAPI 应用入口，负责路由挂载、启动事件、全局异常处理
"""
import json
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from bson import ObjectId
from app.core.config import settings
from app.core.response import error, CODE, HTTP_MAP
from app.core.exceptions import BizError
from app.core.logger import logger, bind_trace_id


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
    - 重置上次异常中断遗留的 parsing 状态为 failed（参照 HRCopilot 启动兜底）
    """
    from app.core.database import MongoDB, RedisClient
    await MongoDB.connect()
    await RedisClient.connect()
    # 预热 Milvus：启动时即连接 + 确保 Collection 存在，失败仅警告不阻断启动
    try:
        from app.core.milvus_client import milvus_client
        milvus_client.ensure_collection()
        logger.info("Milvus Collection 已就绪")
    except Exception as e:
        logger.warning(f"Milvus 预热失败，简历解析相关接口将不可用: {e}")
    # 预热 BGE-M3 模型：避免首次上传简历时才加载导致解析很慢
    try:
        from app.core.embedding import embedding_model
        _ = embedding_model.model  # 触发懒加载
        logger.info("BGE-M3 模型已预热")
    except Exception as e:
        logger.warning(f"BGE-M3 预热失败，首次解析将较慢: {e}")
    # 自动初始化管理员账号
    try:
        from app.services.auth_service import AuthService
        admin_username = settings.ADMIN_USERNAME
        exists = await MongoDB.db.users.find_one({"username": admin_username})
        if exists:
            # 回填早期建库时缺失的 email/name 字段（邮箱登录改造的迁移兜底）
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
    # 初始化预置邮件模板
    try:
        from app.core.email_templates_seed import seed_builtin_templates
        await seed_builtin_templates(MongoDB.db)
        logger.info("预置邮件模板已就绪")
    except Exception as e:
        logger.warning(f"预置邮件模板初始化失败: {e}")
    # 重置遗留的 parsing 状态（进程上次崩溃会导致简历永久卡 parsing）
    try:
        await MongoDB.db.resumes.update_many(
            {"parse_info.parse_status": "parsing"},
            {"$set": {"parse_info.parse_status": "failed"}},
        )
    except Exception as e:
        logger.warning(f"重置遗留 parsing 状态失败: {e}")
    logger.info("应用启动完成")
    yield
    await MongoDB.disconnect()
    logger.info("应用已关闭")


app = FastAPI(title=settings.APP_NAME, version="2.5.0", lifespan=lifespan, default_response_class=MongoJSONResponse)


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    """注入 trace_id 到每个请求"""
    tid = request.headers.get("X-Trace-Id") or bind_trace_id()
    bind_trace_id(tid)
    response = await call_next(request)
    response.headers["X-Trace-Id"] = tid
    return response


@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError):
    """业务异常处理"""
    bind_trace_id(request.headers.get("X-Trace-Id"))
    logger.warning(f"业务异常: code={exc.code} msg={exc.message}")
    return MongoJSONResponse(
        status_code=HTTP_MAP.get(exc.code, 500),
        content=error(exc.code, exc.message, exc.data),
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    """未捕获异常兜底"""
    bind_trace_id(request.headers.get("X-Trace-Id"))
    logger.exception(f"未捕获异常: {exc}")
    return MongoJSONResponse(
        status_code=500,
        content=error(CODE.SERVER_ERROR, "服务器内部错误"),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


# 挂载业务路由（按 Phase 顺序逐步开放）
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
