"""
文件名: app/core/exceptions.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 统一业务异常，配合全局异常处理器返回标准响应
"""
from app.core.response import CODE


class BizError(Exception):
    """业务异常基类"""
    def __init__(self, code: int, message: str, data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class ParamError(BizError):
    def __init__(self, message: str, data=None):
        super().__init__(CODE.PARAM_ERROR, message, data)


class AuthError(BizError):
    def __init__(self, message: str, data=None):
        super().__init__(CODE.UNAUTHORIZED, message, data)


class ForbiddenError(BizError):
    def __init__(self, message: str, data=None):
        super().__init__(CODE.FORBIDDEN, message, data)


class NotFoundError(BizError):
    def __init__(self, message: str, data=None):
        super().__init__(CODE.NOT_FOUND, message, data)


class ConflictError(BizError):
    def __init__(self, message: str, data=None):
        super().__init__(CODE.CONFLICT, message, data)


class ResumeParseError(BizError):
    def __init__(self, message: str, data=None):
        super().__init__(CODE.RESUME_PARSE_FAILED, message, data)


class LLMError(BizError):
    def __init__(self, message: str, data=None):
        super().__init__(CODE.LLM_FAILED, message, data)


class EmailError(BizError):
    def __init__(self, message: str, data=None):
        super().__init__(CODE.EMAIL_FAILED, message, data)
