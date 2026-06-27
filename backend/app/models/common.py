"""
文件名: app/models/common.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 通用响应与分页模型，对应 API-Design.md 0.1/0.3
"""
from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: T | None = None
    trace_id: str


class PageQuery(BaseModel):
    page: int = 1
    page_size: int = 20


class PageResult(BaseModel, Generic[T]):
    list: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
