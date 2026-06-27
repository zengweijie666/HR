"""
文件名: tests/services/test_user_service.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: UserService 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.user_service import UserService
from app.core.exceptions import BizError, AuthError, NotFoundError, ConflictError


def _make_user(user_id="u1", username="zhangsan", role="hr", status="pending"):
    return {
        "user_id": user_id, "username": username, "email": "z@t.com",
        "name": "张三", "role": role, "status": status,
        "password_hash": "hash", "created_at": "2026-06-27", "updated_at": "2026-06-27",
    }


@pytest.mark.asyncio
async def test_list_users():
    svc = UserService()
    svc.users_coll = MagicMock()
    cursor = MagicMock()
    inner = MagicMock()
    # mock 不模拟 projection，手动构造已过滤 password_hash 的返回
    filtered = {k: v for k, v in _make_user().items() if k != "password_hash"}
    inner.to_list = AsyncMock(return_value=[filtered])
    cursor.skip = MagicMock(return_value=MagicMock(limit=MagicMock(return_value=inner)))
    svc.users_coll.find = MagicMock(return_value=cursor)
    svc.users_coll.count_documents = AsyncMock(return_value=1)
    result = await svc.list_users(page=1, page_size=20)
    assert result["total"] == 1
    assert result["list"][0]["username"] == "zhangsan"
    # find 调用时应传入 password_hash projection
    find_args = svc.users_coll.find.call_args.args
    assert find_args[1] == {"password_hash": 0, "_id": 0}


@pytest.mark.asyncio
async def test_create_user_username_exists():
    svc = UserService()
    svc.users_coll = MagicMock()
    svc.users_coll.find_one = AsyncMock(return_value=_make_user())
    with pytest.raises(ConflictError):
        await svc.create_user(username="zhangsan", password="Pass1234", role="hr", email="z@t.com", name="张三")


@pytest.mark.asyncio
async def test_create_user_success():
    svc = UserService()
    svc.users_coll = MagicMock()
    svc.users_coll.find_one = AsyncMock(return_value=None)
    svc.users_coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="oid"))
    result = await svc.create_user(username="newuser", password="Pass1234", role="hr", email="n@t.com", name="新")
    assert result["username"] == "newuser"
    assert result["status"] == "approved"


@pytest.mark.asyncio
async def test_create_user_email_exists():
    """邮箱已注册抛 CONFLICT"""
    svc = UserService()
    svc.users_coll = MagicMock()
    svc.users_coll.find_one = AsyncMock(side_effect=[None, {"email": "n@t.com"}])
    with pytest.raises(ConflictError):
        await svc.create_user(username="new", password="Pass1234", role="hr", email="n@t.com", name="新")


@pytest.mark.asyncio
async def test_approve_success():
    svc = UserService()
    svc.users_coll = MagicMock()
    svc.users_coll.find_one = AsyncMock(return_value=_make_user(status="pending"))
    svc.users_coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    await svc.approve(user_id="u1")
    svc.users_coll.update_one.assert_called_once()
    update_args = svc.users_coll.update_one.call_args.args
    assert update_args[1]["$set"]["status"] == "approved"


@pytest.mark.asyncio
async def test_reject_deletes_record():
    svc = UserService()
    svc.users_coll = MagicMock()
    svc.users_coll.find_one = AsyncMock(return_value=_make_user(status="pending"))
    svc.users_coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    await svc.reject(user_id="u1")
    svc.users_coll.delete_one.assert_called_once()


@pytest.mark.asyncio
async def test_update_status_success():
    svc = UserService()
    svc.users_coll = MagicMock()
    svc.users_coll.find_one = AsyncMock(return_value=_make_user(status="approved"))
    svc.users_coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    await svc.update_status(user_id="u1", status="disabled")
    update_args = svc.users_coll.update_one.call_args.args
    assert update_args[1]["$set"]["status"] == "disabled"


@pytest.mark.asyncio
async def test_reset_password_success():
    svc = UserService()
    svc.users_coll = MagicMock()
    svc.users_coll.find_one = AsyncMock(return_value=_make_user())
    svc.users_coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    await svc.reset_password(user_id="u1", new_password="NewPass1234")
    svc.users_coll.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_delete_success():
    svc = UserService()
    svc.users_coll = MagicMock()
    svc.users_coll.find_one = AsyncMock(return_value=_make_user())
    svc.users_coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    await svc.delete(user_id="u1")
    svc.users_coll.delete_one.assert_called_once()


@pytest.mark.asyncio
async def test_cannot_delete_self():
    """管理员不能删除自己"""
    svc = UserService()
    with pytest.raises(AuthError):
        await svc.delete(user_id="u_self", current_user_id="u_self")


@pytest.mark.asyncio
async def test_user_not_found():
    svc = UserService()
    svc.users_coll = MagicMock()
    svc.users_coll.find_one = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError):
        await svc.approve(user_id="missing")
