"""
文件名: tests/core/test_database.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试 MongoDB/Redis 连接管理
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.database import MongoDB, RedisClient


@pytest.mark.asyncio
async def test_mongodb_connect_creates_indexes(monkeypatch):
    """测试 MongoDB 连接并创建索引"""
    fake_db = AsyncMock()
    fake_client = MagicMock()
    fake_client.__getitem__ = MagicMock(return_value=fake_db)
    monkeypatch.setattr("app.core.database.AsyncIOMotorClient", lambda *a, **kw: fake_client)
    await MongoDB.connect()
    assert MongoDB.db is fake_db


@pytest.mark.asyncio
async def test_redis_get_client(monkeypatch):
    fake_pool = MagicMock()
    monkeypatch.setattr("app.core.database.redis.ConnectionPool.from_url", lambda *a, **kw: fake_pool)
    await RedisClient.connect()
    client = RedisClient.get_client()
    assert client is not None
