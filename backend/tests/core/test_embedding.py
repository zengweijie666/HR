"""
文件名: tests/core/test_embedding.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: BGE-M3 嵌入模型单元测试
"""
from unittest.mock import patch, MagicMock
from app.core.embedding import EmbeddingModel


def test_lazy_load():
    """首次访问 model 时才加载 FlagModel"""
    with patch("app.core.embedding.FlagModel") as MockFlag:
        m = EmbeddingModel()
        assert m._model is None
        _ = m.model
        MockFlag.assert_called_once()


def test_encode_returns_dense_sparse():
    """encode 应返回 (dense, sparse) 二元组"""
    with patch("app.core.embedding.FlagModel") as MockFlag:
        instance = MagicMock()
        instance.encode.return_value = {"dense": [[0.1] * 1024], "sparse": [{}]}
        MockFlag.return_value = instance
        m = EmbeddingModel()
        dense, sparse = m.encode(["test"])
        assert len(dense[0]) == 1024
