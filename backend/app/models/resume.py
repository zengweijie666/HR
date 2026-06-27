"""
文件名: app/models/resume.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 简历模型，对应 API-Design.md 10.1/10.2
"""
from pydantic import BaseModel, Field, field_validator


class Salary(BaseModel):
    min: int
    max: int


class BasicInfo(BaseModel):
    name: str
    phone_masked: str
    email_masked: str
    gender: str | None = None
    age: int | None = None
    location: str | None = None


class WorkExperience(BaseModel):
    company: str
    position: str
    start_date: str
    end_date: str
    description: str


class EducationDetail(BaseModel):
    school: str
    major: str
    degree: str
    start_date: str
    end_date: str


class FileInfo(BaseModel):
    file_name: str
    file_type: str
    file_size: int | None = None


class ParseInfo(BaseModel):
    parse_status: str
    parse_time: str | None = None


class ResumeListItem(BaseModel):
    resume_id: str
    candidate_id: str
    name: str
    gender: str | None = None
    age: int | None = None
    education: str
    education_level: int = Field(ge=0, le=3)
    work_years: int
    skills: list[str] = []
    expected_salary: Salary
    tags: list[str] = []
    is_favorite: bool = False
    parse_status: str
    location: str | None = None
    created_at: str

    @field_validator("education_level")
    @classmethod
    def check_level(cls, v):
        if v not in (0, 1, 2, 3):
            raise ValueError("education_level must be 0-3")
        return v


class ResumeDetail(ResumeListItem):
    basic_info: BasicInfo
    work_experience: list[WorkExperience] = []
    education_detail: list[EducationDetail] = []
    summary: str = ""
    file_info: FileInfo | None = None
    parse_info: ParseInfo | None = None
    notes: str = ""
    interview_notes: list = []
    updated_at: str | None = None


class UploadResponse(BaseModel):
    resume_id: str
    candidate_id: str
    file_name: str
    parse_status: str = "parsing"
    is_duplicate: bool = False
    duplicate_with: str | None = None


class PreviewResponse(BaseModel):
    preview_url: str
    file_type: str
    expires_in: int
