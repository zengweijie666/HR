"""
文件名: app/services/dashboard_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 数据看板统计聚合
入参: 无（全量统计）
出参: 看板统计数据 dict
对应 Business-Requirements F22 (AC22.1-22.3)
"""
from app.core.database import MongoDB
from app.core.logger import logger


class DashboardService:
    """数据看板服务"""

    def __init__(self):
        self.resumes_coll = MongoDB.db.resumes if MongoDB.db else None
        self.sessions_coll = MongoDB.db.chat_sessions if MongoDB.db else None
        self.notes_coll = MongoDB.db.interview_notes if MongoDB.db else None

    async def get_stats(self) -> dict:
        """AC22.1-22.3: 看板统计

        入参: 无
        出参:
            {total_resumes, favorite_count, parsing_count, total_sessions,
             top_skills, education_distribution, salary_distribution}
        """
        if self.resumes_coll is None:
            return {
                "total_resumes": 0, "favorite_count": 0, "parsing_count": 0,
                "total_sessions": 0, "top_skills": [],
                "education_distribution": [], "salary_distribution": [],
            }

        total = await self.resumes_coll.count_documents({})
        favorite = await self.resumes_coll.count_documents({"is_favorite": True})
        parsing = await self.resumes_coll.count_documents(
            {"parse_status": {"$in": ["pending", "parsing"]}}
        )
        sessions = (
            await self.sessions_coll.count_documents({})
            if self.sessions_coll is not None
            else 0
        )

        top_skills = await self._top_skills()
        education_dist = await self._education_distribution()
        salary_dist = await self._salary_distribution()

        logger.info(
            f"看板统计: 简历={total}, 收藏={favorite}, 解析中={parsing}, 会话={sessions}"
        )
        return {
            "total_resumes": total,
            "favorite_count": favorite,
            "parsing_count": parsing,
            "total_sessions": sessions,
            "top_skills": top_skills,
            "education_distribution": education_dist,
            "salary_distribution": salary_dist,
        }

    async def _top_skills(self, limit: int = 10) -> list[dict]:
        """AC22.1: Top 技能聚合

        入参:
            limit: 返回数量
        出参:
            [{_id: skill, count: n}, ...]
        """
        pipeline = [
            {"$unwind": "$skills"},
            {"$group": {"_id": "$skills", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        cursor = self.resumes_coll.aggregate(pipeline)
        return await cursor.to_list(length=limit)

    async def _education_distribution(self) -> list[dict]:
        """AC22.2: 学历分布聚合

        入参: 无
        出参:
            [{_id: education, count: n}, ...]
        """
        pipeline = [
            {"$group": {"_id": "$education", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        cursor = self.resumes_coll.aggregate(pipeline)
        return await cursor.to_list(length=10)

    async def _salary_distribution(self) -> list[dict]:
        """AC22.3: 薪资分布聚合（按 expected_salary.min 分桶）

        入参: 无
        出参:
            [{_id: bucket, count: n}, ...]
        """
        pipeline = [
            {
                "$bucket": {
                    "groupBy": "$expected_salary.min",
                    "boundaries": [0, 15, 25, 100],
                    "default": "Other",
                    "output": {"count": {"$sum": 1}},
                }
            }
        ]
        cursor = self.resumes_coll.aggregate(pipeline)
        return await cursor.to_list(length=10)


dashboard_service = DashboardService()
