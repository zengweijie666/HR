"""
文件名: tests/services/test_tag_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: TagService 标签/收藏/评价单元测试
"""
import pytest
from unittest.mock import AsyncMock
from app.services.tag_service import TagService


@pytest.fixture
def svc():
    """构造 coll 已 mock 的 TagService"""
    s = TagService()
    s.coll = AsyncMock()
    return s


@pytest.mark.asyncio
async def test_update_tags(svc):
    """AC7.1: 全量覆盖"""
    svc.coll.find_one.return_value = {"resume_id": "r1", "tags": ["已面试"]}
    await svc.update_tags("r1", ["已面试", "重点关注"])
    svc.coll.update_one.assert_called_once()
    args = svc.coll.update_one.call_args
    assert args.kwargs["update"]["$set"]["tags"] == ["已面试", "重点关注"]


@pytest.mark.asyncio
async def test_update_tags_empty(svc):
    """AC7.4: 清空标签"""
    await svc.update_tags("r1", [])
    args = svc.coll.update_one.call_args
    assert args.kwargs["update"]["$set"]["tags"] == []


@pytest.mark.asyncio
async def test_toggle_favorite(svc):
    """AC8.1/8.2"""
    await svc.toggle_favorite("r1", True)
    args = svc.coll.update_one.call_args
    assert args.kwargs["update"]["$set"]["is_favorite"] is True


@pytest.mark.asyncio
async def test_update_notes(svc):
    """AC9.1"""
    await svc.update_notes("r1", "评价内容")
    args = svc.coll.update_one.call_args
    assert args.kwargs["update"]["$set"]["notes"] == "评价内容"
