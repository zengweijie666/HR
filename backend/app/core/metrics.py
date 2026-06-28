"""
文件名: app/core/metrics.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: Prometheus 指标定义与收集中间件
    - HTTP 请求总量、耗时分布、在途请求
    - 业务指标：简历解析、LLM调用、向量检索
    - 提供 /metrics 端点供 Prometheus 抓取
"""
import time
from typing import Callable, Awaitable

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method"],
)

RESUME_PARSE_TOTAL = Counter(
    "resume_parse_total",
    "Total resume parse attempts",
    ["status"],
)

RESUME_PARSE_DURATION = Histogram(
    "resume_parse_duration_seconds",
    "Resume parse duration in seconds",
    buckets=(1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0),
)

LLM_CALLS_TOTAL = Counter(
    "llm_calls_total",
    "Total LLM API calls",
    ["model", "status"],
)

LLM_CALL_DURATION = Histogram(
    "llm_call_duration_seconds",
    "LLM API call duration",
    ["model"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0),
)

LLM_TOKEN_USAGE = Counter(
    "llm_token_usage_total",
    "Total LLM token usage",
    ["model", "type"],
)

VECTOR_SEARCH_TOTAL = Counter(
    "vector_search_total",
    "Total vector search requests",
    ["type"],
)

VECTOR_SEARCH_DURATION = Histogram(
    "vector_search_duration_seconds",
    "Vector search duration",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

MINIO_OPERATIONS_TOTAL = Counter(
    "minio_operations_total",
    "Total MinIO object operations",
    ["operation", "status"],
)


def _normalize_path(path: str) -> str:
    """将带ID的路径归一化为模板形式，避免指标爆炸"""
    if not path:
        return path
    parts = path.rstrip("/").split("/")
    normalized = []
    for p in parts:
        if len(p) == 24 and all(c in "0123456789abcdef" for c in p.lower()):
            normalized.append("{id}")
        elif p.startswith("r_") or p.startswith("u_") or p.startswith("c_") or p.startswith("s_"):
            if len(p) > 10:
                normalized.append("{id}")
            else:
                normalized.append(p)
        else:
            normalized.append(p)
    result = "/".join(normalized)
    return result or "/"


async def metrics_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Prometheus 指标收集中间件"""
    method = request.method
    raw_path = request.url.path

    if raw_path in ("/metrics", "/health"):
        return await call_next(request)

    normalized_path = _normalize_path(raw_path)

    HTTP_REQUESTS_IN_PROGRESS.labels(method=method).inc()
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        status_code = 500
        raise
    finally:
        elapsed = time.perf_counter() - start
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method).dec()
        HTTP_REQUESTS_TOTAL.labels(
            method=method, path=normalized_path, status_code=str(status_code)
        ).inc()
        HTTP_REQUEST_DURATION.labels(method=method, path=normalized_path).observe(elapsed)


async def metrics_endpoint(request: Request) -> Response:
    """Prometheus /metrics 端点"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def setup_metrics(app: FastAPI) -> None:
    """将指标中间件和 /metrics 端点挂载到 FastAPI 应用"""
    app.middleware("http")(metrics_middleware)
    app.add_route("/metrics", metrics_endpoint, methods=["GET"])
    app.add_route("/api/metrics", metrics_endpoint, methods=["GET"])
