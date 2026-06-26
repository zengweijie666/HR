"""
文件名: app/api/resumes.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 简历路由，对应 API-Design.md 二
入参: HTTP 请求（文件/查询参数/路径参数）
出参: 统一响应 success/error
"""
from fastapi import APIRouter, Depends, UploadFile, File
from app.services.resume_service import ResumeService
from app.api.deps import get_current_user
from app.core.response import success

router = APIRouter()


@router.post("/upload")
async def upload(file: UploadFile = File(...), overwrite: bool = False, user: dict = Depends(get_current_user)):
    """AC2.1: 上传简历文件"""
    content = await file.read()
    result = await ResumeService().upload(content, file.filename, file.content_type, overwrite)
    return success(data=result)


@router.get("")
async def list_resumes(
    page: int = 1, page_size: int = 20,
    keyword: str | None = None, tag: str | None = None,
    is_favorite: bool | None = None, education_min: int | None = None,
    work_years_min: int | None = None, salary_min: int | None = None,
    salary_max: int | None = None, status: str | None = None,
    user: dict = Depends(get_current_user),
):
    """AC3.1-3.8: 简历列表查询"""
    result = await ResumeService().list(
        page=page, page_size=page_size, keyword=keyword, tag=tag,
        is_favorite=is_favorite, education_min=education_min,
        work_years_min=work_years_min, salary_min=salary_min,
        salary_max=salary_max, status=status,
    )
    return success(data=result)


@router.get("/{resume_id}")
async def get_detail(resume_id: str, user: dict = Depends(get_current_user)):
    """AC4.1-4.4: 获取简历详情"""
    result = await ResumeService().get_detail(resume_id)
    return success(data=result)


@router.delete("/{resume_id}")
async def delete(resume_id: str, user: dict = Depends(get_current_user)):
    """AC6.1-6.4: 删除简历"""
    await ResumeService().delete(resume_id)
    return success()


@router.get("/{resume_id}/preview")
async def preview(resume_id: str, user: dict = Depends(get_current_user)):
    """AC5.1-5.2: 生成预签名 URL"""
    result = await ResumeService().get_preview_url(resume_id)
    return success(data=result)
