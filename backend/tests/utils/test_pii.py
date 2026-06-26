"""
文件名: tests/utils/test_pii.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试 PII 脱敏与哈希
"""
import hashlib
from app.utils.pii import mask_phone, mask_email, hash_phone, hash_email


def test_mask_phone():
    assert mask_phone("13812341234") == "138****1234"
    assert mask_phone("13800138000") == "138****8000"


def test_mask_email():
    assert mask_email("zhangsan@xx.com") == "zha***@xx.com"
    assert mask_email("a@b.com") == "a***@b.com"


def test_hash_phone():
    h = hash_phone("13812341234")
    assert h == hashlib.sha256("13812341234".encode()).hexdigest()
    assert len(h) == 64


def test_hash_email():
    h = hash_email("a@b.com")
    assert h == hashlib.sha256("a@b.com".encode()).hexdigest()


def test_mask_phone_short():
    """短号码不应崩溃"""
    assert mask_phone("123") == "123"


def test_mask_email_invalid():
    """非法邮箱原样返回"""
    assert mask_email("invalid") == "invalid"
