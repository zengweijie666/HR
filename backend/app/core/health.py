"""
文件名: app/core/health.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 深度健康检查，验证各依赖服务连通性
    - /health        简单存活探测（liveness），用于负载均衡
    - /health/ready  就绪探测（readiness），检查所有依赖连通（带超时）
"""
import asyncio
import time
from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.logger import logger

router = APIRouter()


async def _with_timeout(coro, timeout_sec: float = 3.0):
    """带超时保护地执行协程，避免单个依赖卡住整个健康检查"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_sec)
    except asyncio.TimeoutError:
        return None
    except Exception:
        raise


async def _check_mongo() -> dict[str, Any]:
    try:
        from app.core.database import MongoDB
        if MongoDB.db is None:
            return {"name": "mongodb", "status": "down", "detail": "not connected"}
        t0 = time.perf_counter()
        await MongoDB.db.command("ping")
        return {"name": "mongodb", "status": "up", "latency_ms": int((time.perf_counter() - t0) * 1000)}
    except Exception as e:
        logger.warning(f"健康检查 MongoDB 失败: {e}")
        return {"name": "mongodb", "status": "down", "detail": str(e)[:200]}


async def _check_redis() -> dict[str, Any]:
    try:
        from app.core.database import RedisClient
        if RedisClient.pool is None:
            return {"name": "redis", "status": "down", "detail": "not connected"}
        t0 = time.perf_counter()
        client = RedisClient.get_client()
        await client.ping()
        return {"name": "redis", "status": "up", "latency_ms": int((time.perf_counter() - t0) * 1000)}
    except Exception as e:
        logger.warning(f"健康检查 Redis 失败: {e}")
        return {"name": "redis", "status": "down", "detail": str(e)[:200]}


async def _check_minio() -> dict[str, Any]:
    try:
        from app.core.minio_client import minio_client
        client = minio_client.client
        t0 = time.perf_counter()
        found = await asyncio.wait_for(
            asyncio.to_thread(client.bucket_exists, "resumes"),
            timeout=3.0,
        )
        return {
            "name": "minio",
            "status": "up",
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "bucket_exists": found,
        }
    except asyncio.TimeoutError:
        return {"name": "minio", "status": "down", "detail": "connection timeout (3s)"}
    except Exception as e:
        logger.warning(f"健康检查 MinIO 失败: {e}")
        return {"name": "minio", "status": "down", "detail": str(e)[:200]}


async def _check_milvus() -> dict[str, Any]:
    try:
        from pymilvus import utility
        t0 = time.perf_counter()
        cols = await asyncio.wait_for(
            asyncio.to_thread(utility.list_collections),
            timeout=3.0,
        )
        return {
            "name": "milvus",
            "status": "up",
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "collections": len(cols) if isinstance(cols, list) else 0,
        }
    except asyncio.TimeoutError:
        return {"name": "milvus", "status": "down", "detail": "connection timeout (3s)"}
    except Exception as e:
        logger.warning(f"健康检查 Milvus 失败: {e}")
        return {"name": "milvus", "status": "down", "detail": str(e)[:200]}


@router.get("/health")
async def liveness() -> dict[str, Any]:
    return {"status": "ok", "service": "talentsense-backend"}


@router.get("/health/ready")
async def readiness() -> dict[str, Any]:
    mongo_res, redis_res, minio_res, milvus_res = await asyncio.gather(
        _check_mongo(),
        _check_redis(),
        _check_minio(),
        _check_milvus(),
        return_exceptions=False,
    )
    checks = [mongo_res, redis_res, minio_res, milvus_res]
    critical = {"mongodb", "redis"}
    all_up = all(c["status"] == "up" for c in checks)
    critical_up = all(c["status"] == "up" for c in checks if c["name"] in critical)

    if not critical_up:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "degraded",
                "checks": checks,
                "all_healthy": all_up,
            },
        )

    return {
        "status": "up" if all_up else "degraded",
        "checks": checks,
        "all_healthy": all_up,
    }
