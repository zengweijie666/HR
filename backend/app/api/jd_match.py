"""
文件名: app/api/jd_match.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: JD 匹配路由，对应 API-Design.md 五
入参: HTTP 请求（jd_text / top_k）
出参: 统一响应 success/error
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.services.jd_match_service import JdMatchService
from app.api.deps import get_current_user
from app.core.response import success

router = APIRouter()


class JdMatchRequest(BaseModel):
    """JD 匹配请求体"""
    jd_text: str = Field(..., description="JD 原文")
    top_k: int = Field(default=10, ge=1, le=50, description="返回候选人数量")


@router.post("")
async def match_jd(body: JdMatchRequest, user: dict = Depends(get_current_user)):
    """AC19.1-19.2: JD 匹配候选人"""
    result = await JdMatchService().match_jd(
        jd_text=body.jd_text,
        top_k=body.top_k,
    )
    return success(data=result)
