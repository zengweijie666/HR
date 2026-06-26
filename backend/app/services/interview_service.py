"""
文件名: app/services/interview_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 面试题生成 + 面试评价 CRUD
入参: resume_id / job_title / interviewer / rating / result / content
出参: 面试题列表 / 评价文档
对应 Business-Requirements F20-F21 (AC20.1-20.2, AC21.1-21.3)
"""
import uuid
import json
from datetime import datetime, timezone
from app.core.database import MongoDB
from app.core.llm_client import llm_client
from app.core.logger import logger
from app.agent.prompts import INTERVIEW_QUESTION_PROMPT


class InterviewService:
    """面试服务"""

    def __init__(self):
        self.resumes_coll = MongoDB.db.resumes if MongoDB.db is not None else None
        self.notes_coll = MongoDB.db.interview_notes if MongoDB.db is not None else None

    async def generate_questions(
        self, resume_id: str, job_title: str = "", count: int = 5
    ) -> list[dict]:
        """AC20.1-20.2: LLM 生成面试题

        入参:
            resume_id: 简历 ID
            job_title: 岗位名称
            count: 题目数量
        出参:
            面试题列表 [{question, category}, ...]，简历不存在或生成失败时返回空列表
        """
        if self.resumes_coll is None:
            return []
        doc = await self.resumes_coll.find_one({"resume_id": resume_id})
        if not doc:
            logger.warning(f"生成面试题失败: 简历不存在 {resume_id}")
            return []

        prompt = INTERVIEW_QUESTION_PROMPT.format(
            job_title=job_title,
            name=doc.get("name", ""),
            skills=", ".join(doc.get("skills", [])),
            work_years=doc.get("work_years", 0),
            summary=doc.get("summary", ""),
            count=count,
        )
        try:
            resp = await llm_client.chat([{"role": "user", "content": prompt}])
            questions = json.loads(resp)
            logger.info(f"生成 {len(questions)} 道面试题, resume_id={resume_id}")
            return questions
        except Exception as e:
            logger.error(f"面试题生成失败: {e}")
            return []

    async def save_note(
        self,
        resume_id: str,
        interviewer: str,
        rating: int,
        result: str,
        content: str,
    ) -> dict:
        """AC21.1: 保存面试评价

        入参:
            resume_id: 简历 ID
            interviewer: 面试官
            rating: 评分 1-5
            result: 结果（通过/不通过/待定）
            content: 评价内容
        出参:
            评价文档（含 note_id / created_at）
        """
        note_id = f"n_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "note_id": note_id,
            "resume_id": resume_id,
            "interviewer": interviewer,
            "rating": rating,
            "result": result,
            "content": content,
            "created_at": now,
        }
        if self.notes_coll is not None:
            await self.notes_coll.insert_one(doc)
        doc.pop("_id", None)
        logger.info(f"保存面试评价 {note_id}, resume_id={resume_id}")
        return doc

    async def get_notes(self, resume_id: str) -> list[dict]:
        """AC21.2-21.3: 查询面试评价列表

        入参:
            resume_id: 简历 ID
        出参:
            评价列表（按 created_at 降序），无评价返回空列表
        """
        if self.notes_coll is None:
            return []
        cursor = self.notes_coll.find({"resume_id": resume_id}).sort("created_at", -1)
        notes = await cursor.to_list(length=100)
        for n in notes:
            n.pop("_id", None)
        return notes


interview_service = InterviewService()
