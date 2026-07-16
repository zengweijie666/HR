"""
文件名: app/api/auth.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 认证路由，对应 API-Design.md 一、Auth
"""
from fastapi import APIRouter, Depends, Header
from app.models.auth import LoginRequest, RefreshRequest, TokenResponse, UserInfo
from app.models.user import RegisterRequest, ChangePasswordRequest
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.core.response import success

router = APIRouter()


@router.post("/login")
async def login(body: LoginRequest):
    result = await AuthService().login(body.email, body.password)
    return success(data=result.model_dump())


@router.post("/register")
async def register(body: RegisterRequest):
    """HR 自助注册申请（status=pending）"""
    result = await AuthService().register(
        username=body.username, password=body.password,
        email=body.email, name=body.name,
    )
    return success(data=result)


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    result = await AuthService().refresh(body.refresh_token)
    return success(data=result.model_dump())


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return success(data=UserInfo(**user).model_dump())


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user), authorization: str = Header(default=None)):
    """AC1.6: 退出登录，将当前 token 加入黑名单"""
    if not authorization or not authorization.startswith("Bearer "):
        return success()
    token = authorization[7:]
    await AuthService().logout(token)
    return success()


@router.put("/password")
async def change_password(body: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    """修改自己密码"""
    await AuthService().change_password(
        user_id=user["user_id"],
        old_password=body.old_password,
        new_password=body.new_password,
    )
    return success()
