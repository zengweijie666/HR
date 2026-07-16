"""
文件名: app/models/chat.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 对话模型，对应 API-Design.md 三、Chat 与 10.4
"""
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: str


class SessionItem(BaseModel):
    session_id: str
    title: str
    last_message: str | None = None
    message_count: int = 0
    created_at: str
    updated_at: str


class ChatMessage(BaseModel):
    message_id: str
    session_id: str
    role: str
    content: str
    intent: str | None = None
    strategy: str | None = None
    candidates: list | None = None
    created_at: str


class SendMessageRequest(BaseModel):
    query: str = Field(..., min_length=1, description="用户查询，不可为空")
    context: dict = {}
