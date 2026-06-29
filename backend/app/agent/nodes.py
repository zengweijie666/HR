"""
文件名: app/agent/nodes.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: LangGraph 5 节点实现（<300行），每节点输入/输出 AgentState
入参: AgentState
出参: 更新后的 AgentState（部分字段）
对应 Business-Requirements F11/F12
"""
import re
import json
from app.agent.state import AgentState
from app.agent.prompts import (
    INTENT_PROMPT,
    CHITCHAT_PROMPT,
    CLARIFY_PROMPT,
    SEARCH_RESPOND_PROMPT,
    FILTER_EXTRACT_PROMPT,
)
from app.core.llm_client import llm_client
from app.core.logger import logger
from app.services.search_service import SearchService
from app.services.resume_service import ResumeService

# 模块级单例，便于测试 patch
search_service = SearchService()
resume_service = ResumeService()


def _regex_extract_filters(query: str) -> dict:
    """正则兜底提取硬过滤条件，避免LLM调用失败时条件丢失

    入参:
        query: 用户自然语言查询
    出参:
        {"education_min": int|None, "work_years_min": int|None, "salary_max": int|None, "required_skills": list[str]}
    """
    filters = {}

    # 学历
    if re.search(r'博士', query):
        filters["education_min"] = 3
    elif re.search(r'硕士|研究生', query):
        filters["education_min"] = 2
    elif re.search(r'本科|学士', query):
        filters["education_min"] = 1
    elif re.search(r'专科|大专|高职', query):
        filters["education_min"] = 0

    # 工作年限：X年以上/X年经验
    years_match = re.search(r'(\d+)\s*年(以上|及以上|经验|工作经验)', query)
    if years_match:
        filters["work_years_min"] = int(years_match.group(1))
    elif re.search(r'应届|应届生|毕业生|无经验', query):
        filters["work_years_min"] = 0

    # 薪资：XK以内/Xk以下/XK及以下/不超过XK/薪资XK以内
    sal_match = re.search(r'(?:薪资|薪水|工资|期望)?\s*(\d+)\s*[Kk千](?:以内|以下|及以下|之内|以下)', query)
    if sal_match:
        filters["salary_max"] = int(sal_match.group(1))
    # 另一种：不超过XK
    sal_match2 = re.search(r'不超过\s*(\d+)\s*[Kk千]', query)
    if sal_match2 and "salary_max" not in filters:
        filters["salary_max"] = int(sal_match2.group(1))

    # 技能关键词提取：匹配"会X的"/"懂X的"/"有X经验的"/"X工程师"
    skills_set: set[str] = set()
    skill_patterns = [
        r'(?:会|懂|熟悉|精通|掌握|了解)\s*([A-Za-z0-9+#]+(?:[A-Za-z0-9+#.]+)*)',
        r'有\s*([A-Za-z0-9+#]+)\s*(?:项目|开发|实战)?经验',
        r'([A-Za-z0-9+#]+)\s*(?:工程师|开发|程序员|专家)',
    ]
    for pattern in skill_patterns:
        for m in re.finditer(pattern, query):
            raw = m.group(1).strip().lower()
            # 过滤掉非技能词（如"的"、"工程师"等）
            if len(raw) >= 2 and raw not in ("的", "有", "会", "懂"):
                skills_set.add(raw)
    if skills_set:
        filters["required_skills"] = list(skills_set)

    return filters


async def filter_extract_node(state: AgentState) -> dict:
    """节点1.5: 从自然语言query中提取硬过滤条件

    在intent_node之后、retrieve_rank_node之前执行。
    合并前端显式传入的filters和LLM/正则提取的filters（提取的优先覆盖）。
    仅对search意图生效；其他意图不修改filters。

    入参:
        state: AgentState（需含 query / filters）
    出参:
        {"filters": {...}}
    """
    intent_type = state.get("intent_type", "search")
    # 非搜索意图不需要提取filters
    if intent_type not in ("search", None):
        return {"filters": state.get("filters", {})}

    query = state.get("query", "")
    if not query:
        return {"filters": state.get("filters", {})}

    # 先正则兜底
    regex_filters = _regex_extract_filters(query)
    merged = dict(state.get("filters", {}) or {})
    merged.update(regex_filters)

    # 再LLM精细提取
    try:
        prompt = FILTER_EXTRACT_PROMPT.format(query=query)
        resp = await llm_client.chat(
            [{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.strip())
        for key in ("education_min", "work_years_min", "salary_max"):
            val = data.get(key)
            if val is not None:
                try:
                    merged[key] = int(val)
                except (TypeError, ValueError):
                    pass
        # 提取required_skills
        llm_skills = data.get("required_skills", [])
        if isinstance(llm_skills, list) and llm_skills:
            existing = set(merged.get("required_skills", []) or [])
            for s in llm_skills:
                if isinstance(s, str) and s.strip():
                    existing.add(s.strip().lower())
            merged["required_skills"] = list(existing)
        logger.info(f"过滤条件提取: query='{query}' → filters={merged}")
    except Exception as e:
        logger.warning(f"LLM filter提取失败，使用正则兜底: {e}, regex_filters={regex_filters}")

    return {"filters": merged}


async def intent_node(state: AgentState) -> dict:
    """节点1: 意图识别

    入参:
        state: AgentState（需含 query / history）
    出参:
        {"intent": "chitchat"|"search"|"detail"|"compare"|"qa"}
    """
    prompt = INTENT_PROMPT.format(
        query=state["query"], history=str(state.get("history", [])[-5:])
    )
    try:
        result = await llm_client.chat([{"role": "user", "content": prompt}])
        intent = result.strip().lower()
        if intent not in ("chitchat", "search", "detail", "compare", "qa"):
            intent = "qa"  # 兜底改为 qa，让兜底也能通用回答
    except Exception as e:
        logger.warning(f"意图识别失败，兜底 qa: {e}")
        intent = "qa"
    logger.info(f"意图识别: {intent}")
    return {"intent_type": intent}


async def retrieve_rank_node(state: AgentState) -> dict:
    """节点2: 检索+精排

    入参:
        state: AgentState（需含 query / filters / history）
    出参:
        {"candidates": [...]}
    """
    try:
        candidates = await search_service.search(
            query=state["query"],
            filters=state.get("filters", {}),
            top_k=20,
            history=state.get("history", []),
        )
    except Exception as e:
        logger.error(f"检索失败: {e}", exc_info=True)
        candidates = []
    return {"candidates": candidates}


async def clarify_node(state: AgentState) -> dict:
    """节点3: 澄清（候选人为空或信息不足时引导）

    入参:
        state: AgentState
    出参:
        有结果返回 {}；无结果返回 {"response": "..."}
    """
    if state.get("candidates"):
        return {}
    prompt = CLARIFY_PROMPT.format(query=state["query"])
    try:
        resp = await llm_client.chat([{"role": "user", "content": prompt}])
    except Exception as e:
        logger.warning(f"澄清生成失败: {e}")
        resp = "抱歉没找到合适的候选人，能否提供更多细节（如技术栈、年限）？"
    return {"response": resp}


async def detail_node(state: AgentState) -> dict:
    """节点4: 详情查询

    入参:
        state: AgentState（intent_type=detail 时生效）
    出参:
        {"detail": {...}} 或 {}
    """
    if state.get("intent_type") != "detail":
        return {}
    query = state["query"]
    candidate = None
    for c in state.get("candidates", []):
        cid = c.get("candidate_id", "")
        name = c.get("name", "")
        if (cid and cid in query) or (name and name in query):
            candidate = c
            break
    if candidate:
        try:
            detail = await resume_service.get_detail(candidate.get("resume_id", ""))
            return {"detail": detail}
        except Exception as e:
            logger.error(f"详情查询失败: {e}")
    return {}


async def respond_node(state: AgentState) -> dict:
    """节点5: 响应生成（流式）

    入参:
        state: AgentState
    出参:
        {"response": "..."}
    """
    intent = state.get("intent_type", "chitchat")
    if intent == "chitchat":
        prompt = CHITCHAT_PROMPT.format(query=state["query"])
    elif state.get("candidates"):
        prompt = SEARCH_RESPOND_PROMPT.format(
            query=state["query"],
            candidates=str(state["candidates"][:5]),
        )
    else:
        prompt = CHITCHAT_PROMPT.format(query=state["query"])

    response = ""
    try:
        async for tok in llm_client.chat_stream([{"role": "user", "content": prompt}]):
            response += tok
    except Exception as e:
        logger.error(f"响应生成失败: {e}")
        response = "抱歉，生成回复时出错，请稍后重试。"
    return {"response": response}
