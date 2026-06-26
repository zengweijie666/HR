"""
文件名: app/api/interview.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 面试路由，对应 API-Design.md 八
入参: HTTP 请求（resume_id / job_title / interviewer / rating / result / content）
出参: 统一响应 success/error
"""
from fastapi import APIRouter, Depends
from app.services.interview_service import InterviewService
from app.api.deps import get_current_user
from app.core.response import success

router = APIRouter()


@router.post("/questions")
async def generate_questions(body: dict, user: dict = Depends(get_current_user)):
    """AC20.1-20.2: LLM 生成面试题"""
    result = await InterviewService().generate_questions(
        resume_id=body["resume_id"],
        job_title=body.get("job_title", ""),
        count=body.get("count", 5),
    )
    return success(data=result)


@router.post("/notes")
async def save_note(body: dict, user: dict = Depends(get_current_user)):
    """AC21.1: 保存面试评价"""
    result = await InterviewService().save_note(
        resume_id=body["resume_id"],
        interviewer=body.get("interviewer", user.get("username", "")),
        rating=body["rating"],
        result=body.get("result", ""),
        content=body.get("content", ""),
    )
    return success(data=result)


@router.get("/notes/{resume_id}")
async def get_notes(resume_id: str, user: dict = Depends(get_current_user)):
    """AC21.2-21.3: 查询面试评价列表"""
    result = await InterviewService().get_notes(resume_id)
    return success(data=result)
