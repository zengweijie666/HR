"""
文件名: tests/services/test_email_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: EmailService 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.email_service import EmailService


@pytest.fixture
def svc():
    s = EmailService()
    s.config_coll = MagicMock()
    s.config_coll.find_one = AsyncMock(return_value=None)
    s.config_coll.update_one = AsyncMock()
    s.resumes_coll = MagicMock()
    s.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[])
    return s


@pytest.mark.asyncio
async def test_send_recommendation(svc):
    """AC17.1: 发送推荐邮件"""
    svc.config_coll.find_one = AsyncMock(return_value={
        "smtp_host": "smtp.example.com", "smtp_port": 465,
        "smtp_user": "hr@x.com", "smtp_password_encrypted": "encoded-pwd"
    })
    svc.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[
        {"candidate_id": "c1", "name": "张三", "skills": ["Java"], "work_years": 5,
         "expected_salary": {"min": 20, "max": 30}}
    ])
    with patch("app.services.email_service.aiosmtplib.send", AsyncMock(return_value=None)), \
         patch("app.services.email_service.decrypt", return_value="pwd"):
        result = await svc.send_recommendation(
            to_email="boss@example.com", candidate_ids=["c1"], job_title="Java 工程师"
        )
        assert result["status"] == "success"
        assert result["sent_count"] == 1


@pytest.mark.asyncio
async def test_send_recommendation_no_config(svc):
    """AC17.2: 无 SMTP 配置返回错误"""
    svc.config_coll.find_one = AsyncMock(return_value=None)
    result = await svc.send_recommendation(to_email="boss@x.com", candidate_ids=["c1"], job_title="x")
    assert result["status"] == "error"
    assert "未配置" in result["message"] or "config" in result["message"].lower()


@pytest.mark.asyncio
async def test_get_config(svc):
    """AC18.1: 获取 SMTP 配置（脱敏）"""
    svc.config_coll.find_one = AsyncMock(return_value={
        "smtp_host": "smtp.example.com", "smtp_port": 465,
        "smtp_user": "hr@x.com", "smtp_password_encrypted": "xxx"
    })
    result = await svc.get_config()
    assert result["smtp_host"] == "smtp.example.com"
    assert "smtp_password" not in result or result.get("smtp_password") == ""


@pytest.mark.asyncio
async def test_update_config(svc):
    """AC18.2: 更新 SMTP 配置（加密存储）"""
    with patch("app.services.email_service.encrypt", return_value="encrypted"):
        await svc.update_config({
            "smtp_host": "smtp.new.com", "smtp_port": 587,
            "smtp_user": "hr@new.com", "smtp_password": "secret"
        })
        args = svc.config_coll.update_one.call_args
        assert args.kwargs["update"]["$set"]["smtp_password_encrypted"] == "encrypted"


def test_html_report_generation(svc):
    """AC17.3: 生成 HTML 推荐报告"""
    candidates = [
        {"candidate_id": "c1", "name": "张三", "skills": ["Java"], "work_years": 5,
         "expected_salary": {"min": 20, "max": 30}}
    ]
    html = svc._build_html_report(candidates, job_title="Java 工程师")
    assert "<html" in html.lower()
    assert "张三" in html
    assert "Java 工程师" in html
