"""
文件名: tests/core/test_embedding.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: BGE-M3 嵌入模型单元测试
"""
from unittest.mock import patch, MagicMock
from app.core.embedding import EmbeddingModel


def test_lazy_load():
    """首次访问 model 时才加载 BGEM3FlagModel"""
    with patch("app.core.embedding.BGEM3FlagModel") as MockFlag:
        m = EmbeddingModel()
        assert m._model is None
        _ = m.model
        MockFlag.assert_called_once()


def test_encode_returns_dense_sparse():
    """encode 应返回 (dense, sparse) 二元组，key 对齐 BGEM3FlagModel 真实返回，类型为原生"""
    with patch("app.core.embedding.BGEM3FlagModel") as MockFlag:
        instance = MagicMock()
        # 模拟 BGEM3FlagModel 返回 numpy 类型，encode 内部会转原生
        import numpy as np
        instance.encode.return_value = {
            "dense_vecs": np.array([[0.1] * 1024], dtype=np.float32),
            "lexical_weights": [{np.int64(6): np.float32(0.5)}],
            "colbert_vecs": None,
        }
        MockFlag.return_value = instance
        m = EmbeddingModel()
        dense, sparse = m.encode(["test"])
        assert len(dense[0]) == 1024
        # 验证已转原生类型
        assert isinstance(dense[0], list)
        assert isinstance(dense[0][0], float)
        assert isinstance(sparse[0], dict)
        key = next(iter(sparse[0]))
        assert isinstance(key, int)
        assert isinstance(sparse[0][key], float)
