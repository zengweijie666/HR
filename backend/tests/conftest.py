"""
文件名: tests/conftest.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: pytest 全局 fixtures；在导入 app 前注入测试用环境变量，
         使测试脱离 .env 也能独立运行
"""
import os

# 在导入 app 之前注入测试用环境变量（setdefault 不覆盖已存在的真实 .env 配置）
os.environ.setdefault("LLM_API_KEY", "sk-test-key-for-testing")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-testing-only")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("ADMIN_PASSWORD", "admin123")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.com")

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
