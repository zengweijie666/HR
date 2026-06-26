"""
文件名: tests/services/test_auth_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试认证服务
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service(monkeypatch):
    svc = AuthService()
    svc.users_coll = AsyncMock()
    svc.redis = AsyncMock()
    # 默认 token 未加入黑名单（exists 返回 0）
    svc.redis.exists.return_value = 0
    return svc


@pytest.mark.asyncio
async def test_login_success(auth_service):
    """AC1.1: 正确账号密码登录返回 token"""
    auth_service.users_coll.find_one.return_value = {
        "user_id": "u1", "username": "admin",
        "password_hash": AuthService.hash_password("123456"),
        "role": "hr", "email": "a@b.com"
    }
    result = await auth_service.login("admin", "123456")
    assert result.access_token
    assert result.refresh_token
    assert result.user.username == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(auth_service):
    """AC1.2: 错误密码返回 1001"""
    auth_service.users_coll.find_one.return_value = {
        "user_id": "u1", "username": "admin",
        "password_hash": AuthService.hash_password("123456"),
    }
    from app.core.exceptions import AuthError
    with pytest.raises(AuthError):
        await auth_service.login("admin", "wrong")


@pytest.mark.asyncio
async def test_verify_token_valid(auth_service):
    """AC1.3: 有效 token 通过"""
    token = AuthService.create_access_token({"user_id": "u1", "username": "admin"})
    user = await auth_service.verify_token(token)
    assert user["user_id"] == "u1"


@pytest.mark.asyncio
async def test_verify_token_blacklisted(auth_service):
    """AC1.6: 登出后 token 失效"""
    token = AuthService.create_access_token({"user_id": "u1", "username": "admin"})
    auth_service.redis.exists.return_value = 1
    from app.core.exceptions import AuthError
    with pytest.raises(AuthError):
        await auth_service.verify_token(token)


@pytest.mark.asyncio
async def test_logout_adds_blacklist(auth_service):
    """登出加入黑名单"""
    token = AuthService.create_access_token({"user_id": "u1", "username": "admin"})
    await auth_service.logout(token)
    auth_service.redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token(auth_service):
    """AC1.5: refresh_token 换新 access_token"""
    refresh = AuthService.create_refresh_token({"user_id": "u1", "username": "admin"})
    auth_service.redis.exists.return_value = 0
    result = await auth_service.refresh(refresh)
    assert result.access_token
