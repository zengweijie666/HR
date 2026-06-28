"""
文件名: app/services/dashboard_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 数据看板统计聚合
入参: 无（全量统计）
出参: 看板统计数据 dict
对应 Business-Requirements F22 (AC22.1-22.3)
"""
from datetime import datetime, timedelta, timezone

from app.core.database import MongoDB
from app.core.logger import logger


class DashboardService:
    """数据看板服务"""

    def __init__(self):
        pass

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
    def sessions_coll(self):
        """延迟获取 MongoDB chat_sessions collection"""
        if hasattr(self, "_sessions_coll"):
            return self._sessions_coll
        return MongoDB.db.chat_sessions if MongoDB.db is not None else None

    @sessions_coll.setter
    def sessions_coll(self, value):
        """测试注入用"""
        self._sessions_coll = value

    @property
    def notes_coll(self):
        """延迟获取 MongoDB interview_notes collection"""
        if hasattr(self, "_notes_coll"):
            return self._notes_coll
        return MongoDB.db.interview_notes if MongoDB.db is not None else None

    @notes_coll.setter
    def notes_coll(self, value):
        """测试注入用"""
        self._notes_coll = value

    async def get_stats(self) -> dict:
        """AC22.1-22.3: 看板统计（含招聘漏斗、入库趋势、经验分布、面试结果）

        入参: 无
        出参: 看板统计数据 dict
        """
        if self.resumes_coll is None:
            return {
                "total_resumes": 0, "favorite_count": 0, "parsing_count": 0,
                "total_sessions": 0, "top_skills": [],
                "education_distribution": [], "salary_distribution": [],
                "recruitment_funnel": [], "resume_trend": [],
                "work_years_distribution": [], "interview_result_distribution": [],
            }

        total = await self.resumes_coll.count_documents({})
        favorite = await self.resumes_coll.count_documents({"is_favorite": True})
        parsing = await self.resumes_coll.count_documents(
            {"parse_info.parse_status": {"$in": ["pending", "parsing"]}}
        )
        sessions = (
            await self.sessions_coll.count_documents({})
            if self.sessions_coll is not None
            else 0
        )

        top_skills = await self._top_skills()
        education_dist = await self._education_distribution()
        salary_dist = await self._salary_distribution()
        funnel = await self._recruitment_funnel()
        trend = await self._resume_trend(days=30)
        work_years_dist = await self._work_years_distribution()
        interview_dist = await self._interview_result_distribution()

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
            "recruitment_funnel": funnel,
            "resume_trend": trend,
            "work_years_distribution": work_years_dist,
            "interview_result_distribution": interview_dist,
        }

    async def _top_skills(self, limit: int = 10) -> list[dict]:
        """AC22.1: Top 技能聚合

        入参: limit 返回数量
        出参: [{_id: skill, count: n}, ...]
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

        出参: [{_id: education, count: n}, ...]
        """
        pipeline = [
            {"$group": {"_id": "$education", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        cursor = self.resumes_coll.aggregate(pipeline)
        return await cursor.to_list(length=10)

    async def _salary_distribution(self) -> list[dict]:
        """AC22.3: 薪资分布聚合（按 expected_salary.min 分桶）

        出参: [{_id: bucket, count: n}, ...]
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

    async def _recruitment_funnel(self) -> list[dict]:
        """招聘漏斗：总简历 → 解析完成 → 收藏 → 有面试评价 → 面试通过

        出参: [{stage: "简历入库", count: n}, ...]
        """
        total = await self.resumes_coll.count_documents({})
        parsed = await self.resumes_coll.count_documents(
            {"parse_info.parse_status": "completed"}
        )
        fav = await self.resumes_coll.count_documents({"is_favorite": True})

        interviewed = 0
        passed = 0
        if self.notes_coll is not None:
            interviewed = await self.notes_coll.count_documents({})
            passed = await self.notes_coll.count_documents({"result": "通过"})

        return [
            {"stage": "简历入库", "count": total},
            {"stage": "解析完成", "count": parsed},
            {"stage": "收藏候选", "count": fav},
            {"stage": "安排面试", "count": interviewed},
            {"stage": "面试通过", "count": passed},
        ]

    async def _resume_trend(self, days: int = 30) -> list[dict]:
        """简历入库趋势（近N天按日聚合）

        入参: days 统计天数
        出参: [{date: "2026-06-01", count: n}, ...]
        """
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=days)
        pipeline = [
            {"$match": {"created_at": {"$gte": since.isoformat()}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": {"$dateFromString": {"dateString": "$created_at"}},
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        cursor = self.resumes_coll.aggregate(pipeline)
        raw = await cursor.to_list(length=days)

        # 补全空日期，确保连续
        date_map = {item["_id"]: item["count"] for item in raw}
        result = []
        for i in range(days):
            d = (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            result.append({"date": d, "count": date_map.get(d, 0)})
        return result

    async def _work_years_distribution(self) -> list[dict]:
        """工作经验分布（按年限分桶：0-3年/3-5年/5-10年/10+年）

        出参: [{range: "0-3年", count: n}, ...]
        """
        pipeline = [
            {
                "$bucket": {
                    "groupBy": "$work_years",
                    "boundaries": [0, 3, 5, 10, 100],
                    "default": "Other",
                    "output": {"count": {"$sum": 1}},
                }
            }
        ]
        cursor = self.resumes_coll.aggregate(pipeline)
        raw = await cursor.to_list(length=10)

        label_map = {0: "0-3年", 3: "3-5年", 5: "5-10年", 10: "10+年"}
        return [
            {"range": label_map.get(item["_id"], str(item["_id"])), "count": item["count"]}
            for item in raw
        ]

    async def _interview_result_distribution(self) -> list[dict]:
        """面试结果统计（通过/不通过/待定）

        出参: [{result: "通过", count: n}, ...]
        """
        if self.notes_coll is None:
            return []
        pipeline = [
            {"$group": {"_id": "$result", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        cursor = self.notes_coll.aggregate(pipeline)
        raw = await cursor.to_list(length=10)
        return [
            {"result": item["_id"] or "未设置", "count": item["count"]}
            for item in raw
        ]


dashboard_service = DashboardService()
