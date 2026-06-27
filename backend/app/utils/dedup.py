"""
文件名: app/utils/dedup.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 简历去重检查，通过 basic_info.phone_hash + basic_info.email_hash 查 MongoDB
入参: phone_hash, email_hash, MongoDB collection
出参: 命中的 resume_id 或 None
"""


class DedupChecker:
    """去重检查器"""

    def __init__(self, resumes_collection):
        self.coll = resumes_collection

    async def check(self, phone_hash: str, email_hash: str) -> str | None:
        """返回已存在 resume_id，无重复返回 None

        注意：phone_hash/email_hash 存储在 basic_info 子文档中，
        查询路径必须为 basic_info.phone_hash / basic_info.email_hash。
        """
        if not phone_hash and not email_hash:
            return None
        conditions = []
        if phone_hash:
            conditions.append({"basic_info.phone_hash": phone_hash})
        if email_hash:
            conditions.append({"basic_info.email_hash": email_hash})
        query = {"$or": conditions} if len(conditions) > 1 else conditions[0]
        doc = await self.coll.find_one(query, {"resume_id": 1, "_id": 0})
        return doc["resume_id"] if doc else None
