"""
文件名: tests/agent/test_state.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: AgentState 状态定义单元测试
"""
from app.agent.state import AgentState, make_state


def test_state_init():
    """AC: make_state 构造的初始状态字段完整"""
    state = make_state(query="Java 5年", session_id="s1")
    assert state["query"] == "Java 5年"
    assert state["intent_type"] is None
    assert state["strategy"] is None
    assert state["rewrites"] == []
    assert state["chunks"] == []
    assert state["candidates"] == []
    assert state["response"] == ""


def test_state_fields():
    """AC: AgentState 字段可读写更新"""
    state = make_state(query="", session_id="")
    state["intent_type"] = "search"
    state["strategy"] = "hyde"
    state["candidates"] = [{"candidate_id": "c1"}]
    assert state["intent_type"] == "search"
    assert len(state["candidates"]) == 1
