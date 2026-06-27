"""
文件名: app/models/email.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 邮件模型 + 邮件模板模型，对应 API-Design.md 六、Email
入参/出参: 邮件请求 / 模板 CRUD 请求体 / 模板项
"""
from pydantic import BaseModel, Field
from typing import Literal


class EmailRequest(BaseModel):
    to_email: str
    cc: list[str] = []
    subject: str | None = None
    query: str | None = None
    candidate_ids: list[str]
    include_excel: bool = True
    remark: str | None = None


class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str | None = None
    use_ssl: bool = True
    sender_name: str = "TalentSense HR"
    signature: str = "—— TalentSense HR 推荐系统"


class TemplateCreateRequest(BaseModel):
    """创建模板请求"""
    name: str = Field(..., min_length=1, max_length=50, description="模板名称")
    subject: str = Field(..., min_length=1, max_length=200, description="邮件主题（支持变量）")
    body: str = Field(..., min_length=1, description="邮件正文（HTML，支持变量）")
    category: Literal["interview", "offer", "reject", "progress", "custom"] = Field(default="custom")


class TemplateUpdateRequest(BaseModel):
    """更新模板请求"""
    name: str | None = Field(default=None, min_length=1, max_length=50)
    subject: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1)
    category: Literal["interview", "offer", "reject", "progress", "custom"] | None = None


class TemplateItem(BaseModel):
    """模板列表项"""
    template_id: str
    name: str
    subject: str
    body: str
    category: str
    is_builtin: bool = False
    created_at: str
    updated_at: str


class SendMailRequest(BaseModel):
    """发送邮件请求（模板或自定义）"""
    to_email: str = Field(..., description="收件人邮箱")
    template_id: str | None = Field(default=None, description="模板 ID（与 custom 二选一）")
    custom_subject: str | None = Field(default=None, description="自定义主题（template_id 为空时必填）")
    custom_body: str | None = Field(default=None, description="自定义正文（template_id 为空时必填）")
    variables: dict = Field(default_factory=dict, description="模板变量")


class SendTestRequest(BaseModel):
    """发送测试邮件请求"""
    to_email: str = Field(..., description="测试收件人邮箱")
