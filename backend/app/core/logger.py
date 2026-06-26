"""
文件名: app/core/logger.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: loguru 日志配置，绑定 trace_id，对应 Business-Requirements 4.4 可观测性要求
"""
import sys
import uuid
from contextvars import ContextVar
from loguru import logger

_trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")


def bind_trace_id(trace_id: str | None = None) -> str:
    """绑定当前请求 trace_id"""
    tid = trace_id or f"trace_{uuid.uuid4().hex[:16]}"
    _trace_id_ctx.set(tid)
    return tid


def get_trace_id() -> str:
    """获取当前 trace_id，未设置则自动生成"""
    tid = _trace_id_ctx.get()
    if not tid:
        tid = bind_trace_id()
    return tid


# 配置 loguru 输出格式
logger.remove()
logger.configure(patcher=lambda record: record["extra"].update(trace_id=get_trace_id()))
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | trace_id={extra[trace_id]} | {message}",
    level="INFO",
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | trace_id={extra[trace_id]} | {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
)

__all__ = ["logger", "bind_trace_id", "get_trace_id"]
