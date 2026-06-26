"""
文件名: app/utils/pii.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: PII 脱敏与哈希工具，对应 Business-Requirements 4.3 安全要求
入参: 明文手机号/邮箱
出参: 脱敏字符串 / sha256 哈希
"""
import hashlib


def mask_phone(phone: str) -> str:
    """手机号脱敏：138****1234"""
    if len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def mask_email(email: str) -> str:
    """邮箱脱敏：zha***@xx.com"""
    if "@" not in email:
        return email
    name, domain = email.split("@", 1)
    if len(name) <= 3:
        return name + "***@" + domain
    return name[:3] + "***@" + domain


def hash_phone(phone: str) -> str:
    """手机号 SHA256 哈希，用于去重"""
    return hashlib.sha256(phone.encode()).hexdigest()


def hash_email(email: str) -> str:
    """邮箱 SHA256 哈希，用于去重"""
    return hashlib.sha256(email.encode()).hexdigest()
