"""
文件名: scripts/find_user.py
创建时间: 2026-06-28
作者: TalentSense Team
功能描述: 查询MongoDB中已有的用户账号
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import MongoDB


async def main():
    await MongoDB.connect()
    if MongoDB.db is None:
        print("MongoDB连接失败")
        return
    coll = MongoDB.db.users
    users = await coll.find({}).to_list(length=20)
    for u in users:
        print(f"  user_id={u.get('user_id')}, username={u.get('username')}, email={u.get('email')}, status={u.get('status')}, role={u.get('role')}")
    await MongoDB.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
