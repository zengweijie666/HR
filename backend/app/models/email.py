"""
文件名: app/models/email.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 邮件模型，对应 API-Design.md 六、Email
"""
from pydantic import BaseModel


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
