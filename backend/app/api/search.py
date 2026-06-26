"""
文件名: app/api/search.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 检索路由，对应 API-Design.md 四
入参: HTTP 请求（query / filters / top_k）
出参: 统一响应 success/error
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.services.search_service import SearchService
from app.api.deps import get_current_user
from app.core.response import success

router = APIRouter()


class SearchRequest(BaseModel):
    """检索请求体"""
    query: str = Field(..., description="自然语言查询")
    filters: dict = Field(default_factory=dict, description="过滤条件")
    top_k: int = Field(default=10, ge=1, le=50, description="返回数量")


@router.post("")
async def search(body: SearchRequest, user: dict = Depends(get_current_user)):
    """AC13.1-13.4: 自然语言检索候选人"""
    result = await SearchService().search(
        query=body.query,
        filters=body.filters,
        top_k=body.top_k,
    )
    return success(data=result)
