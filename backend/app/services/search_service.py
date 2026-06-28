"""
文件名: app/services/search_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 检索服务 - BGE-M3 混合检索 + 策略改写 + Reranker 精排 + Redis 缓存 + LLM 评分
入参: query / filters / top_k / history
出参: 候选人卡片列表
对应 Business-Requirements F13
"""
import asyncio
import json
from app.core.embedding import embedding_model
from app.core.reranker import reranker_model
from app.core.vector_store import vector_store
from app.core.strategy_selector import strategy_selector
from app.core.database import MongoDB, RedisClient
from app.core.llm_client import llm_client
from app.core.config import settings
from app.core.logger import logger
from app.agent.prompts import SCORE_PROMPT


class SearchService:
    """检索服务"""

    def __init__(self):
        self.embedding = embedding_model
        self.reranker = reranker_model
        self.vector_store = vector_store
        self.strategy_selector = strategy_selector

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

    @property
    def redis(self):
        """延迟获取 Redis client"""
        if hasattr(self, "_redis"):
            return self._redis
        return RedisClient.get_client() if RedisClient.pool is not None else None

    @redis.setter
    def redis(self, value):
        """测试注入用"""
        self._redis = value

    async def search(
        self,
        query: str,
        filters: dict,
        top_k: int = 10,
        history: list = None,
    ) -> list[dict]:
        """主检索流程

        入参:
            query: 自然语言查询
            filters: 过滤条件 {education_min, work_years_min, salary_max}
            top_k: 返回数量
            history: 对话历史（用于策略选择）
        出参:
            候选人卡片列表
        """
        history = history or []
        cache_key = f"search:{query}:{json.dumps(filters, sort_keys=True, default=str)}:{top_k}"

        # 缓存命中
        if self.redis is not None:
            try:
                cached_val = await self.redis.get(cache_key)
                if cached_val:
                    logger.info(f"检索缓存命中: {query}")
                    return json.loads(cached_val)
            except Exception as e:
                logger.warning(f"缓存读取失败: {e}")

        # 策略改写
        strategy = await self.strategy_selector.select(query, history)
        rewrites = await self.strategy_selector.rewrite(query, strategy, history)
        logger.info(f"检索策略={strategy}, 改写={rewrites}")

        # 多改写检索 + 去重
        all_chunks: list[dict] = []
        for rq in rewrites:
            dense, sparse = self.embedding.encode([rq])
            chunks = await self.vector_store.hybrid_search(
                dense, sparse, filters=filters, top_k=settings.RETRIEVE_TOP_K
            )
            all_chunks.extend(chunks)

        seen_ids: set[str] = set()
        unique_chunks: list[dict] = []
        for c in all_chunks:
            cid = c.get("chunk_id")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                unique_chunks.append(c)

        # Reranker 精排
        if unique_chunks:
            docs = [c.get("parent_content", "") for c in unique_chunks]
            logger.info(f"Reranker 精排开始, {len(docs)} 个文档")
            try:
                scores = self.reranker.rerank(query, docs)
                logger.info(f"Reranker 返回类型={type(scores).__name__}, value={str(scores)[:200]}")
                if scores is None:
                    logger.warning("Reranker 返回 None, 跳过精排")
                    scores = []
                elif isinstance(scores, (int, float)):
                    scores = [scores]
                for i, c in enumerate(unique_chunks):
                    c["rerank_score"] = float(scores[i]) if i < len(scores) else 0.0
                unique_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)
                unique_chunks = unique_chunks[:top_k]
            except Exception as e:
                logger.error(f"Reranker 精排失败: {e}", exc_info=True)
                for c in unique_chunks:
                    c["rerank_score"] = 0.0

        # 拉取候选人元数据 + LLM 评分
        candidate_ids = [c["candidate_id"] for c in unique_chunks if c.get("candidate_id")]
        logger.info(f"候选人 ID 列表: {candidate_ids}")
        results = await self._enrich_candidates(candidate_ids, query, unique_chunks)

        # 写缓存
        if self.redis is not None:
            try:
                await self.redis.setex(
                    cache_key, 300, json.dumps(results, ensure_ascii=False, default=str)
                )
            except Exception as e:
                logger.warning(f"缓存写入失败: {e}")
        return results

    async def _enrich_candidates(
        self, candidate_ids: list[str], query: str, chunks: list[dict]
    ) -> list[dict]:
        """拉取候选人元数据 + LLM 评分

        入参:
            candidate_ids: Milvus 返回的 ID 列表（注意：Milvus candidate_id 字段存的是 resume_id）
            query: 原始查询
            chunks: 检索 chunks（用于 rerank_score 回退）
        出参:
            候选人卡片列表（按 score 降序）
        """
        if not candidate_ids:
            return []
        if self.resumes_coll is None:
            return []
        # Milvus 中 candidate_id 字段存的是 resume_id，用 resume_id 查询 MongoDB
        cursor = self.resumes_coll.find({"resume_id": {"$in": candidate_ids}})
        docs = await cursor.to_list(length=len(candidate_ids))
        logger.info(f"MongoDB 查询到 {len(docs)} 条简历文档")
        chunk_map = {c.get("candidate_id"): c for c in chunks}

        scored: list[dict] = []

        async def _score_one(doc: dict) -> dict | None:
            """单个候选人评分（并发安全）"""
            try:
                cid = doc.get("candidate_id")
                rid = doc.get("resume_id")
                rerank_score = float(chunk_map.get(rid, {}).get("rerank_score", 0.0))
                score_data = await self._llm_score_multi(query, doc, rerank_score)
                return {
                    "candidate_id": cid,
                    "resume_id": rid,
                    "name": doc.get("basic_info", {}).get("name", "") or doc.get("name", ""),
                    "work_years": doc.get("work_years", 0),
                    "education": doc.get("education", ""),
                    "education_level": doc.get("education_level", 0),
                    "skills": doc.get("skills", []),
                    "expected_salary": doc.get("expected_salary", {"min": 0, "max": 0}),
                    "score": score_data["overall"],
                    "score_detail": {
                        "skill": score_data["skill"],
                        "experience": score_data["experience"],
                        "education": score_data["education"],
                        "salary": score_data["salary"],
                    },
                    "reason": score_data["reason"],
                    "tags": doc.get("tags", []),
                    "is_favorite": doc.get("is_favorite", False),
                    "summary": doc.get("summary", ""),
                }
            except Exception as e:
                logger.warning(f"候选人评分异常: {e}")
                return None

        results = await asyncio.gather(*[_score_one(doc) for doc in docs], return_exceptions=False)
        scored = [r for r in results if r is not None]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    async def _llm_score_multi(self, query: str, candidate: dict, rerank_score: float = 0.0) -> dict:
        """LLM 分维度评分（4 维度 + overall + reason）

        入参:
            query: 原始查询
            candidate: 候选人文档
            rerank_score: reranker 得分（LLM 调用失败时兜底）
        出参:
            {skill, experience, education, salary, overall, reason}
        异常兜底:
            - LLM 调用失败（网络/超时）→ 4 维度全部回退 rerank_score*100
            - LLM 返回但 JSON 解析失败 → 全 0 + reason="评分暂不可用"
        设计:
            - overall 始终用代码加权计算（0.4*skill + 0.3*experience + 0.2*education + 0.1*salary），
              不信任 LLM 的 overall，避免 LLM 评分趋同导致无区分度
            - 候选人只传关键字段（姓名/年限/学历/技能/项目/工作经历），避免无关字段干扰
        """
        brief = self._build_candidate_brief(candidate)
        try:
            prompt = SCORE_PROMPT.format(query=query, candidate=brief)
            resp = await llm_client.chat(
                [{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
        except Exception as e:
            logger.warning(f"LLM 评分调用失败，回退 rerank_score: {e}")
            fallback = rerank_score * 100
            return {
                "skill": fallback,
                "experience": fallback,
                "education": fallback,
                "salary": fallback,
                "overall": round(fallback),
                "reason": "基于语义相似度匹配",
            }

        # LLM 调用成功，解析 JSON
        try:
            data = json.loads(resp.strip())
            result = {
                "skill": float(data.get("skill", 0)),
                "experience": float(data.get("experience", 0)),
                "education": float(data.get("education", 0)),
                "salary": float(data.get("salary", 0)),
                "reason": data.get("reason", "评分暂不可用"),
            }
            # overall 始终用代码加权计算，确保不同候选人评分有区分度
            # 权重：技能 40% + 经验 30% + 学历 20% + 薪资 10%
            result["overall"] = round(
                0.4 * result["skill"] + 0.3 * result["experience"]
                + 0.2 * result["education"] + 0.1 * result["salary"]
            )
            return result
        except Exception as e:
            logger.warning(f"LLM 评分 JSON 解析失败，全 0 兜底: {e}")
            return {
                "skill": 0,
                "experience": 0,
                "education": 0,
                "salary": 0,
                "overall": 0,
                "reason": "评分暂不可用",
            }

    @staticmethod
    def _build_candidate_brief(candidate: dict) -> str:
        """提取候选人关键字段供 LLM 评分，过滤无关字段避免干扰

        入参:
            candidate: MongoDB 候选人文档（含 basic_info/skills/work_experience 等全量字段）
        出参:
            精简后的候选人描述字符串，包含：姓名/工作年限/学历/技能/工作经历/项目/总结
        """
        basic = candidate.get("basic_info", {}) or {}
        name = basic.get("name", "") or candidate.get("name", "")
        work_years = candidate.get("work_years", 0)
        education = candidate.get("education", "")
        skills = candidate.get("skills", []) or []

        # 工作经历：公司/岗位（最多3条）
        work_exp = candidate.get("work_experience", []) or []
        work_desc = "; ".join([
            f"{w.get('company', '')}/{w.get('position', '')}"
            for w in work_exp[:3]
            if w.get("company") or w.get("position")
        ])

        # 项目经历：名称+描述（最多3条，每条截断100字）
        projects = candidate.get("projects", []) or []
        project_desc = "; ".join([
            f"{p.get('name', '')}: {(p.get('description', '') or '')[:100]}"
            for p in projects[:3]
            if p.get("name")
        ])

        summary = (candidate.get("summary", "") or "")[:150]

        return (
            f"姓名:{name}, 工作年限:{work_years}年, 学历:{education}, "
            f"技能:{skills}, "
            f"工作经历:{work_desc}, "
            f"项目:{project_desc}, "
            f"总结:{summary}"
        )

    async def _llm_reason(self, query: str, candidate: dict, score: float) -> str:
        """LLM 生成推荐理由（保留向后兼容，新流程已由 _llm_score_multi 提供 reason）

        入参:
            query: 原始查询
            candidate: 候选人文档
            score: 评分
        出参:
            推荐理由
        """
        try:
            prompt = (
                f"用一句话说明为什么候选人 {candidate.get('name', '')} 适合需求: "
                f"{query}（评分 {score}）"
            )
            resp = await llm_client.chat([{"role": "user", "content": prompt}])
            return resp.strip()
        except Exception as e:
            logger.warning(f"LLM 理由生成失败: {e}")
            return ""


search_service = SearchService()
