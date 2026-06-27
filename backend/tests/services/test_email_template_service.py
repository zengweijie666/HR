"""
文件名: tests/services/test_email_template_service.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: EmailTemplateService 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.email_template_service import EmailTemplateService
from app.core.exceptions import NotFoundError, ConflictError


@pytest.fixture
def svc():
    s = EmailTemplateService()
    s.templates_coll = MagicMock()
    s.templates_coll.find_one = AsyncMock(return_value=None)
    s.templates_coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="oid"))
    s.templates_coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    s.templates_coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    return s


@pytest.mark.asyncio
async def test_list_templates(svc):
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=[{"template_id": "t1", "name": "面试邀请"}])
    svc.templates_coll.find = MagicMock(return_value=cursor)
    result = await svc.list_templates()
    assert result["total"] == 1
    assert result["list"][0]["name"] == "面试邀请"


@pytest.mark.asyncio
async def test_create_template_success(svc):
    result = await svc.create_template(name="自定义", subject="主题", body="<p>正文</p>", category="custom")
    assert result["name"] == "自定义"
    assert result["is_builtin"] is False


@pytest.mark.asyncio
async def test_create_template_name_exists(svc):
    svc.templates_coll.find_one = AsyncMock(return_value={"template_id": "t1", "name": "重名"})
    with pytest.raises(ConflictError):
        await svc.create_template(name="重名", subject="主题", body="正文", category="custom")


@pytest.mark.asyncio
async def test_update_template_success(svc):
    svc.templates_coll.find_one = AsyncMock(return_value={
        "template_id": "t1", "name": "旧", "is_builtin": False
    })
    await svc.update_template("t1", name="新名")
    svc.templates_coll.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_update_builtin_template_rejected(svc):
    """预置模板不允许编辑（仅可删除后重建）"""
    svc.templates_coll.find_one = AsyncMock(return_value={
        "template_id": "t1", "name": "面试邀请", "is_builtin": True
    })
    with pytest.raises(Exception):
        await svc.update_template("t1", name="改")


@pytest.mark.asyncio
async def test_delete_template_success(svc):
    svc.templates_coll.find_one = AsyncMock(return_value={
        "template_id": "t1", "is_builtin": False
    })
    await svc.delete_template("t1")
    svc.templates_coll.delete_one.assert_called_once()


@pytest.mark.asyncio
async def test_delete_builtin_template_rejected(svc):
    svc.templates_coll.find_one = AsyncMock(return_value={
        "template_id": "t1", "is_builtin": True
    })
    with pytest.raises(Exception):
        await svc.delete_template("t1")


@pytest.mark.asyncio
async def test_render_template_success(svc):
    svc.templates_coll.find_one = AsyncMock(return_value={
        "template_id": "t1",
        "subject": "【{{ company }}】面试 - {{ position }}",
        "body": "<p>{{ candidate_name }}，时间 {{ interview_time }}</p>"
    })
    subject, body = await svc.render_template("t1", {
        "company": "ACME", "position": "Java", "candidate_name": "张三", "interview_time": "周一 10:00"
    })
    assert "ACME" in subject and "Java" in subject
    assert "张三" in body and "周一 10:00" in body


@pytest.mark.asyncio
async def test_render_template_not_found(svc):
    svc.templates_coll.find_one = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError):
        await svc.render_template("missing", {})


def test_render_variables_safety():
    """渲染应拒绝未定义的复杂表达式（沙箱）"""
    svc = EmailTemplateService()
    # 沙箱环境只允许变量替换，应自动 HTML 转义
    rendered = svc._render_str("{{ x }}", {"x": "<b>"})
    assert "&lt;" in rendered
