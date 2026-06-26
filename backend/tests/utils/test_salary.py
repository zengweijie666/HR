"""
文件名: tests/utils/test_salary.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试薪资字符串解析
"""
from app.utils.salary import parse_salary


def test_parse_range_k():
    assert parse_salary("20-30K") == {"min": 20, "max": 30}


def test_parse_range_lowercase():
    assert parse_salary("15-25k") == {"min": 15, "max": 25}


def test_parse_single():
    assert parse_salary("30K") == {"min": 30, "max": 30}


def test_parse_yuan():
    assert parse_salary("20000-30000元") == {"min": 20, "max": 30}


def test_parse_invalid():
    assert parse_salary("面议") is None


def test_parse_empty():
    assert parse_salary("") is None
