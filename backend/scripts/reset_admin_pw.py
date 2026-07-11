"""
文件名: scripts/reset_admin_pw.py
创建时间: 2026-06-28
功能描述: 重置admin和hr_test密码为已知值
入参: 环境变量 ADMIN_EMAIL / ADMIN_PASSWORD / TEST_USER_EMAIL / TEST_USER_PASSWORD（从 .env 读取）
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import MongoDB
import bcrypt


async def main():
    await MongoDB.connect()
    coll = MongoDB.db.users

    def hash_pw(pw):
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@test.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "change-me-in-env")
    test_email = os.environ.get("TEST_USER_EMAIL", "hr_test@example.com")
    test_password = os.environ.get("TEST_USER_PASSWORD", "change-me-in-env")

    for username, password, email, role, name in [
        ("admin", admin_password, admin_email, "admin", "管理员"),
        ("hr_test", test_password, test_email, "hr", "HR测试"),
    ]:
        existing = await coll.find_one({"username": username})
        if existing:
            await coll.update_one(
                {"username": username},
                {"$set": {
                    "password_hash": hash_pw(password),
                    "status": "approved",
                    "email": email,
                }}
            )
            print(f"已重置密码: username={username}, email={email}, password=***（见环境变量）")
        else:
            import uuid
            from datetime import datetime, timezone
            user_id = f"u_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc).isoformat()
            await coll.insert_one({
                "user_id": user_id,
                "username": username,
                "password_hash": hash_pw(password),
                "email": email,
                "name": name,
                "role": role,
                "status": "approved",
                "created_at": now,
                "updated_at": now,
            })
            print(f"已创建用户: username={username}, password=***（见环境变量）")

    await MongoDB.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
