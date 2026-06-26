"""
文件名: app/core/reranker.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: BGE-Reranker-v2-m3 CrossEncoder 精排
入参: query, documents
出参: scores 列表
"""
from app.core.config import settings
from app.core.logger import logger

# 顶层占位符，使 patch("app.core.reranker.FlagModel") 可生效
FlagModel = None


class RerankerModel:
    """BGE-Reranker"""

    def __init__(self):
        self._model = None

    @property
    def model(self):
        """延迟加载 BGE-Reranker 模型"""
        if self._model is None:
            global FlagModel
            if FlagModel is None:  # pragma: no cover - 实际运行时分支
                from FlagEmbedding import FlagModel as _FlagModel  # type: ignore
                FlagModel = _FlagModel
            self._model = FlagModel(settings.BGE_RERANKER_PATH, use_fp16=True)
            logger.info("BGE-Reranker 模型已加载")
        return self._model

    @model.setter
    def model(self, value):
        """测试注入用"""
        self._model = value

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        """对 documents 重排，返回 scores

        入参:
            query: 查询文本
            documents: 候选文档列表
        出参:
            与 documents 等长的 score 列表
        """
        pairs = [[query, doc] for doc in documents]
        return self.model.compute_score(pairs)


reranker_model = RerankerModel()
