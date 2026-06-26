"""
文件名: tests/core/test_logger.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试日志与 trace_id 上下文
"""
import logging
from app.core.logger import logger, bind_trace_id, get_trace_id


def test_logger_exists():
    assert logger is not None


def test_bind_trace_id():
    tid = bind_trace_id("trace_abc")
    assert get_trace_id() == "trace_abc"


def test_get_trace_id_auto():
    bind_trace_id(None)
    tid = get_trace_id()
    assert tid.startswith("trace_")
