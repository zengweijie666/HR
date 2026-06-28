"""
文件名: app/api/monitor.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 前端监控上报接口
    - POST /api/v1/monitor/error  前端JS错误上报
    - POST /api/v1/monitor/perm   前端性能指标上报
"""
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, Field

from app.core.database import MongoDB
from app.core.logger import logger
from app.core.response import success

router = APIRouter()


class FrontendError(BaseModel):
    message: str
    stack: Optional[str] = ""
    url: Optional[str] = ""
    line: Optional[int] = 0
    col: Optional[int] = 0
    filename: Optional[str] = ""
    error_type: Optional[str] = "js_error"
    user_agent: Optional[str] = ""
    extra: Optional[dict[str, Any]] = Field(default_factory=dict)


class FrontendPerf(BaseModel):
    metric: str
    value: float
    url: Optional[str] = ""
    extra: Optional[dict[str, Any]] = Field(default_factory=dict)


def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


async def _try_get_user(authorization: str | None) -> dict | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        from app.services.auth_service import AuthService
        return await AuthService().verify_token(authorization[7:])
    except Exception:
        return None


@router.post("/error")
async def report_error(
    payload: FrontendError,
    request: Request,
    authorization: str | None = Header(default=None),
):
    """前端JS错误上报，异步写入MongoDB，避免阻塞"""
    user = await _try_get_user(authorization)
    doc = {
        "error_type": payload.error_type,
        "message": payload.message[:500],
        "stack": payload.stack[:2000] if payload.stack else "",
        "url": payload.url[:500],
        "line": payload.line,
        "col": payload.col,
        "filename": payload.filename[:200],
        "user_agent": payload.user_agent[:300] or request.headers.get("user-agent", ""),
        "client_ip": _get_client_ip(request),
        "user_id": user.get("user_id") if user else "",
        "username": user.get("username") if user else "",
        "extra": payload.extra or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.bind(
        user_id=doc["user_id"],
        client_ip=doc["client_ip"],
        error_type=doc["error_type"],
    ).error(f"前端错误: {doc['message']} url={doc['url']}")
    try:
        if MongoDB.db is not None:
            await MongoDB.db.frontend_errors.insert_one(doc)
    except Exception as e:
        logger.warning(f"前端错误落库失败: {e}")
    return success()


@router.post("/perf")
async def report_perf(
    payload: FrontendPerf,
    request: Request,
    authorization: str | None = Header(default=None),
):
    """前端性能指标上报（FP/FCP/LCP/接口耗时等），仅写日志不入库避免膨胀"""
    user = await _try_get_user(authorization)
    logger.bind(
        user_id=user.get("user_id") if user else "",
        metric=payload.metric,
        value=payload.value,
        url=payload.url,
    ).info(f"前端性能: {payload.metric}={payload.value} url={payload.url}")
    return success()
