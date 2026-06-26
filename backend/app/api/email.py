"""
文件名: app/api/email.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 邮件路由，对应 API-Design.md 六
入参: HTTP 请求（to_email / candidate_ids / config）
出参: 统一响应 success/error
"""
from fastapi import APIRouter, Depends
from app.services.email_service import EmailService
from app.api.deps import get_current_user
from app.core.response import success

router = APIRouter()


@router.post("/send")
async def send_recommendation(body: dict, user: dict = Depends(get_current_user)):
    """AC17.1: 发送推荐邮件"""
    result = await EmailService().send_recommendation(
        to_email=body.get("to_email", ""),
        candidate_ids=body.get("candidate_ids", []),
        job_title=body.get("job_title", ""),
    )
    return success(data=result)


@router.get("/config")
async def get_config(user: dict = Depends(get_current_user)):
    """AC18.1: 获取 SMTP 配置（脱敏）"""
    result = await EmailService().get_config()
    return success(data=result)


@router.put("/config")
async def update_config(body: dict, user: dict = Depends(get_current_user)):
    """AC18.2: 更新 SMTP 配置（加密存储）"""
    await EmailService().update_config(body)
    return success()
