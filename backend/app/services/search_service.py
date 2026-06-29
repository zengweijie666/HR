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
        decomposed: dict = None,
        compressed_context: dict = None,
    ) -> list[dict]:
        """主检索流程

        入参:
            query: 自然语言查询
            filters: 过滤条件 {education_min, work_years_min, salary_max}
            top_k: 返回数量
            history: 对话历史（用于策略选择）
        出参:
            候选人卡片列表
        流程:
            1. 缓存检查
            2. 策略改写（同义词/多查询）
            3. 多改写混合检索（Milvus top_k=RETRIEVE_TOP_K*2 扩大召回）
            4. chunk_id 去重
            5. Reranker 精排所有chunks
            6. 【关键修复】按 candidate_id(resume_id) 去重，每个简历保留最高 rerank_score 的chunk
            7. 拉取 MongoDB 元数据
            8. 【关键修复】Python 内存硬过滤（学历/薪资/年限），兜底 Milvus 层
            9. 取候选池（top_k*2 送 LLM 评分，保证评分后有足够结果）
            10. LLM 并发评分 + 融合 rerank_score
            11. 排序 + 截断 top_k
            12. 写缓存
        """
        history = history or []
        filters = dict(filters or {})  # 复制，避免修改调用方 dict

        # 【关键修复】从自然语言 query 中正则提取 required_skills
        # 直接搜索 API 不经过 agent graph 的 filter_extract_node，需在此补充提取
        try:
            from app.agent.nodes import _regex_extract_filters
            extracted = _regex_extract_filters(query)
            extracted_skills = extracted.get("required_skills", [])
            if extracted_skills:
                existing = set(filters.get("required_skills", []) or [])
                for sk in extracted_skills:
                    existing.add(sk)
                filters["required_skills"] = list(existing)
                logger.info(f"从query提取 required_skills={filters['required_skills']}")
        except Exception as e:
            logger.warning(f"required_skills 提取失败: {e}")

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

        # 多路召回：Route A（主查询）+ Route B（子查询）+ Route C（MongoDB 结构化保底）
        # 若 decomposed 提供 main_query，Route A 用它；否则回退 strategy_selector 改写
        if decomposed and decomposed.get("main_query"):
            route_a_queries = [decomposed["main_query"]]
            strategy = "decompose"
            logger.info(f"检索策略=decompose, Route A main_query='{route_a_queries[0]}'")
        else:
            strategy = await self.strategy_selector.select(query, history)
            route_a_queries = await self.strategy_selector.rewrite(query, strategy, history)
            logger.info(f"检索策略={strategy}, 改写={route_a_queries}")

        # 扩大 Milvus 每路召回数量，避免多简历多chunk导致候选人被截断
        retrieve_per_query = max(settings.RETRIEVE_TOP_K, top_k * 5)

        # Route A: 主查询 hybrid_search
        all_chunks: list[dict] = []
        for rq in route_a_queries:
            dense, sparse = self.embedding.encode([rq])
            chunks = await self.vector_store.hybrid_search(
                dense, sparse, filters=filters, top_k=retrieve_per_query
            )
            all_chunks.extend(chunks)

        # Route B: 子查询独立检索（若 decomposed 提供）
        sub_queries = (decomposed or {}).get("sub_queries", []) if decomposed else []
        for sq in sub_queries[:3]:
            dense, sparse = self.embedding.encode([sq])
            chunks = await self.vector_store.hybrid_search(
                dense, sparse, filters=filters, top_k=max(retrieve_per_query // 3, 10)
            )
            all_chunks.extend(chunks)
            logger.info(f"Route B 子查询召回: '{sq[:30]}' → {len(chunks)} chunks")

        # Route C: MongoDB 结构化保底（按 structured_filters 查 MongoDB）
        if decomposed and decomposed.get("structured_filters"):
            sf = decomposed["structured_filters"]
            mongo_hits = await self._mongo_structured_recall(sf, max(retrieve_per_query // 2, 10))
            if mongo_hits:
                logger.info(f"Route C MongoDB 结构化保底召回 {len(mongo_hits)} chunks")
                for c in mongo_hits:
                    c["rerank_score"] = 0.0  # 兜底分，让 Reranker 重打
                all_chunks.extend(mongo_hits)

        # chunk_id 去重
        seen_chunk_ids: set[str] = set()
        unique_chunks: list[dict] = []
        for c in all_chunks:
            cid = c.get("chunk_id")
            if cid and cid not in seen_chunk_ids:
                seen_chunk_ids.add(cid)
                unique_chunks.append(c)
        logger.info(f"去重后 chunk 数: {len(unique_chunks)}")

        # Reranker 精排（对所有 unique_chunks 精排，不提前截断）
        if unique_chunks:
            docs = [c.get("parent_content", "") for c in unique_chunks]
            logger.info(f"Reranker 精排开始, {len(docs)} 个chunks")
            try:
                scores = self.reranker.rerank(query, docs)
                if scores is None:
                    logger.warning("Reranker 返回 None, 跳过精排")
                    scores = []
                elif isinstance(scores, (int, float)):
                    scores = [scores]
                for i, c in enumerate(unique_chunks):
                    c["rerank_score"] = float(scores[i]) if i < len(scores) else 0.0
            except Exception as e:
                logger.error(f"Reranker 精排失败: {e}", exc_info=True)
                for c in unique_chunks:
                    c["rerank_score"] = 0.0

            # 【关键修复】按 candidate_id(resume_id) 去重，每个简历保留最高 rerank_score 的chunk
            best_chunk_by_resume: dict[str, dict] = {}
            for c in unique_chunks:
                rid = c.get("candidate_id", "")
                if not rid:
                    continue
                if rid not in best_chunk_by_resume or c["rerank_score"] > best_chunk_by_resume[rid]["rerank_score"]:
                    best_chunk_by_resume[rid] = c

            # 按 rerank_score 降序排列简历级chunks
            deduped_chunks = sorted(
                best_chunk_by_resume.values(),
                key=lambda x: x["rerank_score"],
                reverse=True,
            )

            # 注意：不再使用 rerank_score 绝对阈值过滤。BGE-Reranker 对口语化查询（如
            # "有没有会html的"）整体打分偏低，绝对阈值会误杀全部候选人。相关性过滤交给
            # 下游的技能硬过滤（required_skills）+ 最低分数截断（MIN_SCORE_THRESHOLD=40）。
            logger.info(f"简历级去重后 候选人数: {len(deduped_chunks)}")

            # 取足够多的候选简历送 LLM 评分（top_k*3 但至少 20，以保证硬过滤后仍有足够结果）
            candidate_pool_size = max(top_k * 3, 20)
            candidate_chunks = deduped_chunks[:candidate_pool_size]
        else:
            candidate_chunks = []

        # 拉取候选人元数据
        candidate_ids = [c["candidate_id"] for c in candidate_chunks if c.get("candidate_id")]
        logger.info(f"准备查询MongoDB的候选人ID数: {len(candidate_ids)}, IDs={candidate_ids}")
        results = await self._enrich_candidates(candidate_ids, query, candidate_chunks, filters)

        # 最终排序取 top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        # 【关键修复】最低分数截断：低于40分的候选人与需求基本不匹配，不返回
        MIN_SCORE_THRESHOLD = 40
        results = [r for r in results if r["score"] >= MIN_SCORE_THRESHOLD]
        results = results[:top_k]
        logger.info(f"分数截断后 {len(results)} 人 (min_score={MIN_SCORE_THRESHOLD})")

        # 写缓存
        if self.redis is not None:
            try:
                await self.redis.setex(
                    cache_key, 300, json.dumps(results, ensure_ascii=False, default=str)
                )
            except Exception as e:
                logger.warning(f"缓存写入失败: {e}")
        return results

    async def _mongo_structured_recall(self, sf: dict, limit: int) -> list[dict]:
        """Route C: MongoDB 结构化保底召回

        按 structured_filters 的 required_skills / work_years_min / education_min
        在 MongoDB 查匹配的简历，返回其 chunk 格式（candidate_id + parent_content）。

        入参:
            sf: structured_filters dict
            limit: 最多返回数量
        出参:
            [{"candidate_id", "parent_content", "chunk_id": "mongo_<rid>"}]
        """
        try:
            query: dict = {}
            skills = sf.get("required_skills", [])
            if skills:
                query["skills"] = {"$regex": "|".join(s.lower() for s in skills), "$options": "i"}
            years_min = sf.get("work_years_min")
            if years_min is not None:
                query["work_years"] = {"$gte": years_min}
            edu_min = sf.get("education_min")
            if edu_min is not None:
                query["education_level"] = {"$gte": edu_min}

            if not query:
                return []

            cursor = self.resumes_coll.find(query).limit(limit)
            docs = await cursor.to_list(length=limit)
            logger.info(f"Route C MongoDB 查询: {query} → {len(docs)} 条")
            return [
                {
                    "candidate_id": d.get("resume_id", ""),
                    "parent_content": d.get("summary", "") or d.get("name", "") + " " + " ".join(d.get("skills", []) or []),
                    "chunk_id": f"mongo_{d.get('resume_id', '')}",
                }
                for d in docs
            ]
        except Exception as e:
            logger.warning(f"Route C MongoDB 保底召回失败: {e}")
            return []

    async def _enrich_candidates(
        self,
        candidate_ids: list[str],
        query: str,
        chunks: list[dict],
        filters: dict = None,
    ) -> list[dict]:
        """拉取候选人元数据 + Python内存过滤 + LLM评分

        入参:
            candidate_ids: Milvus 返回的 resume_id 列表（已按简历级去重）
            query: 原始查询
            chunks: 检索chunks（每个resume_id一个最佳chunk，用于rerank_score）
            filters: 过滤条件（用于Python内存硬过滤兜底）
        出参:
            候选人卡片列表（按score降序）
        """
        filters = filters or {}
        if not candidate_ids:
            return []
        if self.resumes_coll is None:
            return []
        cursor = self.resumes_coll.find({"resume_id": {"$in": candidate_ids}})
        docs = await cursor.to_list(length=len(candidate_ids))
        logger.info(f"MongoDB 查询到 {len(docs)} 条简历文档")
        chunk_map = {c.get("candidate_id"): c for c in chunks}

        # Python 内存硬过滤（兜底 Milvus 层过滤，防止已有数据scalar字段未更新时过滤失效）
        edu_min = filters.get("education_min")
        years_min = filters.get("work_years_min")
        sal_max = filters.get("salary_max")
        required_skills = filters.get("required_skills", []) or []
        # 【关键修复】领域同义词扩展：nlp→[nlp,bert,fasttext,...]，html 保持严格
        # 领域词（nlp/cv/ai/ml/dl/frontend/backend/devops）代表技术方向，
        # 候选人可能写了领域下的具体技术（BERT/Transformer）但没写领域名，需要扩展避免误杀。
        # 具体技术（html/java/python/react）不扩展，保持精确匹配。
        try:
            from app.utils.skill_synonyms import expand_required_skills
            expanded_skills = expand_required_skills(required_skills)
        except Exception as e:
            logger.warning(f"required_skills 领域扩展失败，使用原始列表: {e}")
            expanded_skills = required_skills
        # 技能关键词统一小写，便于匹配
        required_skills_lower = [s.lower() for s in expanded_skills if isinstance(s, str)]
        filtered_docs: list[dict] = []
        for doc in docs:
            doc_edu = doc.get("education_level", 1)
            doc_years = doc.get("work_years", 0)
            doc_salary = doc.get("expected_salary", {}) or {}
            doc_sal_min = doc_salary.get("min", 0) or 0
            doc_sal_max = doc_salary.get("max", 0) or 0

            if edu_min is not None and doc_edu < edu_min:
                continue
            if years_min is not None and doc_years < years_min:
                continue
            if sal_max is not None:
                # 如果简历填了薪资，要求薪资下限<=预算；未填薪资(0)视为可谈，不强制过滤
                if doc_sal_min > 0 and doc_sal_min > sal_max:
                    continue
                # 如果填了薪资上限且也超过预算，过滤掉
                if doc_sal_max > 0 and doc_sal_max > sal_max and doc_sal_min == 0:
                    continue

            # 【关键修复】技能硬过滤：如果用户指定了required_skills，候选人必须至少具备其中一个
            if required_skills_lower:
                doc_skills = doc.get("skills", []) or []
                doc_skills_lower = {s.lower() for s in doc_skills if isinstance(s, str)}
                # 检查候选人技能中是否包含任一required_skill（子串匹配，如"html5"包含"html"）
                has_skill = any(
                    any(req in sk or sk in req for sk in doc_skills_lower)
                    for req in required_skills_lower
                )
                if not has_skill:
                    continue

            filtered_docs.append(doc)
        logger.info(
            f"Python硬过滤后 {len(filtered_docs)}/{len(docs)} 人 "
            f"(edu_min={edu_min}, years_min={years_min}, sal_max={sal_max}, required_skills={required_skills_lower})"
        )

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
                        "rerank": round(rerank_score * 100, 1),
                    },
                    "reason": score_data["reason"],
                    "tags": doc.get("tags", []),
                    "is_favorite": doc.get("is_favorite", False),
                    "summary": doc.get("summary", ""),
                }
            except Exception as e:
                logger.warning(f"候选人评分异常: {e}")
                return None

        results = await asyncio.gather(
            *[_score_one(doc) for doc in filtered_docs], return_exceptions=False
        )
        scored = [r for r in results if r is not None]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    async def _llm_score_multi(self, query: str, candidate: dict, rerank_score: float = 0.0) -> dict:
        """LLM 分维度评分（4 维度 + 代码加权overall + reason）

        入参:
            query: 原始查询
            candidate: 候选人文档
            rerank_score: reranker 得分（0-1，用于融合稳定性）
        出参:
            {skill, experience, education, salary, overall, reason}
        设计:
            - LLM 输出4个维度分（0-100）
            - overall 代码加权计算（0.35*skill + 0.25*experience + 0.15*education + 0.1*salary + 0.15*rerank*100）
              融合 rerank_score 降低 LLM 随机性导致的排名波动
            - LLM 失败时回退到 rerank_score
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

        try:
            data = json.loads(resp.strip())
            result = {
                "skill": float(data.get("skill", 0)),
                "experience": float(data.get("experience", 0)),
                "education": float(data.get("education", 0)),
                "salary": float(data.get("salary", 0)),
                "reason": data.get("reason", "评分暂不可用"),
            }
            # 代码加权：skill 35% + experience 25% + education 15% + salary 10% + rerank 15%
            # 融合 rerank_score 提高排名稳定性，避免 LLM 单次打分波动导致排名剧烈变化
            rerank_100 = min(100.0, max(0.0, rerank_score * 100))
            result["overall"] = round(
                0.35 * result["skill"]
                + 0.25 * result["experience"]
                + 0.15 * result["education"]
                + 0.10 * result["salary"]
                + 0.15 * rerank_100
            )
            return result
        except Exception as e:
            logger.warning(f"LLM 评分 JSON 解析失败，回退 rerank: {e}")
            fallback = rerank_score * 100
            return {
                "skill": fallback,
                "experience": fallback,
                "education": fallback,
                "salary": fallback,
                "overall": round(fallback),
                "reason": "基于语义相似度匹配",
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
        salary = candidate.get("expected_salary", {}) or {}
        sal_min = salary.get("min", 0)
        sal_max = salary.get("max", 0)
        sal_str = f"{sal_min}K-{sal_max}K" if sal_min or sal_max else "未填"

        work_exp = candidate.get("work_experience", []) or []
        work_desc = "; ".join([
            f"{w.get('company', '')}/{w.get('position', '')}"
            for w in work_exp[:3]
            if w.get("company") or w.get("position")
        ])

        projects = candidate.get("projects", []) or []
        project_desc = "; ".join([
            f"{p.get('name', '')}: {(p.get('description', '') or '')[:100]}"
            for p in projects[:3]
            if p.get("name")
        ])

        summary = (candidate.get("summary", "") or "")[:150]

        return (
            f"姓名:{name}, 工作年限:{work_years}年, 学历:{education}, 期望薪资:{sal_str}, "
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
