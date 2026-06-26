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


@pytest.mark.asyncio
async def test_get_stats(svc):
    """AC22.1: 看板统计"""
    svc.resumes_coll.count_documents = AsyncMock(side_effect=[100, 30, 15])
    svc.sessions_coll.count_documents = AsyncMock(return_value=50)
    # aggregate 链式调用，依次返回 top_skills / education / salary 三个 cursor
    top_skills_cursor = MagicMock()
    top_skills_cursor.to_list = AsyncMock(return_value=[
        {"_id": "Java", "count": 20}, {"_id": "Python", "count": 15}
    ])
    edu_cursor = MagicMock()
    edu_cursor.to_list = AsyncMock(return_value=[{"_id": "本科", "count": 60}])
    salary_cursor = MagicMock()
    salary_cursor.to_list = AsyncMock(return_value=[{"_id": "0-15", "count": 20}])
    svc.resumes_coll.aggregate = MagicMock(
        side_effect=[top_skills_cursor, edu_cursor, salary_cursor]
    )

    result = await svc.get_stats()
    assert "total_resumes" in result
    assert result["total_resumes"] == 100
    assert result["favorite_count"] == 30
    assert "top_skills" in result
    assert len(result["top_skills"]) == 2


@pytest.mark.asyncio
async def test_education_distribution(svc):
    """AC22.2: 学历分布"""
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[
        {"_id": "本科", "count": 60},
        {"_id": "硕士", "count": 30},
        {"_id": "专科", "count": 10},
    ])
    svc.resumes_coll.aggregate = MagicMock(return_value=mock_cursor)
    result = await svc._education_distribution()
    assert len(result) == 3
    assert result[0]["count"] == 60


@pytest.mark.asyncio
async def test_salary_range(svc):
    """AC22.3: 薪资分布"""
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[
        {"_id": "0-15", "count": 20},
        {"_id": "15-25", "count": 50},
        {"_id": "25+", "count": 30},
    ])
    svc.resumes_coll.aggregate = MagicMock(return_value=mock_cursor)
    result = await svc._salary_distribution()
    assert len(result) == 3
