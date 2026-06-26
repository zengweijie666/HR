"""
文件名: app/main.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: FastAPI 应用入口，负责路由挂载、启动事件、全局异常处理
"""
import json
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
    """生命周期：启动/关闭事件"""
    from app.core.database import MongoDB, RedisClient
    await MongoDB.connect()
    await RedisClient.connect()
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
