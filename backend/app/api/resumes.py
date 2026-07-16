"""
文件名: app/api/resumes.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 简历路由，对应 API-Design.md 二
入参: HTTP 请求（文件/查询参数/路径参数）
出参: 统一响应 success/error
"""
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File
from pydantic import BaseModel, Field
from app.services.resume_service import ResumeService
from app.services.tag_service import TagService
from app.api.deps import get_current_user, require_admin
from app.core.response import success

router = APIRouter()


class UpdateTagsRequest(BaseModel):
    """标签更新请求体"""
    tags: list[str] = Field(default_factory=list, description="标签列表")


class ToggleFavoriteRequest(BaseModel):
    """收藏切换请求体"""
    is_favorite: bool = Field(..., description="是否收藏")


class UpdateNotesRequest(BaseModel):
    """备注更新请求体"""
    notes: str = Field(default="", description="评价备注")


@router.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    overwrite: bool = False,
    user: dict = Depends(get_current_user),
):
    """AC2.1: 上传简历文件

    解析（LLM 结构化 + BGE-M3 编码 + Milvus 写入）较慢，
    通过 BackgroundTasks 异步执行，接口立即返回 parse_status="parsing"。
    前端通过列表刷新或详情查看最终状态。
    """
    content = await file.read()
    service = ResumeService()
    result = await service.upload(content, file.filename, file.content_type, overwrite, background_tasks)
    return success(data=result)


@router.get("")
async def list_resumes(
    page: int = 1, page_size: int = 20,
    keyword: str | None = None, tag: str | None = None,
    is_favorite: bool | None = None, education_min: int | None = None,
    work_years_min: int | None = None, salary_min: int | None = None,
    salary_max: int | None = None, status: str | None = None,
    date_from: str | None = None, date_to: str | None = None,
    sort_by: str = "created_at", sort_order: str = "desc",
    user: dict = Depends(get_current_user),
):
    """AC3.1-3.8: 简历列表查询（根据角色返回原始/脱敏手机邮箱，支持日期范围筛选和排序）"""
    result = await ResumeService().list(
        page=page, page_size=page_size, keyword=keyword, tag=tag,
        is_favorite=is_favorite, education_min=education_min,
        work_years_min=work_years_min, salary_min=salary_min,
        salary_max=salary_max, status=status,
        date_from=date_from, date_to=date_to,
        sort_by=sort_by, sort_order=sort_order,
        current_user=user,
    )
    return success(data=result)


@router.get("/{resume_id}")
async def get_detail(resume_id: str, user: dict = Depends(get_current_user)):
    """AC4.1-4.4: 获取简历详情（根据角色返回原始/脱敏手机邮箱）"""
    result = await ResumeService().get_detail(resume_id, current_user=user)
    return success(data=result)


@router.delete("/{resume_id}")
async def delete(resume_id: str, user: dict = Depends(require_admin)):
    """AC6.1-6.4: 删除简历（仅 admin）"""
    await ResumeService().delete(resume_id)
    return success()


@router.get("/{resume_id}/preview")
async def preview(resume_id: str, user: dict = Depends(get_current_user)):
    """AC5.1-5.2: 生成预签名 URL"""
    result = await ResumeService().get_preview_url(resume_id)
    return success(data=result)


@router.put("/{resume_id}/tags")
async def update_tags(resume_id: str, body: UpdateTagsRequest, user: dict = Depends(get_current_user)):
    """AC7.1/7.4: 全量覆盖标签"""
    result = await TagService().update_tags(resume_id, body.tags)
    return success(data=result)


@router.put("/{resume_id}/favorite")
async def toggle_favorite(resume_id: str, body: ToggleFavoriteRequest, user: dict = Depends(get_current_user)):
    """AC8.1/8.2: 切换收藏状态"""
    result = await TagService().toggle_favorite(resume_id, body.is_favorite)
    return success(data=result)


@router.put("/{resume_id}/notes")
async def update_notes(resume_id: str, body: UpdateNotesRequest, user: dict = Depends(get_current_user)):
    """AC9.1: 更新评价备注"""
    result = await TagService().update_notes(resume_id, body.notes)
    return success(data=result)
