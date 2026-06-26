"""
文件名: tests/core/test_ocr.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: RapidOCR 封装单元测试
"""
import pytest
from unittest.mock import patch, MagicMock
from app.core.ocr import OCREngine


def test_ocr_lazy_load():
    """首次访问 engine 时才加载 RapidOCR"""
    with patch("app.core.ocr.RapidOCR") as MockOCR:
        engine = OCREngine()
        assert engine._engine is None
        _ = engine.engine
        MockOCR.assert_called_once()


def test_ocr_extract_text():
    """extract_text 应将 OCR 返回的 (text, score) 列表拼接为字符串"""
    with patch("app.core.ocr.RapidOCR") as MockOCR:
        instance = MagicMock()
        instance.return_value = ([("text1", 0.9), ("text2", 0.8)], None)
        MockOCR.return_value = instance
        engine = OCREngine()
        result = engine.extract_text(b"fake-image-bytes")
        assert "text1" in result
        assert "text2" in result
