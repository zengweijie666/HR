"""
文件名: tests/core/test_exceptions.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试业务异常
"""
import pytest
from app.core.exceptions import BizError, ParamError, AuthError, NotFoundError
from app.core.response import CODE


def test_biz_error_attributes():
    e = BizError(code=1001, message="参数错误", data={"field": "q"})
    assert e.code == 1001
    assert e.message == "参数错误"
    assert e.data == {"field": "q"}


def test_param_error_helper():
    e = ParamError("query 不能为空")
    assert e.code == CODE.PARAM_ERROR


def test_auth_error_helper():
    e = AuthError("Token 过期")
    assert e.code == CODE.UNAUTHORIZED


def test_not_found_helper():
    e = NotFoundError("简历不存在")
    assert e.code == CODE.NOT_FOUND


def test_biz_error_is_exception():
    with pytest.raises(BizError):
        raise ParamError("x")
