"""
文件名: test_prompts.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: 测试 prompts 模块意图/通用问答/评分模板
"""
from app.agent.prompts import INTENT_PROMPT, QA_PROMPT, SCORE_PROMPT


def test_intent_prompt_contains_qa_category():
    """INTENT_PROMPT 应包含 qa 意图分类"""
    assert "qa" in INTENT_PROMPT
    assert "HR 知识问答" in INTENT_PROMPT or "通用问答" in INTENT_PROMPT


def test_qa_prompt_exists_and_has_constraints():
    """QA_PROMPT 应存在且包含不编造候选人约束"""
    assert QA_PROMPT is not None
    assert "不编造" in QA_PROMPT or "禁止编造" in QA_PROMPT


def test_score_prompt_requires_json_with_4_dimensions():
    """SCORE_PROMPT 应要求 JSON 输出含 4 维度"""
    assert "skill" in SCORE_PROMPT
    assert "experience" in SCORE_PROMPT
    assert "education" in SCORE_PROMPT
    assert "salary" in SCORE_PROMPT
    assert "overall" in SCORE_PROMPT
    assert "reason" in SCORE_PROMPT
