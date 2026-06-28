"""
文件名: app/api/deps.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: FastAPI 依赖注入：get_current_user / require_admin
    鉴权成功后自动绑定 user_id 到日志上下文，便于按用户追踪链路
"""
from fastapi import Depends, Header
from app.services.auth_service import AuthService
from app.core.exceptions import AuthError, ForbiddenError
from app.core.logger import bind_request_context


async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """JWT 校验，返回 user payload"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Token 格式错误")
    token = authorization[7:]
    user = await AuthService().verify_token(token)
    bind_request_context(user_id=user.get("user_id", ""))
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """要求 admin 角色，hr 调用抛 ForbiddenError（403）"""
    if user.get("role") != "admin":
        raise ForbiddenError("需要管理员权限")
    return user
