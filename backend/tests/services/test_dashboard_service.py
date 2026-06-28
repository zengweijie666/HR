"""
文件名: tests/services/test_dashboard_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: DashboardService 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.dashboard_service import DashboardService


@pytest.fixture
def svc():
    """构造带 mock collection 的 service（motor aggregate() 同步返回 cursor，用 MagicMock）"""
    s = DashboardService()
    s.resumes_coll = MagicMock()
    s.sessions_coll = MagicMock()
    s.notes_coll = MagicMock()
    return s


def _make_cursor(data: list) -> MagicMock:
    """构造 mock aggregate cursor"""
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=data)
    return cursor


@pytest.mark.asyncio
async def test_get_stats(svc):
    """AC22.1: 看板统计（含新增漏斗/趋势/经验/面试结果）"""
    # count_documents 调用顺序：total, favorite, parsing (resumes) + sessions
    # + funnel: total, parsed, fav (resumes) + interviewed, passed (notes)
    svc.resumes_coll.count_documents = AsyncMock(side_effect=[100, 30, 15, 100, 90, 30])
    svc.sessions_coll.count_documents = AsyncMock(return_value=50)
    svc.notes_coll.count_documents = AsyncMock(side_effect=[10, 5])

    # aggregate 调用顺序：top_skills / education / salary / resume_trend / work_years (resumes)
    svc.resumes_coll.aggregate = MagicMock(side_effect=[
        _make_cursor([{"_id": "Java", "count": 20}, {"_id": "Python", "count": 15}]),
        _make_cursor([{"_id": "本科", "count": 60}]),
        _make_cursor([{"_id": "0-15", "count": 20}]),
        _make_cursor([{"_id": "2026-06-01", "count": 5}]),  # resume_trend
        _make_cursor([{"_id": 0, "count": 30}, {"_id": 3, "count": 40}]),  # work_years
    ])
    svc.notes_coll.aggregate = MagicMock(return_value=_make_cursor([
        {"_id": "通过", "count": 5}, {"_id": "不通过", "count": 3}
    ]))

    result = await svc.get_stats()
    assert result["total_resumes"] == 100
    assert result["favorite_count"] == 30
    assert len(result["top_skills"]) == 2
    assert len(result["recruitment_funnel"]) == 5
    assert result["recruitment_funnel"][0]["count"] == 100
    assert len(result["resume_trend"]) == 30
    assert len(result["work_years_distribution"]) == 2
    assert len(result["interview_result_distribution"]) == 2


@pytest.mark.asyncio
async def test_education_distribution(svc):
    """AC22.2: 学历分布"""
    svc.resumes_coll.aggregate = MagicMock(return_value=_make_cursor([
        {"_id": "本科", "count": 60},
        {"_id": "硕士", "count": 30},
        {"_id": "专科", "count": 10},
    ]))
    result = await svc._education_distribution()
    assert len(result) == 3
    assert result[0]["count"] == 60


@pytest.mark.asyncio
async def test_salary_range(svc):
    """AC22.3: 薪资分布"""
    svc.resumes_coll.aggregate = MagicMock(return_value=_make_cursor([
        {"_id": "0-15", "count": 20},
        {"_id": "15-25", "count": 50},
        {"_id": "25+", "count": 30},
    ]))
    result = await svc._salary_distribution()
    assert len(result) == 3


@pytest.mark.asyncio
async def test_recruitment_funnel(svc):
    """招聘漏斗统计"""
    svc.resumes_coll.count_documents = AsyncMock(side_effect=[100, 90, 30])
    svc.notes_coll.count_documents = AsyncMock(side_effect=[10, 5])
    result = await svc._recruitment_funnel()
    assert len(result) == 5
    assert result[0] == {"stage": "简历入库", "count": 100}
    assert result[4] == {"stage": "面试通过", "count": 5}


@pytest.mark.asyncio
async def test_work_years_distribution(svc):
    """工作经验分布"""
    svc.resumes_coll.aggregate = MagicMock(return_value=_make_cursor([
        {"_id": 0, "count": 30},
        {"_id": 3, "count": 40},
        {"_id": 5, "count": 20},
        {"_id": 10, "count": 10},
    ]))
    result = await svc._work_years_distribution()
    assert len(result) == 4
    assert result[0]["range"] == "0-3年"
    assert result[3]["range"] == "10+年"


@pytest.mark.asyncio
async def test_interview_result_distribution(svc):
    """面试结果统计"""
    svc.notes_coll.aggregate = MagicMock(return_value=_make_cursor([
        {"_id": "通过", "count": 5},
        {"_id": "不通过", "count": 3},
        {"_id": "待定", "count": 2},
    ]))
    result = await svc._interview_result_distribution()
    assert len(result) == 3
    assert result[0]["result"] == "通过"
