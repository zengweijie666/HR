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
async def test_rewrite_direct_with_synonym_expand():
    """AC: direct 策略调用 LLM 做同义词扩展，返回 [原查询, 扩展查询]"""
    svc = StrategySelector()
    svc.llm = AsyncMock()
    # 模拟 LLM 对 "Java 5年" 的同义词扩展
    svc.llm.chat = AsyncMock(return_value="Java JVM Spring SpringBoot MyBatis 后端")
    rewrites = await svc.rewrite("Java 5年", "direct", [])
    assert rewrites[0] == "Java 5年"
    assert len(rewrites) == 2
    assert "Spring" in rewrites[1]


@pytest.mark.asyncio
async def test_rewrite_direct_llm_fail_fallback():
    """AC: direct 策略 LLM 失败时回退为 [原查询]"""
    svc = StrategySelector()
    svc.llm = AsyncMock()
    svc.llm.chat = AsyncMock(side_effect=Exception("LLM 不可用"))
    rewrites = await svc.rewrite("Java 5年", "direct", [])
    assert rewrites == ["Java 5年"]


@pytest.mark.asyncio
async def test_rewrite_direct_expand_same_as_query():
    """AC: 扩展结果与原查询相同时只返回 [原查询]，避免重复检索"""
    svc = StrategySelector()
    svc.llm = AsyncMock()
    svc.llm.chat = AsyncMock(return_value="Java 5年")
    rewrites = await svc.rewrite("Java 5年", "direct", [])
    assert rewrites == ["Java 5年"]


@pytest.mark.asyncio
async def test_rewrite_nlp_expands_to_bert_fasttext():
    """AC: NLP 查询应扩展出 BERT/FastText 等关联技术栈关键词

    业务场景: 简历库中候选人写了 BERT/FastText 但没写 NLP，
    搜索"NLP"必须能召回这些候选人，靠同义词扩展实现语义关联。
    """
    svc = StrategySelector()
    svc.llm = AsyncMock()
    # 模拟 LLM 对 "NLP" 的同义词扩展（应包含 BERT/FastText/Transformer 等）
    expanded_text = "NLP BERT GPT Transformer FastText Word2Vec TextCNN 自然语言处理 文本分类 命名实体识别"
    svc.llm.chat = AsyncMock(return_value=expanded_text)

    rewrites = await svc.rewrite("NLP", "direct", [])

    # 验证：原查询保留 + 扩展查询包含关联技术栈
    assert rewrites[0] == "NLP"
    assert len(rewrites) == 2
    expanded = rewrites[1]
    assert "BERT" in expanded
    assert "FastText" in expanded
    assert "自然语言处理" in expanded


@pytest.mark.asyncio
async def test_rewrite_nlp_triggers_multiple_retrievals():
    """AC: direct+扩展 后会触发多次 vector_store 检索，确保关联候选人被召回

    集成场景：search_service 会为 rewrites 中每个查询都调用一次 hybrid_search，
    所以扩展出的 "BERT FastText ..." 查询能独立检索到写 BERT 的候选人。
    """
    svc = StrategySelector()
    svc.llm = AsyncMock()
    svc.llm.chat = AsyncMock(return_value="NLP BERT FastText Transformer 自然语言处理")
    rewrites = await svc.rewrite("NLP", "direct", [])
    # 必须返回多个查询，search_service 才会做多查询检索
    assert len(rewrites) >= 2


@pytest.mark.asyncio
async def test_rewrite_hyde():
    """AC: hyde 策略调用 LLM 生成假设简历"""
    svc = StrategySelector()
    svc.llm = AsyncMock()
    svc.llm.chat = AsyncMock(return_value="5年Java后端开发经验")
    rewrites = await svc.rewrite("找个Java大佬", "hyde", [])
    assert len(rewrites) >= 1
    assert "Java" in rewrites[0]


@pytest.mark.asyncio
async def test_expand_synonyms_strips_markdown():
    """AC: _expand_synonyms 应去除 LLM 返回的 markdown 代码块包裹"""
    svc = StrategySelector()
    svc.llm = AsyncMock()
    svc.llm.chat = AsyncMock(return_value="```text\nNLP BERT FastText\n```")
    expanded = await svc._expand_synonyms("NLP")
    assert "```" not in expanded
    assert "BERT" in expanded


@pytest.mark.asyncio
async def test_expand_synonyms_failure_returns_empty():
    """AC: _expand_synonyms LLM 失败时返回空字符串，由调用方回退原查询"""
    svc = StrategySelector()
    svc.llm = AsyncMock()
    svc.llm.chat = AsyncMock(side_effect=Exception("网络错误"))
    expanded = await svc._expand_synonyms("NLP")
    assert expanded == ""
