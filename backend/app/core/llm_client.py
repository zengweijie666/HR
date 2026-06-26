"""
文件名: app/core/llm_client.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: AsyncOpenAI + tenacity 重试，对应 Backend-Design.md 3.6
入参: messages 列表
出参: 文本内容 / token 流
"""
from typing import AsyncGenerator
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import LLMError


class LLMClient:
    """LLM 异步客户端"""

    def __init__(self):
        self._client = None

    @property
    def client(self) -> AsyncOpenAI:
        """延迟初始化 AsyncOpenAI"""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL
            )
        return self._client

    @client.setter
    def client(self, value):
        """测试注入用"""
        self._client = value

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def chat(self, messages: list[dict], **kwargs) -> str:
        """非流式调用，失败自动重试 3 次

        入参:
            messages: OpenAI 消息列表
            **kwargs: 透传给 OpenAI 的额外参数
        出参:
            模型返回的文本内容
        异常:
            LLMError: 重试耗尽后抛出
        """
        try:
            resp = await self.client.chat.completions.create(
                model=settings.LLM_MODEL, messages=messages, stream=False, **kwargs
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise LLMError(f"LLM 调用失败: {e}")

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        """流式生成，yield token

        入参:
            messages: OpenAI 消息列表
            **kwargs: 透传给 OpenAI 的额外参数
        出参:
            异步生成器，逐 token 返回文本
        异常:
            LLMError: 流式调用失败时抛出
        """
        try:
            stream = await self.client.chat.completions.create(
                model=settings.LLM_MODEL, messages=messages, stream=True, **kwargs
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            logger.error(f"LLM 流式调用失败: {e}")
            raise LLMError(f"LLM 流式调用失败: {e}")


llm_client = LLMClient()
