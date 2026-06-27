"""
文件名: app/api/users.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: 用户管理路由（全部 admin only），对应 API-Design 扩展
入参: HTTP 请求（路径参数 / 查询参数 / body）
出参: 统一响应 success/error
"""
from fastapi import APIRouter, Depends
from app.services.user_service import UserService
from app.api.deps import require_admin
from app.models.user import (
    CreateUserRequest, UpdateStatusRequest, ResetPasswordRequest,
)
from app.core.response import success

router = APIRouter()


@router.get("")
async def list_users(
    page: int = 1, page_size: int = 20,
    status: str | None = None, role: str | None = None,
    keyword: str | None = None,
    user: dict = Depends(require_admin),
):
    """用户列表（admin only）

    入参:
        page: 页码（默认 1）
        page_size: 每页数量（默认 20）
        status: 状态筛选（pending/approved/disabled）
        role: 角色筛选（admin/hr）
        keyword: 用户名/姓名关键词
    出参:
        {list, total, page, page_size, total_pages}
    """
    result = await UserService().list_users(
        page=page, page_size=page_size, status=status, role=role, keyword=keyword,
    )
    return success(data=result)


@router.post("")
async def create_user(body: CreateUserRequest, user: dict = Depends(require_admin)):
    """管理员直接开号（admin only，status=approved）

    入参:
        body: CreateUserRequest（username/password/role/email/name）
    出参:
        新建用户信息（不含 password_hash）
    """
    result = await UserService().create_user(
        username=body.username, password=body.password, role=body.role,
        email=body.email, name=body.name,
    )
    return success(data=result)


@router.get("/{user_id}")
async def get_user(user_id: str, user: dict = Depends(require_admin)):
    """用户详情（admin only）

    入参:
        user_id: 用户 ID
    出参:
        用户详情（不含 password_hash）
    """
    result = await UserService().get_user(user_id)
    return success(data=result)


@router.put("/{user_id}/approve")
async def approve(user_id: str, user: dict = Depends(require_admin)):
    """审批通过（admin only，pending → approved）

    入参:
        user_id: 用户 ID
    出参:
        success
    """
    await UserService().approve(user_id)
    return success()


@router.put("/{user_id}/reject")
async def reject(user_id: str, user: dict = Depends(require_admin)):
    """拒绝申请（admin only，直接删除记录）

    入参:
        user_id: 用户 ID
    出参:
        success
    """
    await UserService().reject(user_id)
    return success()


@router.put("/{user_id}/status")
async def update_status(user_id: str, body: UpdateStatusRequest, user: dict = Depends(require_admin)):
    """启用/禁用账号（admin only）

    入参:
        user_id: 用户 ID
        body: UpdateStatusRequest（status: approved/disabled）
    出参:
        success
    """
    await UserService().update_status(user_id, body.status)
    return success()


@router.put("/{user_id}/password")
async def reset_password(user_id: str, body: ResetPasswordRequest, user: dict = Depends(require_admin)):
    """重置密码（admin only）

    入参:
        user_id: 用户 ID
        body: ResetPasswordRequest（new_password）
    出参:
        success
    """
    await UserService().reset_password(user_id, body.new_password)
    return success()


@router.delete("/{user_id}")
async def delete_user(user_id: str, user: dict = Depends(require_admin)):
    """删除账号（admin only，不能删自己）

    入参:
        user_id: 待删除用户 ID
    出参:
        success
    异常:
        AuthError: 试图删除自己
    """
    await UserService().delete(user_id, current_user_id=user["user_id"])
    return success()
