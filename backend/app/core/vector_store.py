"""
文件名: app/core/vector_store.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: Milvus 混合检索（复用 EduRAG），Dense+Sparse WeightedRanker
入参: query vectors / filters
出参: 检索结果列表
"""
from typing import Any
from pymilvus import AnnSearchRequest, WeightedRanker
from app.core.config import settings
from app.core.logger import logger
from app.core.milvus_client import milvus_client


def build_filter_expr(filters: dict) -> str:
    """构建 Milvus 标量过滤表达式

    入参:
        filters: {"education_min": int, "work_years_min": int, "salary_max": int}
    出参:
        Milvus 表达式字符串，空 filters 返回 ""
    """
    exprs: list[str] = []
    if filters.get("education_min") is not None:
        exprs.append(f"education_level >= {filters['education_min']}")
    if filters.get("work_years_min") is not None:
        exprs.append(f"work_years >= {filters['work_years_min']}")
    if filters.get("salary_max") is not None:
        exprs.append(f"salary_min <= {filters['salary_max']}")
    return " and ".join(exprs)


class VectorStore:
    """混合检索"""

    @property
    def collection(self):
        """复用全局 milvus_client 的 collection"""
        return milvus_client.collection

    async def insert(self, children, dense, sparse, parents, resume_id: str):
        """插入子块向量

        入参:
            children: Chunk 列表（子块）
            dense: 稠密向量列表
            sparse: 稀疏向量列表
            parents: Chunk 列表（父块，用于回溯 parent_content）
            resume_id: 简历 ID
        """
        data = [
            [c.chunk_id for c in children],
            [resume_id] * len(children),
            dense,
            sparse,
            [0] * len(children),  # salary_min 占位
            [0] * len(children),  # salary_max 占位
            [1] * len(children),  # education_level 占位
            [0] * len(children),  # work_years 占位
            [""] * len(children),
            [c.parent_id for c in children],
            [next((p.content for p in parents if p.parent_id == c.parent_id), "") for c in children],
        ]
        self.collection.insert(data)
        logger.info(f"插入 {len(children)} 子块, resume_id={resume_id}")

    async def hybrid_search(
        self, query_dense, query_sparse, filters: dict, top_k: int = 20
    ) -> list[dict]:
        """Dense+Sparse 混合检索

        入参:
            query_dense: 查询稠密向量列表
            query_sparse: 查询稀疏向量列表
            filters: 标量过滤条件
            top_k: 返回数量
        出参:
            [{"chunk_id", "candidate_id", "score", "parent_content"}, ...]
        """
        expr = build_filter_expr(filters)
        dense_req = AnnSearchRequest(
            data=[query_dense[0]] if isinstance(query_dense[0], list) else query_dense,
            anns_field="dense_vector",
            param={"metric_type": "IP", "params": {"nprobe": 16}},
            limit=top_k * 2,
            expr=expr,
        )
        sparse_req = AnnSearchRequest(
            data=query_sparse,
            anns_field="sparse_vector",
            param={"metric_type": "IP"},
            limit=top_k * 2,
            expr=expr,
        )
        results = self.collection.hybrid_search(
            reqs=[dense_req, sparse_req],
            rerank=WeightedRanker(settings.HYBRID_DENSE_WEIGHT, settings.HYBRID_SPARSE_WEIGHT),
            limit=top_k,
        )
        parsed: list[dict] = []
        for hit in results[0]:
            parsed.append({
                "chunk_id": hit.get("id"),
                "candidate_id": hit.get("candidate_id"),
                "score": hit.score,
                "parent_content": hit.get("parent_content") or "",
            })
        return parsed

    async def delete_by_resume_id(self, resume_id: str):
        """删除某简历的所有向量

        入参:
            resume_id: 简历 ID（对应 Milvus 中的 candidate_id 字段）
        """
        self.collection.delete(f'candidate_id == "{resume_id}"')
        logger.info(f"删除 resume_id={resume_id} 的所有向量")


vector_store = VectorStore()
