"""
文件名: app/api/candidates.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 候选人路由，对应 API-Design.md 五
入参: HTTP 请求（candidate_ids / columns / resume_id）
出参: Excel 文件 / 统一响应 success/error
"""
from fastapi import APIRouter, Depends, Response
from app.services.export_service import ExportService
from app.services.candidate_service import CandidateService
from app.api.deps import get_current_user
from app.core.response import success

router = APIRouter()


@router.post("/export")
async def export_excel(body: dict, user: dict = Depends(get_current_user)):
    """AC14.1: 导出 Excel"""
    excel_bytes = await ExportService().export_excel(
        resume_ids=body.get("resume_ids", []),
        columns=body.get("columns", ["name", "work_years", "skills"]),
    )
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=candidates.xlsx"},
    )


@router.get("/similar/{resume_id}")
async def get_similar(
    resume_id: str, top_k: int = 5,
    user: dict = Depends(get_current_user),
):
    """AC15.1: 相似候选人"""
    result = await CandidateService().get_similar(resume_id=resume_id, top_k=top_k)
    return success(data=result)


@router.post("/compare")
async def compare(body: dict, user: dict = Depends(get_current_user)):
    """AC16.1: 候选人对比"""
    result = await CandidateService().compare(
        candidate_ids=body.get("candidate_ids", [])
    )
    return success(data=result)
