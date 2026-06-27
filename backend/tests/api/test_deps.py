"""
文件名: tests/api/test_deps.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: deps.require_admin 单元测试
"""
import pytest
from app.api.deps import require_admin
from app.core.exceptions import ForbiddenError


@pytest.mark.asyncio
async def test_require_admin_pass():
    """admin 角色通过"""
    user = await require_admin({"user_id": "u1", "username": "admin", "role": "admin"})
    assert user["role"] == "admin"


@pytest.mark.asyncio
async def test_require_admin_reject_hr():
    """hr 角色被拒绝"""
    with pytest.raises(ForbiddenError) as exc:
        await require_admin({"user_id": "u2", "username": "hr", "role": "hr"})
    assert "管理员" in exc.value.message
