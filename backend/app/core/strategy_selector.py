"""
文件名: app/core/strategy_selector.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: Query 改写策略选择器（复用 EduRAG），4 种策略
入参: query, history
出参: 策略名 / 改写后的 query 列表
对应 Business-Requirements F13
"""
import json
from app.core.llm_client import llm_client
from app.agent.prompts import (
    STRATEGY_SELECT_PROMPT,
    HYDE_PROMPT,
    SUBQUERY_PROMPT,
    BACKTRACKING_PROMPT,
)
from app.core.logger import logger


class StrategySelector:
    """Query 改写策略选择器

    支持 4 种策略：
    - direct: 原样返回
    - hyde: 假设文档检索
    - subquery: 复杂查询拆解
    - backtracking: 历史指代简化
    """

    def __init__(self):
        self.llm = llm_client

    async def select(self, query: str, history: list[dict]) -> str:
        """LLM 选择策略

        入参:
            query: 用户查询
            history: 对话历史
        出参:
            策略名（direct/hyde/subquery/backtracking），无效时兜底为 direct
        """
        prompt = STRATEGY_SELECT_PROMPT.format(query=query, history=str(history[-5:]))
        try:
            result = await self.llm.chat([{"role": "user", "content": prompt}])
            strategy = result.strip().lower()
            if strategy not in ("direct", "hyde", "subquery", "backtracking"):
                strategy = "direct"
            return strategy
        except Exception as e:
            logger.warning(f"策略选择失败，兜底 direct: {e}")
            return "direct"

    async def rewrite(self, query: str, strategy: str, history: list[dict]) -> list[str]:
        """根据策略改写 query

        入参:
            query: 原始查询
            strategy: 策略名
            history: 对话历史
        出参:
            改写后的 query 列表
        """
        if strategy == "direct":
            return [query]
        if strategy == "hyde":
            prompt = HYDE_PROMPT.format(query=query)
            result = await self.llm.chat([{"role": "user", "content": prompt}])
            return [result]
        if strategy == "subquery":
            prompt = SUBQUERY_PROMPT.format(query=query)
            result = await self.llm.chat([{"role": "user", "content": prompt}])
            try:
                parsed = json.loads(result)
                if isinstance(parsed, list) and parsed:
                    return [str(x) for x in parsed]
            except Exception as e:
                logger.warning(f"subquery 解析失败，回退原查询: {e}")
            return [query]
        if strategy == "backtracking":
            prompt = BACKTRACKING_PROMPT.format(query=query, history=str(history[-3:]))
            result = await self.llm.chat([{"role": "user", "content": prompt}])
            return [result]
        return [query]


strategy_selector = StrategySelector()
