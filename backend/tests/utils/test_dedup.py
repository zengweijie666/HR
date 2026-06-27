"""
文件名: tests/utils/test_dedup.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试简历去重检查器
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.utils.dedup import DedupChecker


@pytest.mark.asyncio
async def test_no_duplicate():
    coll = AsyncMock()
    coll.find_one.return_value = None
    checker = DedupChecker(coll)
    result = await checker.check("h1", "h2")
    assert result is None


@pytest.mark.asyncio
async def test_duplicate_by_phone():
    coll = AsyncMock()
    coll.find_one.return_value = {"resume_id": "res_existing"}
    checker = DedupChecker(coll)
    result = await checker.check("h1", "h2")
    assert result == "res_existing"


@pytest.mark.asyncio
async def test_dedup_checks_basic_info_path():
    """去重应查询 basic_info.phone_hash / basic_info.email_hash 路径"""
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=None)
    checker = DedupChecker(coll)
    await checker.check("hash_p", "hash_e")
    call_args = coll.find_one.call_args
    query = call_args.args[0]
    # 必须查 basic_info.phone_hash 而非顶层 phone_hash
    assert "basic_info.phone_hash" in str(query) or "basic_info.email_hash" in str(query)


@pytest.mark.asyncio
async def test_dedup_empty_hashes_returns_none():
    """phone_hash 和 email_hash 均为空时应返回 None"""
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=None)
    checker = DedupChecker(coll)
    result = await checker.check("", "")
    assert result is None
    coll.find_one.assert_not_called()
