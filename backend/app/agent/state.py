"""
文件名: app/agent/state.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: LangGraph Agent 状态定义，5 节点共享
入参: query / session_id / history
出参: 含意图/策略/改写/检索/重排/响应等字段的 TypedDict
对应 Business-Requirements F10-F12
"""
from typing import TypedDict


class AgentState(TypedDict, total=False):
    """LangGraph 状态，total=False 允许字段缺失

    字段分组：
    - 输入: query / session_id / user_id / history / filters
    - 中间产物: intent / strategy / rewrites / chunks / ranked / candidates
    - 输出: response / message_id / error
    """
    # 输入
    query: str
    session_id: str
    user_id: str
    history: list[dict]
    filters: dict
    # 中间产物
    intent_type: str | None      # chitchat/search/detail/compare（避开 LangGraph 节点名 intent）
    strategy: str | None         # direct/hyde/subquery/backtracking
    rewrites: list[str]          # 改写后的 query 列表
    chunks: list[dict]           # 检索结果
    ranked: list[dict]           # 重排后的结果
    decomposed: dict             # 查询分解结果（main_query/sub_queries/structured_filters）
    compressed_context: dict     # resume_id → 压缩后的 context 字符串
    candidates: list[dict]       # 候选人卡片
    # 输出
    response: str               # LLM 最终回复
    message_id: str             # 消息 ID
    error: str | None            # 错误信息


def make_state(
    query: str,
    session_id: str,
    history: list = None,
    filters: dict = None,
    user_id: str = "",
    last_candidates: list = None,
) -> AgentState:
    """构造初始 AgentState

    入参:
        query: 用户查询
        session_id: 会话 ID
        history: 对话历史
        filters: 过滤条件
        user_id: 用户 ID
        last_candidates: 上一轮检索到的候选人列表（供 compare/qa/detail 复用，避免重复检索）
    出参:
        完整初始化的 AgentState
    """
    return AgentState(
        query=query,
        session_id=session_id,
        user_id=user_id,
        history=history or [],
        filters=filters or {},
        intent_type=None,
        strategy=None,
        rewrites=[],
        chunks=[],
        ranked=[],
        decomposed={},
        compressed_context={},
        candidates=last_candidates or [],
        response="",
        message_id="",
        error=None,
    )
