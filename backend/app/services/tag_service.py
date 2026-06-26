"""
文件名: app/services/tag_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 标签/收藏/评价服务，对应 API-Design.md 2.6-2.8
入参: resume_id / tags / is_favorite / notes
出参: 更新后的字段字典
"""
from datetime import datetime, timezone
from app.core.database import MongoDB


class TagService:
    """标签/收藏/评价服务"""

    def __init__(self):
        self.coll = MongoDB.db.resumes if MongoDB.db else None

    async def update_tags(self, resume_id: str, tags: list[str]) -> dict:
        """AC7.1/7.4: 全量覆盖标签

        入参:
            resume_id: 简历 ID
            tags: 新标签列表（空列表表示清空）
        出参:
            {"resume_id", "tags"}
        """
        await self.coll.update_one(
            {"resume_id": resume_id},
            update={"$set": {"tags": tags, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        return {"resume_id": resume_id, "tags": tags}

    async def toggle_favorite(self, resume_id: str, is_favorite: bool) -> dict:
        """AC8.1/8.2: 切换收藏状态

        入参:
            resume_id: 简历 ID
            is_favorite: 是否收藏
        出参:
            {"resume_id", "is_favorite"}
        """
        await self.coll.update_one(
            {"resume_id": resume_id},
            update={"$set": {"is_favorite": is_favorite, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        return {"resume_id": resume_id, "is_favorite": is_favorite}

    async def update_notes(self, resume_id: str, notes: str) -> dict:
        """AC9.1: 更新评价备注

        入参:
            resume_id: 简历 ID
            notes: 评价内容
        出参:
            {"resume_id", "notes"}
        """
        await self.coll.update_one(
            {"resume_id": resume_id},
            update={"$set": {"notes": notes, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        return {"resume_id": resume_id, "notes": notes}
