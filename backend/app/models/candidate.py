"""
文件名: app/models/candidate.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 候选人卡片模型，对应 API-Design.md 10.3
"""
from pydantic import BaseModel
from app.models.resume import Salary


class CandidateCard(BaseModel):
    candidate_id: str
    resume_id: str
    name: str
    work_years: int
    education: str
    skills: list[str] = []
    expected_salary: Salary
    score: int
    reason: str
    tags: list[str] = []
    is_favorite: bool = False


class ExportRequest(BaseModel):
    candidate_ids: list[str] = []
    fields: list[str] | None = None


class SimilarResponse(BaseModel):
    resume_id: str
    name: str
    similarity: float
    shared_skills: list[str] = []
