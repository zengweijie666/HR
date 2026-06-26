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

# 顶层占位符，使 patch("app.core.embedding.BGEM3FlagModel") 可生效
BGEM3FlagModel = None


class EmbeddingModel:
    """BGE-M3 嵌入"""

    def __init__(self):
        self._model = None

    @property
    def model(self):
        """延迟加载 BGE-M3 模型

        通过 `global BGEM3FlagModel` 引用模块级符号，
        使测试中 `patch("app.core.embedding.BGEM3FlagModel")` 可拦截构造。
        BGE-M3 必须使用 BGEM3FlagModel（支持 dense+sparse），旧 FlagModel 不支持 sparse。
        """
        if self._model is None:
            global BGEM3FlagModel
            if BGEM3FlagModel is None:  # pragma: no cover - 实际运行时分支
                from FlagEmbedding import BGEM3FlagModel as _BGEM3FlagModel  # type: ignore
                BGEM3FlagModel = _BGEM3FlagModel
            self._model = BGEM3FlagModel(settings.BGE_M3_PATH, use_fp16=True)
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
            dense: numpy 数组，shape=(len(texts), 1024)
            sparse: List[Dict[token_id, weight]]，兼容 Milvus SPARSE_FLOAT_VECTOR
        """
        result = self.model.encode(texts, return_dense=True, return_sparse=True)
        # BGEM3FlagModel.encode 返回 {"dense_vecs", "lexical_weights", "colbert_vecs"}
        return result["dense_vecs"], result["lexical_weights"]


embedding_model = EmbeddingModel()
