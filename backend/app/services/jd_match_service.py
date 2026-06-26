"""
文件名: app/services/jd_match_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: JD 匹配服务 - LLM 解析 JD + 混合检索 + Reranker 精排 + 匹配理由生成
入参: jd_text / top_k
出参: {jd: {...}, candidates: [...]}
对应 Business-Requirements F19 (AC19.1-19.2)
"""
import json
from app.core.embedding import embedding_model
from app.core.reranker import reranker_model
from app.core.vector_store import vector_store
from app.core.database import MongoDB
from app.core.llm_client import llm_client
from app.core.logger import logger
from app.agent.prompts import JD_PARSE_PROMPT, JD_MATCH_REASON_PROMPT


class JdMatchService:
    """JD 匹配服务"""

    def __init__(self):
        self.resumes_coll = MongoDB.db.resumes if MongoDB.db is not None else None
        self.embedding = embedding_model
        self.vector_store = vector_store
        self.reranker = reranker_model
        self.llm = llm_client

    async def match_jd(self, jd_text: str, top_k: int = 10) -> dict:
        """AC19.1-19.2: JD 匹配主流程

        入参:
            jd_text: JD 原文
            top_k: 返回候选人数量
        出参:
            {"jd": {title, skills, work_years_min, salary_max},
             "candidates": [{candidate_id, resume_id, name, work_years, education,
                             skills, expected_salary, match_score, reason, tags, is_favorite}]}
        """
        # 1. LLM 解析 JD
        jd = await self._parse_jd(jd_text)
        logger.info(f"JD 解析完成: title={jd.get('title')}")

        # 2. 构造检索查询
        query = (
            f"{jd.get('title', '')} "
            f"{' '.join(jd.get('skills', []))} "
            f"{jd.get('work_years_min', 0)}年经验"
        ).strip()
        dense, sparse = self.embedding.encode([query])

        # 3. 混合检索
        chunks = await self.vector_store.hybrid_search(
            dense, sparse, filters={}, top_k=top_k
        )

        # 4. Reranker 精排
        if chunks:
            docs = [c.get("parent_content", "") for c in chunks]
            scores = self.reranker.rerank(query, docs)
            for i, c in enumerate(chunks):
                c["rerank_score"] = float(scores[i]) if i < len(scores) else 0.0
            chunks.sort(key=lambda x: x["rerank_score"], reverse=True)
            chunks = chunks[:top_k]

        # 5. 拉取候选人元数据 + 生成匹配理由
        candidate_ids = [c["candidate_id"] for c in chunks if c.get("candidate_id")]
        candidates = await self._enrich_candidates(candidate_ids, jd, chunks)

        return {"jd": jd, "candidates": candidates}

    async def _parse_jd(self, jd_text: str) -> dict:
        """AC19.2: LLM 解析 JD 为结构化数据

        入参:
            jd_text: JD 原文
        出参:
            {title, skills, work_years_min, salary_max}，解析失败时返回兜底空结构
        """
        try:
            prompt = JD_PARSE_PROMPT.format(jd_text=jd_text)
            resp = await self.llm.chat([{"role": "user", "content": prompt}])
            parsed = json.loads(resp.strip())
            # 字段兜底
            return {
                "title": parsed.get("title", ""),
                "skills": parsed.get("skills", []) or [],
                "work_years_min": parsed.get("work_years_min", 0) or 0,
                "salary_max": parsed.get("salary_max", 0) or 0,
            }
        except Exception as e:
            logger.warning(f"JD 解析失败，使用空结构兜底: {e}")
            return {"title": "", "skills": [], "work_years_min": 0, "salary_max": 0}

    async def _enrich_candidates(
        self, candidate_ids: list[str], jd: dict, chunks: list[dict]
    ) -> list[dict]:
        """拉取候选人元数据 + 生成匹配理由

        入参:
            candidate_ids: 候选人 ID 列表
            jd: 解析后的 JD 字典
            chunks: 检索 chunks（用于 rerank_score 回退）
        出参:
            候选人列表（按 match_score 降序）
        """
        if not candidate_ids or self.resumes_coll is None:
            return []
        cursor = self.resumes_coll.find({"candidate_id": {"$in": candidate_ids}})
        docs = await cursor.to_list(length=len(candidate_ids))
        chunk_map = {c.get("candidate_id"): c for c in chunks}

        scored: list[dict] = []
        for doc in docs:
            cid = doc.get("candidate_id")
            rerank_score = float(chunk_map.get(cid, {}).get("rerank_score", 0.0))
            match_score = round(rerank_score * 100, 1)
            reason = await self._match_reason(jd, doc, match_score)
            scored.append({
                "candidate_id": cid,
                "resume_id": doc.get("resume_id"),
                "name": doc.get("name", ""),
                "work_years": doc.get("work_years", 0),
                "education": doc.get("education", ""),
                "skills": doc.get("skills", []),
                "expected_salary": doc.get("expected_salary", {"min": 0, "max": 0}),
                "match_score": match_score,
                "reason": reason,
                "tags": doc.get("tags", []),
                "is_favorite": doc.get("is_favorite", False),
            })
        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored

    async def _match_reason(self, jd: dict, candidate: dict, score: float) -> str:
        """LLM 生成 JD 匹配理由

        入参:
            jd: 解析后的 JD 字典
            candidate: 候选人文档
            score: 匹配分数
        出参:
            一句话匹配理由，失败时返回空字符串
        """
        try:
            prompt = JD_MATCH_REASON_PROMPT.format(
                jd=str(jd), candidate=str(candidate), score=score
            )
            resp = await self.llm.chat([{"role": "user", "content": prompt}])
            return resp.strip()
        except Exception as e:
            logger.warning(f"JD 匹配理由生成失败: {e}")
            return ""


jd_match_service = JdMatchService()
