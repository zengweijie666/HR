"""
文件名: app/models/auth.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 认证相关模型，对应 API-Design.md 一、Auth
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class RefreshRequest(BaseModel):
    refresh_token: str


class UserInfo(BaseModel):
    user_id: str
    username: str
    role: str = "hr"
    email: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo
