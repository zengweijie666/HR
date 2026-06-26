"""
文件名: app/api/deps.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: FastAPI 依赖注入：get_current_user
"""
from fastapi import Header
from app.services.auth_service import AuthService
from app.core.exceptions import AuthError


async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """JWT 校验，返回 user payload"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Token 格式错误")
    token = authorization[7:]
    return await AuthService().verify_token(token)
