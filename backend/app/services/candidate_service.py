"""
文件名: app/services/candidate_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 相似候选人推荐 + 对比分析
入参: resume_id / candidate_ids
出参: 相似列表 / 对比维度数据
对应 Business-Requirements F15/F16
"""
from app.core.database import MongoDB
from app.core.embedding import embedding_model
from app.core.vector_store import vector_store


class CandidateService:
    """相似候选人推荐 + 对比"""

    def __init__(self):
        self.embedding = embedding_model
        self.vector_store = vector_store

    @property
    def resumes_coll(self):
        """延迟获取 MongoDB resumes collection（避免模块导入时 MongoDB 未连接）"""
        if hasattr(self, "_resumes_coll"):
            return self._resumes_coll
        return MongoDB.db.resumes if MongoDB.db is not None else None

    @resumes_coll.setter
    def resumes_coll(self, value):
        """测试注入用"""
        self._resumes_coll = value

    async def get_similar(self, resume_id: str, top_k: int = 5) -> list[dict]:
        """AC15.1: 基于简历向量找相似候选人

        入参:
            resume_id: 基准简历 ID
            top_k: 返回数量
        出参:
            相似候选人列表（已剔除本人）
        """
        if self.resumes_coll is None:
            return []
        doc = await self.resumes_coll.find_one({"resume_id": resume_id})
        if not doc:
            return []
        # 用简历 summary 或 skills_text 作为查询
        query_text = doc.get("summary", "") or "、".join(doc.get("skills", []))
        dense, sparse = self.embedding.encode([query_text])
        # 扩大召回，避免多chunk导致候选人截断
        retrieve_k = max((top_k + 1) * 5, 20)
        chunks = await self.vector_store.hybrid_search(dense, sparse, {}, top_k=retrieve_k)

        # Milvus candidate_id 字段存的是 resume_id；resume级去重，排除自己
        self_rid = resume_id
        seen: set[str] = set()
        resume_ids: list[str] = []
        for c in chunks:
            rid = c.get("candidate_id", "")
            if not rid or rid == self_rid or rid in seen:
                continue
            seen.add(rid)
            resume_ids.append(rid)
            if len(resume_ids) >= top_k:
                break
        if not resume_ids:
            return []
        cursor = self.resumes_coll.find({"resume_id": {"$in": resume_ids}})
        docs = await cursor.to_list(length=top_k)
        for d in docs:
            d.pop("_id", None)
        return docs

    async def compare(self, candidate_ids: list[str]) -> dict:
        """AC16.1: 候选人对比

        入参:
            candidate_ids: 候选人 ID 列表
        出参:
            {"candidates": [...], "dimensions": [...]}
        """
        if not candidate_ids or self.resumes_coll is None:
            return {"candidates": [], "dimensions": []}
        cursor = self.resumes_coll.find({"candidate_id": {"$in": candidate_ids}})
        docs = await cursor.to_list(length=len(candidate_ids))
        for d in docs:
            d.pop("_id", None)

        candidates = []
        for doc in docs:
            salary = doc.get("expected_salary", {}) or {}
            candidates.append({
                "candidate_id": doc.get("candidate_id"),
                "name": doc.get("basic_info", {}).get("name", "") or doc.get("name", ""),
                "work_years": doc.get("work_years", 0),
                "education_level": doc.get("education_level", 0),
                "education": doc.get("education", ""),
                "skills_count": len(doc.get("skills", [])),
                "skills": doc.get("skills", []),
                "salary_min": salary.get("min", 0),
                "salary_max": salary.get("max", 0),
                "expected_salary": salary,
            })
        return {
            "candidates": candidates,
            "dimensions": ["work_years", "education_level", "skills_count", "expected_salary"],
        }


candidate_service = CandidateService()
