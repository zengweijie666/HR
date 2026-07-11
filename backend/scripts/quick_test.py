"""
文件名: scripts/quick_test.py
创建时间: 2026-06-28
功能描述: 快速测试单个搜索查询
入参: 环境变量 ADMIN_EMAIL / ADMIN_PASSWORD（从 .env 读取），命令行参数为查询语句
"""
import asyncio
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx


BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:8000/api/v1")


async def main():
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(f"{BASE_URL}/auth/login", json={
            "email": os.environ.get("ADMIN_EMAIL", "admin@test.com"),
            "password": os.environ.get("ADMIN_PASSWORD", "change-me-in-env"),
        })
        print(f"登录: {r.status_code}")
        token = r.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r = await client.post(f"{BASE_URL}/chat/sessions", headers=headers, json={"title": "测试"})
        session_id = r.json()["data"]["session_id"]
        print(f"会话: {session_id}")

        query = sys.argv[1] if len(sys.argv) > 1 else "nlp工程师"
        print(f"\n查询: '{query}'")

        async with client.stream(
            "POST",
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            headers=headers,
            json={"query": query},
            timeout=300,
        ) as resp:
            print(f"响应状态: {resp.status_code}")
            candidates_data = None
            retrieval_data = None
            full_text = ""
            async for line in resp.aiter_lines():
                if line.startswith("event:"):
                    current_event = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
                    try:
                        data = json.loads(data_str)
                    except:
                        data = data_str
                    if current_event == "retrieval":
                        retrieval_data = data
                        print(f"\n[检索] 召回数量: {data.get('count', '?')}, IDs: {data.get('candidate_ids', [])}")
                    elif current_event == "candidates":
                        candidates_data = data if isinstance(data, list) else []
                        print(f"\n[候选人] 返回 {len(candidates_data)} 人:")
                        for i, c in enumerate(candidates_data[:15]):
                            name = c.get("name", "?")
                            score = c.get("score", 0)
                            wy = c.get("work_years", 0)
                            edu = c.get("education_level", 0)
                            skills = (c.get("skills", []) or [])[:6]
                            print(f"  {i+1}. {name} | 分数:{score:.1f} | 经验:{wy}年 | 学历:{edu} | 技能:{skills}")
                    elif current_event == "token":
                        if isinstance(data, dict) and "delta" in data:
                            full_text += data["delta"]
                    elif current_event == "error":
                        print(f"\n[错误] {data}")
                    elif current_event == "done":
                        print(f"\n[完成] reason: {data.get('reason', '')}")
            print(f"\n[LLM回复]:\n{full_text[:500]}")


if __name__ == "__main__":
    asyncio.run(main())
