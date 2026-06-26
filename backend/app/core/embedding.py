"""
文件名: app/core/embedding.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: BGE-M3 嵌入模型，@property 延迟加载
入参: 文本列表
出参: (dense_vectors, sparse_vectors)
"""
from app.core.config import settings
from app.core.logger import logger

# 顶层占位符，使 patch("app.core.embedding.FlagModel") 可生效
FlagModel = None


class EmbeddingModel:
    """BGE-M3 嵌入"""

    def __init__(self):
        self._model = None

    @property
    def model(self):
        """延迟加载 BGE-M3 模型

        通过 `global FlagModel` 引用模块级符号，
        使测试中 `patch("app.core.embedding.FlagModel")` 可拦截构造。
        """
        if self._model is None:
            global FlagModel
            if FlagModel is None:  # pragma: no cover - 实际运行时分支
                from FlagEmbedding import FlagModel as _FlagModel  # type: ignore
                FlagModel = _FlagModel
            self._model = FlagModel(settings.BGE_M3_PATH, use_fp16=True)
            logger.info("BGE-M3 模型已加载")
        return self._model

    @model.setter
    def model(self, value):
        """测试注入用"""
        self._model = value

    def encode(self, texts: list[str]) -> tuple[list, list]:
        """编码文本，返回 (dense, sparse)

        入参:
            texts: 待编码文本列表
        出参:
            (dense_vectors, sparse_vectors) 二元组
        """
        result = self.model.encode(texts, return_dense=True, return_sparse=True)
        return result["dense"], result["sparse"]


embedding_model = EmbeddingModel()
