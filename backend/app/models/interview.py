"""
文件名: app/models/interview.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 面试模型，对应 API-Design.md 八、Interview
"""
from pydantic import BaseModel, Field


class InterviewQuestionRequest(BaseModel):
    dimensions: list[str] = ["technical", "project", "system_design", "behavioral"]
    count_per_dimension: int = 3
    focus_skills: list[str] = []


class InterviewQuestion(BaseModel):
    dimension: str
    question: str
    skill: str | None = None
    difficulty: str = "medium"
    reference_answer: str | None = None


class InterviewNoteRequest(BaseModel):
    interviewer: str
    rating: int = Field(ge=1, le=5)
    result: str  # pass/fail/pending
    notes: str = ""


class InterviewNote(InterviewNoteRequest):
    note_id: str
    resume_id: str
    created_at: str
