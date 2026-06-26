"""
文件名: tests/core/test_response.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试统一响应封装
"""
from app.core.response import success, error, CODE


def test_success_default():
    resp = success()
    assert resp["code"] == 0
    assert resp["message"] == "success"
    assert resp["data"] is None
    assert "trace_id" in resp


def test_success_with_data():
    resp = success(data={"id": 1}, message="created")
    assert resp["code"] == 0
    assert resp["message"] == "created"
    assert resp["data"] == {"id": 1}


def test_error_with_code():
    resp = error(code=CODE.PARAM_ERROR, message="字段 query 不能为空")
    assert resp["code"] == 1001
    assert resp["message"] == "字段 query 不能为空"
    assert resp["data"] is None
    assert "trace_id" in resp


def test_error_with_data():
    resp = error(code=CODE.RESUME_PARSE_FAILED, message="PDF 损坏", data={"resume_id": "r1"})
    assert resp["code"] == 2001
    assert resp["data"] == {"resume_id": "r1"}
