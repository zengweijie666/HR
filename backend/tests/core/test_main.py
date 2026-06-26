"""
文件名: tests/core/test_main.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试 main.py 健康检查与全局异常处理
"""
from fastapi.testclient import TestClient
from app.main import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_biz_error_handler():
    """BizError 应转换为标准响应"""
    from app.core.exceptions import ParamError
    from fastapi import APIRouter
    test_router = APIRouter()

    @test_router.get("/_test/param-error")
    async def _raise():
        raise ParamError("test msg")

    app.include_router(test_router, prefix="/api/v1")
    client = TestClient(app)
    r = client.get("/api/v1/_test/param-error")
    body = r.json()
    assert r.status_code == 400
    assert body["code"] == 1001
    assert body["message"] == "test msg"
    assert "trace_id" in body


def test_unhandled_exception_handler():
    """未捕获异常返回 5000"""
    from fastapi import APIRouter
    test_router = APIRouter()

    @test_router.get("/_test/server-error")
    async def _raise():
        raise RuntimeError("boom")

    app.include_router(test_router, prefix="/api/v1")
    # ServerErrorMiddleware 总是会重新抛出异常；禁用 raise_server_exceptions
    # 以便自定义的 Exception 处理程序返回 500 响应。
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/api/v1/_test/server-error")
    body = r.json()
    assert r.status_code == 500
    assert body["code"] == 5000
