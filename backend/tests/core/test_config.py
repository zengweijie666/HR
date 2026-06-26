"""
文件名: tests/core/test_config.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试配置加载
"""
import os
from app.core.config import Settings


def test_settings_loads_defaults(monkeypatch):
    """测试默认配置加载"""
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("JWT_SECRET", "secret-test")
    s = Settings()
    assert s.APP_NAME == "TalentSense HR"
    assert s.API_V1_PREFIX == "/api/v1"
    assert s.MONGO_DB == "talentsense"
    assert s.LLM_MODEL == "qwen-plus"
    assert s.HYBRID_DENSE_WEIGHT == 1.0
    assert s.HYBRID_SPARSE_WEIGHT == 0.7
    assert s.RETRIEVE_TOP_K == 20


def test_settings_reads_env(monkeypatch):
    """测试环境变量覆盖"""
    monkeypatch.setenv("LLM_API_KEY", "sk-override")
    monkeypatch.setenv("JWT_SECRET", "secret-override")
    monkeypatch.setenv("MONGO_DB", "test_db")
    s = Settings()
    assert s.LLM_API_KEY == "sk-override"
    assert s.JWT_SECRET == "secret-override"
    assert s.MONGO_DB == "test_db"
