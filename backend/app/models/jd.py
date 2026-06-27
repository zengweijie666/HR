"""
文件名: app/models/jd.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: JD 匹配模型，对应 API-Design.md 七、JD Match
"""
from pydantic import BaseModel


class JdMatchRequest(BaseModel):
    jd_text: str
    top_k: int = 10
    filters: dict = {}


class ParsedRequirements(BaseModel):
    skills: list[str] = []
    work_years_min: int | None = None
    education_min: int | None = None
    responsibilities: list[str] = []


class MatchAnalysis(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]
    experience_match: bool
    education_match: bool
    reason: str
