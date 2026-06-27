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
import re
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
        """选择策略：优先规则快速判断，LLM 兜底

        入参:
            query: 用户查询
            history: 对话历史
        出参:
            策略名（direct/hyde/subquery/backtracking）
        规则:
            - 含历史指代（"他/那个/刚说的/刚才"）→ backtracking
            - 含多个技能/条件关键词（且/并且/同时/和 连接 ≥3 个关键词）→ subquery
            - 短查询（≤10字）且含明确岗位/技能词 → direct
            - 短查询但模糊描述（"大佬/高手/厉害的/大牛/好的"）→ hyde
            - 其他情况交给 LLM 判断
        """
        q = query.strip()

        # 规则1：指代消解（需要历史）
        if history and re.search(r'(他|她|那个|这位|刚说|刚才|之前|上面)', q):
            return "backtracking"

        # 规则2：多条件查询（含多个"且/并且/和/同时"或逗号分隔的多个条件）
        condition_count = len(re.findall(r'(且|并且|同时|还要|加上|另外)', q))
        comma_conditions = len([s for s in re.split(r'[，,、]', q) if s.strip()])
        if condition_count >= 2 or (comma_conditions >= 3 and len(q) > 10):
            return "subquery"

        # 规则3：模糊描述词 → hyde
        if re.search(r'(大佬|高手|大牛|厉害|牛人|专家|资深的|好的|优秀的|强的)', q):
            return "hyde"

        # 规则4：短查询（≤20字）且含明确技能/岗位关键词 → direct
        # 先去掉常见动词前缀和数量词，提取核心
        core_q = q
        verb_prefixes = [
            r'^(我要|要|找|给我找|帮我找|推荐|帮我推荐|给我推荐|需要|想要|有没有|有)',
        ]
        for vp in verb_prefixes:
            core_q = re.sub(vp, '', core_q, count=1)
        # 去掉数量词（两名、2个、3位、几个等）
        core_q = re.sub(r'^[0-9一二两三四五六七八九十]+[名个位点]+', '', core_q)
        core_q = core_q.strip()

        if len(q) <= 20 and core_q:
            # 检查是否包含明确的岗位/技能词
            direct_keywords = [
                '工程师', '开发', '经理', '主管', '总监', '产品', '设计', '运营',
                'java', 'python', 'go', 'c++', '前端', '后端', '全栈', '测试',
                'nlp', 'cv', '算法', '数据', 'ai', 'ml', 'dl', '大模型',
                'pmp', '运维', 'devops', 'dba', '架构师', '自然语言处理',
                '机器学习', '深度学习', '数据分析', '产品经理', 'ui', 'ue',
            ]
            q_lower = q.lower()
            core_lower = core_q.lower()
            if any(kw in q_lower or kw in core_lower for kw in direct_keywords):
                return "direct"

        # LLM 判断兜底
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
            # HYDE：原查询 + 关键词扩展查询（不生成长篇简历，长文本向量稀释严重）
            prompt = HYDE_PROMPT.format(query=query)
            try:
                result = await self.llm.chat([{"role": "user", "content": prompt}])
                expanded = result.strip()
                # 返回 [原查询, 关键词扩展查询]；扩展结果去 markdown 包裹
                if expanded.startswith("```"):
                    expanded = re.sub(r'^```\w*\n?', '', expanded)
                    expanded = re.sub(r'\n?```$', '', expanded)
                queries = [query]
                if expanded and expanded != query:
                    queries.append(expanded)
                return queries
            except Exception as e:
                logger.warning(f"HYDE 改写失败，回退原查询: {e}")
                return [query]
        if strategy == "subquery":
            prompt = SUBQUERY_PROMPT.format(query=query)
            try:
                result = await self.llm.chat([{"role": "user", "content": prompt}])
                parsed = json.loads(result)
                if isinstance(parsed, list) and parsed:
                    # 始终保留原查询，加上子查询
                    queries = [query] + [str(x) for x in parsed if str(x).strip() and str(x) != query]
                    return queries[:5]  # 最多 5 个查询，避免检索过多
            except Exception as e:
                logger.warning(f"subquery 解析失败，回退原查询: {e}")
            return [query]
        if strategy == "backtracking":
            prompt = BACKTRACKING_PROMPT.format(query=query, history=str(history[-3:]))
            try:
                result = await self.llm.chat([{"role": "user", "content": prompt}])
                simplified = result.strip()
                if simplified and simplified != query:
                    return [simplified, query]
            except Exception as e:
                logger.warning(f"backtracking 改写失败，回退原查询: {e}")
            return [query]
        return [query]


strategy_selector = StrategySelector()
