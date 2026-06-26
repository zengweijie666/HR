"""
文件名: app/utils/dedup.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 简历去重检查，通过 phone_hash + email_hash 查 MongoDB
入参: phone_hash, email_hash, MongoDB collection
出参: 命中的 resume_id 或 None
"""


class DedupChecker:
    """去重检查器"""

    def __init__(self, resumes_collection):
        self.coll = resumes_collection

    async def check(self, phone_hash: str, email_hash: str) -> str | None:
        """返回已存在 resume_id，无重复返回 None"""
        doc = await self.coll.find_one(
            {"$or": [{"phone_hash": phone_hash}, {"email_hash": email_hash}]},
            {"resume_id": 1, "_id": 0}
        )
        return doc["resume_id"] if doc else None
