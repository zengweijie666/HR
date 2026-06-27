"""
文件名: app/utils/pii.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: PII 脱敏与哈希工具，对应 Business-Requirements 4.3 安全要求
入参: 明文手机号/邮箱（可能为 None，LLM 返回 null 时兜底）
出参: 脱敏字符串 / sha256 哈希
"""
import hashlib


def mask_phone(phone: str | None) -> str:
    """手机号脱敏：138****1234，None/空串原样返回"""
    if not phone:
        return ""
    if len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def mask_email(email: str | None) -> str:
    """邮箱脱敏：zha***@xx.com，None/空串原样返回"""
    if not email or "@" not in email:
        return email or ""
    name, domain = email.split("@", 1)
    if len(name) <= 3:
        return name + "***@" + domain
    return name[:3] + "***@" + domain


def hash_phone(phone: str | None) -> str:
    """手机号 SHA256 哈希，用于去重。None/空串返回空哈希占位"""
    if not phone:
        return ""
    return hashlib.sha256(phone.encode()).hexdigest()


def hash_email(email: str | None) -> str:
    """邮箱 SHA256 哈希，用于去重。None/空串返回空哈希占位"""
    if not email:
        return ""
    return hashlib.sha256(email.encode()).hexdigest()
