"""
文件名: tests/conftest.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: pytest 全局 fixtures
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
