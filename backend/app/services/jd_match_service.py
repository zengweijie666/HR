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
        self.embedding = embedding_model
        self.vector_store = vector_store
        self.reranker = reranker_model
        self.llm = llm_client

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
        try:
            dense, sparse = self.embedding.encode([query])
        except Exception as e:
            logger.error(f"JD 匹配 embedding 编码失败: {e}", exc_info=True)
            return {"jd": jd, "candidates": []}

        # 3. 构造过滤条件（JD中的硬条件传Milvus）
        milvus_filters = {}
        if jd.get("work_years_min"):
            milvus_filters["work_years_min"] = jd["work_years_min"]
        if jd.get("salary_max"):
            milvus_filters["salary_max"] = jd["salary_max"]

        # 4. 混合检索（扩大召回，避免多chunk导致候选人被截断）
        retrieve_k = max(top_k * 5, 50)
        try:
            chunks = await self.vector_store.hybrid_search(
                dense, sparse, filters=milvus_filters, top_k=retrieve_k
            )
        except Exception as e:
            logger.error(f"JD 匹配 Milvus 检索失败: {e}", exc_info=True)
            chunks = []

        # 5. Reranker 精排 + resume级去重
        if chunks:
            docs = [c.get("parent_content", "") for c in chunks]
            try:
                scores = self.reranker.rerank(query, docs)
                if scores is None:
                    scores = []
                elif isinstance(scores, (int, float)):
                    scores = [scores]
                for i, c in enumerate(chunks):
                    c["rerank_score"] = float(scores[i]) if i < len(scores) else 0.0
            except Exception as e:
                logger.warning(f"JD 匹配 Reranker 精排失败，使用原始分数: {e}")
                for c in chunks:
                    c["rerank_score"] = 0.0
            # resume级去重：每个resume_id保留最高rerank_score的chunk
            best_by_resume = {}
            for c in chunks:
                rid = c.get("candidate_id", "")
                if not rid:
                    continue
                if rid not in best_by_resume or c["rerank_score"] > best_by_resume[rid]["rerank_score"]:
                    best_by_resume[rid] = c
            chunks = sorted(best_by_resume.values(), key=lambda x: x["rerank_score"], reverse=True)
            logger.info(f"JD匹配简历级去重后 {len(chunks)} 人")

        # 6. 拉取候选人元数据 + Python后过滤 + 生成匹配理由
        candidate_pool = chunks[: max(top_k * 2, 20)]
        candidate_ids = [c["candidate_id"] for c in candidate_pool if c.get("candidate_id")]
        candidates = await self._enrich_candidates(candidate_ids, jd, candidate_pool)

        return {"jd": jd, "candidates": candidates[:top_k]}

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
        """拉取候选人元数据 + Python内存过滤 + 生成匹配理由

        入参:
            candidate_ids: Milvus 返回的 ID 列表（Milvus candidate_id 字段存的是 resume_id）
            jd: 解析后的 JD 字典
            chunks: 检索 chunks（用于 rerank_score 回退）
        出参:
            候选人列表（按 match_score 降序）
        """
        if not candidate_ids or self.resumes_coll is None:
            return []
        cursor = self.resumes_coll.find({"resume_id": {"$in": candidate_ids}})
        docs = await cursor.to_list(length=len(candidate_ids))
        chunk_map = {c.get("candidate_id"): c for c in chunks}

        # Python内存硬过滤（兜底Milvus层）
        years_min = jd.get("work_years_min", 0) or 0
        sal_max = jd.get("salary_max", 0) or 0
        filtered_docs = []
        for doc in docs:
            doc_years = doc.get("work_years", 0)
            doc_salary = doc.get("expected_salary", {}) or {}
            doc_sal_min = doc_salary.get("min", 0) or 0
            if years_min and doc_years < years_min:
                continue
            if sal_max and doc_sal_min > 0 and doc_sal_min > sal_max:
                continue
            filtered_docs.append(doc)
        logger.info(f"JD匹配Python过滤后 {len(filtered_docs)}/{len(docs)} 人")

        scored: list[dict] = []
        reasons: list[str] = []

        # 先并发生成所有匹配理由（避免串行 LLM 调用导致 48 秒超时）
        match_tasks = []
        for doc in filtered_docs:
            rid = doc.get("resume_id", "")
            rerank_score = float(chunk_map.get(rid, {}).get("rerank_score", 0.0))
            match_score = round(rerank_score * 100, 1)
            match_tasks.append((doc, match_score))
            reasons.append("")  # 占位

        import asyncio
        async def _gen_reason(idx: int, doc: dict, ms: float) -> tuple[int, str]:
            r = await self._match_reason(jd, doc, ms)
            return idx, r

        reason_results = await asyncio.gather(
            *[_gen_reason(i, doc, ms) for i, (doc, ms) in enumerate(match_tasks)]
        )
        for idx, reason in reason_results:
            reasons[idx] = reason

        for i, (doc, match_score) in enumerate(match_tasks):
            cid = doc.get("candidate_id")
            rid = doc.get("resume_id")
            scored.append({
                "candidate_id": cid,
                "resume_id": rid,
                "name": doc.get("basic_info", {}).get("name", "") or doc.get("name", ""),
                "work_years": doc.get("work_years", 0),
                "education": doc.get("education", ""),
                "education_level": doc.get("education_level", 0),
                "skills": doc.get("skills", []),
                "expected_salary": doc.get("expected_salary", {"min": 0, "max": 0}),
                "match_score": match_score,
                "score": match_score,  # 兼容前端 CandidateCard 组件（读 score 字段）
                "reason": reasons[i],
                "tags": doc.get("tags", []),
                "is_favorite": doc.get("is_favorite", False),
                "summary": doc.get("summary", ""),
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
