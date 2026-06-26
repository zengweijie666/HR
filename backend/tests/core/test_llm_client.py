"""
文件名: tests/core/test_llm_client.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: LLM 客户端单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.llm_client import LLMClient


@pytest.mark.asyncio
async def test_chat_returns_content():
    """非流式调用应返回 message.content"""
    with patch("app.core.llm_client.AsyncOpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        msg = MagicMock()
        msg.choices = [MagicMock(message=MagicMock(content="hello"))]
        instance.chat.completions.create = AsyncMock(return_value=msg)
        client = LLMClient()
        client.client = instance
        result = await client.chat([{"role": "user", "content": "hi"}])
        assert result == "hello"


@pytest.mark.asyncio
async def test_chat_retries_on_failure():
    """tenacity 应至少重试 3 次"""
    with patch("app.core.llm_client.AsyncOpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value
        instance.chat.completions.create = AsyncMock(side_effect=Exception("LLM down"))
        client = LLMClient()
        client.client = instance
        from app.core.exceptions import LLMError
        with pytest.raises(LLMError):
            await client.chat([{"role": "user", "content": "hi"}])
        # 至少调用 3 次
        assert instance.chat.completions.create.call_count >= 3


@pytest.mark.asyncio
async def test_chat_stream_yields_tokens():
    """流式调用应逐 token yield"""
    with patch("app.core.llm_client.AsyncOpenAI") as MockOpenAI:
        instance = MockOpenAI.return_value

        async def fake_stream():
            yield MagicMock(choices=[MagicMock(delta=MagicMock(content="tok1"))])
            yield MagicMock(choices=[MagicMock(delta=MagicMock(content="tok2"))])

        instance.chat.completions.create = AsyncMock(return_value=fake_stream())
        client = LLMClient()
        client.client = instance
        tokens = []
        async for t in client.chat_stream([{"role": "user", "content": "hi"}]):
            tokens.append(t)
        assert tokens == ["tok1", "tok2"]
