"""
文件名: tests/core/test_milvus_client.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: Milvus 客户端 + 过滤表达式构建测试
"""
from unittest.mock import patch, MagicMock
from app.core.milvus_client import MilvusClient


def test_init_collection():
    """不存在时应创建 Collection"""
    with patch("app.core.milvus_client.connections.connect"), \
         patch("app.core.milvus_client.Collection") as MockColl, \
         patch("app.core.milvus_client.utility.has_collection", return_value=False):
        instance = MagicMock()
        MockColl.return_value = instance
        client = MilvusClient()
        client.ensure_collection()
        # 应创建 collection
        MockColl.assert_called()


def test_filter_expr_builder():
    """build_filter_expr 应生成 education/work_years/salary 过滤表达式"""
    from app.core.vector_store import build_filter_expr
    expr = build_filter_expr({"education_min": 2, "work_years_min": 5, "salary_max": 30})
    assert "education_level >= 2" in expr
    assert "work_years >= 5" in expr
    assert "salary_min <= 30" in expr


def test_filter_expr_empty():
    """空 filters 应返回空字符串"""
    from app.core.vector_store import build_filter_expr
    assert build_filter_expr({}) == ""
