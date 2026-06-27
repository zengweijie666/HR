"""
文件名: tests/services/test_auth_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试认证服务
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.auth_service import AuthService
from app.core.exceptions import AuthError


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


# ========== Task 4: register / login status / change_password ==========

@pytest.mark.asyncio
async def test_register_success():
    """注册成功，status=pending, role=hr"""
    svc = AuthService()
    svc.users_coll = AsyncMock()
    svc.users_coll.find_one.return_value = None
    svc.users_coll.insert_one.return_value = MagicMock(inserted_id="oid")
    result = await svc.register(username="zhangsan", password="Pass1234", email="z@test.com", name="张三")
    assert result["username"] == "zhangsan"
    assert result["status"] == "pending"
    # 校验插入的文档字段
    doc = svc.users_coll.insert_one.call_args.args[0]
    assert doc["role"] == "hr"
    assert doc["status"] == "pending"
    assert doc["email"] == "z@test.com"
    assert doc["name"] == "张三"
    assert "password_hash" in doc


@pytest.mark.asyncio
async def test_register_username_exists():
    """用户名已存在抛 CONFLICT"""
    from app.core.exceptions import BizError
    from app.core.response import CODE
    svc = AuthService()
    svc.users_coll = AsyncMock()
    svc.users_coll.find_one.return_value = {"username": "zhangsan"}
    with pytest.raises(BizError) as exc:
        await svc.register(username="zhangsan", password="Pass1234")
    assert exc.value.code == CODE.CONFLICT


@pytest.mark.asyncio
async def test_login_pending_rejected():
    """pending 状态拒绝登录"""
    svc = AuthService()
    svc.users_coll = AsyncMock()
    svc.users_coll.find_one.return_value = {
        "user_id": "u1", "username": "zhangsan",
        "password_hash": AuthService.hash_password("Pass1234"),
        "role": "hr", "status": "pending",
    }
    svc.redis = AsyncMock()
    svc.redis.exists.return_value = 0
    with pytest.raises(AuthError) as exc:
        await svc.login("zhangsan", "Pass1234")
    assert "待审批" in exc.value.message


@pytest.mark.asyncio
async def test_login_disabled_rejected():
    """disabled 状态拒绝登录"""
    svc = AuthService()
    svc.users_coll = AsyncMock()
    svc.users_coll.find_one.return_value = {
        "user_id": "u1", "username": "zhangsan",
        "password_hash": AuthService.hash_password("Pass1234"),
        "role": "hr", "status": "disabled",
    }
    svc.redis = AsyncMock()
    svc.redis.exists.return_value = 0
    with pytest.raises(AuthError) as exc:
        await svc.login("zhangsan", "Pass1234")
    assert "已禁用" in exc.value.message


@pytest.mark.asyncio
async def test_change_password_success():
    """修改自己密码成功"""
    svc = AuthService()
    svc.users_coll = AsyncMock()
    svc.users_coll.find_one.return_value = {
        "user_id": "u1", "username": "admin",
        "password_hash": AuthService.hash_password("Old1234"),
    }
    svc.users_coll.update_one.return_value = MagicMock(modified_count=1)
    await svc.change_password(user_id="u1", old_password="Old1234", new_password="New1234")
    svc.users_coll.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_change_password_old_wrong():
    """旧密码错误抛 AuthError"""
    svc = AuthService()
    svc.users_coll = AsyncMock()
    svc.users_coll.find_one.return_value = {
        "user_id": "u1", "username": "admin",
        "password_hash": AuthService.hash_password("Old1234"),
    }
    with pytest.raises(AuthError):
        await svc.change_password(user_id="u1", old_password="Wrong", new_password="New1234")
