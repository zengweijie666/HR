"""
文件名: tests/core/test_cache.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: Redis 缓存装饰器单元测试
"""
import pytest
from unittest.mock import AsyncMock
from app.core.cache import cached


@pytest.mark.asyncio
async def test_cached_hit():
    """AC: 缓存命中直接返回，不调用原函数"""
    redis = AsyncMock()
    redis.get.return_value = '{"x":1}'

    @cached(redis, prefix="test", ttl=60, key_args=["q"])
    async def fn(q: str):
        return {"x": 1}

    result = await fn(q="a")
    assert result == {"x": 1}
    redis.get.assert_called_once()


@pytest.mark.asyncio
async def test_cached_miss():
    """AC: 缓存未命中调用原函数并写入缓存"""
    redis = AsyncMock()
    redis.get.return_value = None
    redis.setex = AsyncMock()

    @cached(redis, prefix="test", ttl=60, key_args=["q"])
    async def fn(q: str):
        return {"y": 2}

    result = await fn(q="a")
    assert result == {"y": 2}
    redis.setex.assert_called_once()
