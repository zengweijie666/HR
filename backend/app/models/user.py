"""
文件名: app/models/user.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: 用户管理相关 Pydantic 模型
入参/出参: 注册/创建/状态更新/密码重置请求体，用户列表项
"""
from pydantic import BaseModel, Field
from typing import Literal


class RegisterRequest(BaseModel):
    """HR 自助注册请求（status=pending）"""
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    password: str = Field(..., min_length=8, max_length=32, description="密码")
    email: str = Field(..., description="邮箱（必填，唯一）")
    name: str = Field(..., min_length=1, max_length=30, description="显示名（必填）")


class CreateUserRequest(BaseModel):
    """管理员直接开号请求（status=approved）"""
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8, max_length=32)
    email: str = Field(..., description="邮箱（必填，唯一）")
    name: str = Field(..., min_length=1, max_length=30)
    role: Literal["admin", "hr"] = Field(default="hr")


class UpdateStatusRequest(BaseModel):
    """启用/禁用账号"""
    status: Literal["approved", "disabled"]


class ResetPasswordRequest(BaseModel):
    """管理员重置密码"""
    new_password: str = Field(..., min_length=8, max_length=32)


class ChangePasswordRequest(BaseModel):
    """用户修改自己密码"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=32)


class UserItem(BaseModel):
    """用户列表项"""
    user_id: str
    username: str
    email: str | None = None
    name: str | None = None
    role: str
    status: str
    created_at: str
    updated_at: str
