"""
文件名: app/api/dashboard.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 看板路由，对应 API-Design.md 九
入参: HTTP 请求（无）
出参: 统一响应 success/error
"""
from fastapi import APIRouter, Depends
from app.services.dashboard_service import DashboardService
from app.api.deps import get_current_user
from app.core.response import success

router = APIRouter()


@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    """AC22.1-22.3: 获取看板统计数据"""
    result = await DashboardService().get_stats()
    return success(data=result)
