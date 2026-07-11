"""
文件名: scripts/create_test_user.py
创建时间: 2026-06-28
功能描述: 直接在MongoDB中创建/更新一个已审批的测试用户
入参: 环境变量 TEST_USER_EMAIL / TEST_USER_PASSWORD（从 .env 读取）
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import MongoDB
from app.services.auth_service import AuthService


async def main():
    await MongoDB.connect()
    coll = MongoDB.db.users
    email = os.environ.get("TEST_USER_EMAIL", "hr_test@example.com")
    password = os.environ.get("TEST_USER_PASSWORD", "change-me-in-env")
    result = await coll.update_one(
        {"email": email},
        {"$set": {
            "email": email,
            "username": "hr_test",
            "name": "HR测试",
            "password_hash": AuthService.hash_password(password),
            "role": "hr",
            "status": "approved",
        }},
        upsert=True,
    )
    print(f"用户已创建/更新: email={email}, password=***（已隐藏，见环境变量）, matched={result.matched_count}, upserted={result.upserted_id}")
    await MongoDB.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
