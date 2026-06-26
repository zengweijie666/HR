"""
文件名: tests/core/test_reranker.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: BGE-Reranker 单元测试
"""
from unittest.mock import patch, MagicMock
from app.core.reranker import RerankerModel


def test_lazy_load():
    """首次访问 model 时才加载 FlagModel"""
    with patch("app.core.reranker.FlagModel") as MockFlag:
        m = RerankerModel()
        assert m._model is None
        _ = m.model
        MockFlag.assert_called_once()


def test_rerank_returns_scores():
    """rerank 应返回 score 列表"""
    with patch("app.core.reranker.FlagModel") as MockFlag:
        instance = MagicMock()
        instance.compute_score.return_value = [0.9, 0.5]
        MockFlag.return_value = instance
        m = RerankerModel()
        scores = m.rerank("query", ["doc1", "doc2"])
        assert scores == [0.9, 0.5]
