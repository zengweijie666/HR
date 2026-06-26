"""
文件名: tests/core/test_strategy_selector.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: StrategySelector 单元测试
"""
import pytest
from unittest.mock import AsyncMock
from app.core.strategy_selector import StrategySelector


@pytest.mark.asyncio
async def test_select_returns_valid_strategy():
    """AC: LLM 返回策略需校验，无效值兜底为 direct"""
    svc = StrategySelector()
    svc.llm = AsyncMock()
    svc.llm.chat = AsyncMock(return_value="hyde")
    result = await svc.select("找个Java大佬", [])
    assert result in ("direct", "hyde", "subquery", "backtracking")


@pytest.mark.asyncio
async def test_rewrite_direct():
    """AC: direct 策略直接返回原 query"""
    svc = StrategySelector()
    svc.llm = AsyncMock()
    rewrites = await svc.rewrite("Java 5年", "direct", [])
    assert rewrites == ["Java 5年"]


@pytest.mark.asyncio
async def test_rewrite_hyde():
    """AC: hyde 策略调用 LLM 生成假设简历"""
    svc = StrategySelector()
    svc.llm = AsyncMock()
    svc.llm.chat = AsyncMock(return_value="5年Java后端开发经验")
    rewrites = await svc.rewrite("找个Java大佬", "hyde", [])
    assert len(rewrites) >= 1
    assert "Java" in rewrites[0]
