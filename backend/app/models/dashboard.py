"""
文件名: app/models/dashboard.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 看板模型，对应 API-Design.md 九、Dashboard
"""
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_resumes: int
    new_this_week: int
    new_this_month: int
    favorite_count: int
    interviewed_count: int


class DistributionItem(BaseModel):
    name: str
    value: int


class DashboardStats(BaseModel):
    summary: DashboardSummary
    skill_distribution: list[DistributionItem]
    work_years_distribution: list[DistributionItem]
    education_distribution: list[DistributionItem]
    salary_distribution: list[DistributionItem]
    tag_distribution: list[DistributionItem]
