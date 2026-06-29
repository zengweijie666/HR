"""
文件名: app/agent/graph.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: LangGraph 图定义，5 节点条件路由
入参: AgentState
出参: 编译后的 graph
对应 Business-Requirements F10-F12
"""
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import (
    intent_node,
    filter_extract_node,
    retrieve_rank_node,
    clarify_node,
    detail_node,
    respond_node,
)


def _route_after_intent(state: AgentState) -> str:
    """根据意图路由

    入参:
        state: AgentState
    出参:
        下一节点名（filter_extract/detail/respond）
    """
    intent = state.get("intent_type", "chitchat")
    if intent == "chitchat":
        return "respond"
    if intent == "detail":
        return "detail"
    # search / compare / qa 兜底走 filter_extract + retrieve_rank
    return "filter_extract"


def _route_after_retrieve(state: AgentState) -> str:
    """检索后路由: 有结果→respond, 无结果→clarify

    入参:
        state: AgentState
    出参:
        下一节点名（clarify/respond）
    """
    if state.get("candidates"):
        return "respond"
    return "clarify"


def build_graph():
    """构建 LangGraph 状态机

    出参:
        编译后的 graph，可调用 ainvoke / astream
    """
    workflow = StateGraph(AgentState)
    workflow.add_node("intent", intent_node)
    workflow.add_node("filter_extract", filter_extract_node)
    workflow.add_node("retrieve_rank", retrieve_rank_node)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("detail", detail_node)
    workflow.add_node("respond", respond_node)

    workflow.set_entry_point("intent")
    workflow.add_conditional_edges("intent", _route_after_intent, {
        "filter_extract": "filter_extract",
        "detail": "detail",
        "respond": "respond",
    })
    workflow.add_edge("filter_extract", "retrieve_rank")
    workflow.add_conditional_edges("retrieve_rank", _route_after_retrieve, {
        "clarify": "clarify",
        "respond": "respond",
    })
    workflow.add_edge("clarify", END)
    workflow.add_edge("detail", "respond")
    workflow.add_edge("respond", END)

    return workflow.compile()


agent_graph = build_graph()
