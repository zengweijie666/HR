"""
文件名: app/api/email.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 邮件路由（模板 CRUD + 发送 + SMTP 配置），对应 API-Design.md 六
入参: HTTP 请求（to_email / candidate_ids / config / template）
出参: 统一响应 success/error
"""
from fastapi import APIRouter, Depends
from app.services.email_service import EmailService
from app.services.email_template_service import EmailTemplateService
from app.api.deps import get_current_user, require_admin
from app.models.email import (
    TemplateCreateRequest, TemplateUpdateRequest,
    SendMailRequest, SendTestRequest,
)
from app.core.response import success

router = APIRouter()


@router.post("/send")
async def send_mail(body: SendMailRequest, user: dict = Depends(get_current_user)):
    """发送邮件（模板或自定义）"""
    result = await EmailService().send_mail(
        to_email=body.to_email, template_id=body.template_id,
        custom_subject=body.custom_subject, custom_body=body.custom_body,
        variables=body.variables,
    )
    return success(data=result)


@router.post("/send-test")
async def send_test(body: SendTestRequest, user: dict = Depends(require_admin)):
    """发送测试邮件（admin only）"""
    result = await EmailService().send_test(to_email=body.to_email)
    return success(data=result)


@router.get("/templates")
async def list_templates(category: str | None = None, user: dict = Depends(get_current_user)):
    """邮件模板列表（登录用户可查，admin 才能增删改）"""
    result = await EmailTemplateService().list_templates(category=category)
    return success(data=result)


@router.post("/templates")
async def create_template(body: TemplateCreateRequest, user: dict = Depends(require_admin)):
    """创建模板（admin only）"""
    result = await EmailTemplateService().create_template(
        name=body.name, subject=body.subject, body=body.body, category=body.category,
    )
    return success(data=result)


@router.put("/templates/{template_id}")
async def update_template(template_id: str, body: TemplateUpdateRequest, user: dict = Depends(require_admin)):
    """更新模板（admin only，预置模板不可改）"""
    result = await EmailTemplateService().update_template(
        template_id, name=body.name, subject=body.subject, body=body.body, category=body.category,
    )
    return success(data=result)


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, user: dict = Depends(require_admin)):
    """删除模板（admin only，预置模板不可删）"""
    await EmailTemplateService().delete_template(template_id)
    return success()


@router.get("/config")
async def get_config(user: dict = Depends(require_admin)):
    """AC18.1: 获取 SMTP 配置（脱敏，仅 admin）"""
    result = await EmailService().get_config()
    return success(data=result)


@router.put("/config")
async def update_config(body: dict, user: dict = Depends(require_admin)):
    """AC18.2: 更新 SMTP 配置（加密存储，仅 admin）"""
    await EmailService().update_config(body)
    return success()

