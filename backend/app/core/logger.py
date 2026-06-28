"""
文件名: app/core/logger.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: loguru 日志配置，支持结构化JSON输出与trace_id链路追踪
    - DEBUG/开发环境：人类可读彩色格式输出到控制台
    - 生产/非DEBUG环境：JSON结构化日志输出（便于Loki/ELK采集）
    - 文件日志：按大小轮转，保留7天，始终使用可读格式便于本地排查
"""
import json
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime

from loguru import logger

from app.core.config import settings

_trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")
_user_id_ctx: ContextVar[str] = ContextVar("user_id", default="")
_request_path_ctx: ContextVar[str] = ContextVar("request_path", default="")
_client_ip_ctx: ContextVar[str] = ContextVar("client_ip", default="")


def bind_trace_id(trace_id: str | None = None) -> str:
    tid = trace_id or f"trace_{uuid.uuid4().hex[:16]}"
    _trace_id_ctx.set(tid)
    return tid


def bind_request_context(user_id: str = "", path: str = "", client_ip: str = "") -> None:
    if user_id:
        _user_id_ctx.set(user_id)
    if path:
        _request_path_ctx.set(path)
    if client_ip:
        _client_ip_ctx.set(client_ip)


def clear_request_context() -> None:
    _trace_id_ctx.set("")
    _user_id_ctx.set("")
    _request_path_ctx.set("")
    _client_ip_ctx.set("")


def get_trace_id() -> str:
    tid = _trace_id_ctx.get()
    if not tid:
        tid = bind_trace_id()
    return tid


class JsonSink:
    """JSON 结构化日志序列化器，生产环境使用"""

    def __call__(self, message):
        record = message.record
        payload = {
            "ts": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record["level"].name,
            "trace_id": _trace_id_ctx.get() or record["extra"].get("trace_id", ""),
            "user_id": _user_id_ctx.get() or record["extra"].get("user_id", ""),
            "path": _request_path_ctx.get() or record["extra"].get("path", ""),
            "client_ip": _client_ip_ctx.get() or record["extra"].get("client_ip", ""),
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
            "msg": record["message"],
        }
        if record["extra"]:
            extra_clean = {k: v for k, v in record["extra"].items() if k not in ("trace_id", "user_id", "path", "client_ip")}
            if extra_clean:
                payload["extra"] = self._safe_serialize(extra_clean)
        if record["exception"] is not None:
            payload["exception"] = {
                "type": record["exception"].type.__name__ if record["exception"].type else "",
                "msg": str(record["exception"].value) if record["exception"].value else "",
            }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        sys.stdout.flush()

    @staticmethod
    def _safe_serialize(obj):
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)


logger.remove()

_patcher = lambda record: record["extra"].setdefault("trace_id", _trace_id_ctx.get())
logger.configure(patcher=_patcher)

if settings.DEBUG:
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>trace_id={extra[trace_id]}</cyan> | <cyan>{name}:{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True,
        backtrace=False,
        diagnose=False,
    )
else:
    logger.add(
        JsonSink(),
        level="INFO",
        backtrace=False,
        diagnose=False,
        serialize=False,
    )

logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | trace_id={extra[trace_id]} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
    enqueue=True,
)

__all__ = [
    "logger",
    "bind_trace_id",
    "get_trace_id",
    "bind_request_context",
    "clear_request_context",
]
