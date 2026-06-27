"""
文件名: app/core/response.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 统一响应封装 {code, message, data, trace_id}，对应 API-Design.md 0.1/0.2
"""
import uuid
from typing import Any


class CODE:
    """业务状态码常量，对应 API-Design.md 0.2"""
    SUCCESS = 0
    PARAM_ERROR = 1001
    UNAUTHORIZED = 1002
    FORBIDDEN = 1003
    NOT_FOUND = 1004
    CONFLICT = 1005
    AUTH_PENDING = 1006       # 账号待审批
    AUTH_DISABLED = 1007      # 账号已禁用
    RESUME_PARSE_FAILED = 2001
    LLM_FAILED = 2002
    VECTOR_SEARCH_FAILED = 2003
    EMAIL_FAILED = 2004
    SERVER_ERROR = 5000


HTTP_MAP = {
    CODE.SUCCESS: 200,
    CODE.PARAM_ERROR: 400,
    CODE.UNAUTHORIZED: 401,
    CODE.FORBIDDEN: 403,
    CODE.NOT_FOUND: 404,
    CODE.CONFLICT: 409,
    CODE.AUTH_PENDING: 403,
    CODE.AUTH_DISABLED: 403,
    CODE.RESUME_PARSE_FAILED: 422,
    CODE.LLM_FAILED: 422,
    CODE.VECTOR_SEARCH_FAILED: 422,
    CODE.EMAIL_FAILED: 422,
    CODE.SERVER_ERROR: 500,
}


def _trace_id() -> str:
    return f"trace_{uuid.uuid4().hex[:16]}"


def success(data: Any = None, message: str = "success") -> dict:
    """成功响应"""
    return {"code": CODE.SUCCESS, "message": message, "data": data, "trace_id": _trace_id()}


def error(code: int, message: str, data: Any = None) -> dict:
    """失败响应"""
    return {"code": code, "message": message, "data": data, "trace_id": _trace_id()}
