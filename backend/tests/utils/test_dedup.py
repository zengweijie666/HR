"""
文件名: tests/utils/test_dedup.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试简历去重检查器
"""
from unittest.mock import AsyncMock
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
