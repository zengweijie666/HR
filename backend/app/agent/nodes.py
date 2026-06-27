"""
文件名: app/agent/nodes.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: LangGraph 5 节点实现（<300行），每节点输入/输出 AgentState
入参: AgentState
出参: 更新后的 AgentState（部分字段）
对应 Business-Requirements F11/F12
"""
from app.agent.state import AgentState
from app.agent.prompts import (
    INTENT_PROMPT,
    CHITCHAT_PROMPT,
    CLARIFY_PROMPT,
    SEARCH_RESPOND_PROMPT,
)
from app.core.llm_client import llm_client
from app.core.logger import logger
from app.services.search_service import SearchService
from app.services.resume_service import ResumeService

# 模块级单例，便于测试 patch
search_service = SearchService()
resume_service = ResumeService()


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
            top_k=10,
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
