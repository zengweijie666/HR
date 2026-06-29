"""
文件名: scripts/test_real_search.py
创建时间: 2026-06-28
作者: TalentSense Team
功能描述: 使用真实数据测试搜索匹配功能，验证13份NLP简历召回和过滤功能
使用方式: cd backend && .venv/Scripts/python.exe scripts/test_real_search.py
"""
import asyncio
import sys
import json
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx


BASE_URL = "http://127.0.0.1:8000/api/v1"


def _parse_sse_events(lines: list[str]) -> list[dict]:
    events = []
    current_event = None
    current_data = []
    for line in lines:
        line = line.rstrip("\n\r")
        if line.startswith("event:"):
            current_event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            current_data.append(line[len("data:"):].strip())
        elif line == "":
            if current_event and current_data:
                data_str = "\n".join(current_data)
                try:
                    events.append({"event": current_event, "data": json.loads(data_str)})
                except json.JSONDecodeError:
                    events.append({"event": current_event, "data": data_str})
            current_event = None
            current_data = []
    return events


async def register_and_login(client: httpx.AsyncClient) -> str:
    r = await client.post(f"{BASE_URL}/auth/login", json={
        "email": "a****@********",
        "password": "admin123",
    })
    print(f"  登录响应: {r.status_code}")
    r.raise_for_status()
    return r.json()["data"]["access_token"]


async def create_session(client: httpx.AsyncClient, token: str) -> str:
    r = await client.post(
        f"{BASE_URL}/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "测试搜索"},
    )
    r.raise_for_status()
    return r.json()["data"]["session_id"]


async def send_message(client: httpx.AsyncClient, token: str, session_id: str, message: str) -> list[dict]:
    async with client.stream(
        "POST",
        f"{BASE_URL}/chat/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": message},
        timeout=300,
    ) as resp:
        resp.raise_for_status()
        lines = []
        async for line in resp.aiter_lines():
            lines.append(line)
        return _parse_sse_events(lines)


def get_candidates_from_events(events: list[dict]) -> list[dict]:
    for e in events:
        if e["event"] == "candidates":
            return e["data"] if isinstance(e["data"], list) else []
    return []


def get_filters_from_logs(events: list[dict]):
    for e in events:
        if e["event"] == "retrieval":
            return e["data"]
    return None


async def main():
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("步骤1: 注册并登录")
        token = await register_and_login(client)
        print(f"  登录成功，token长度: {len(token)}")

        print("\n" + "=" * 60)
        print("步骤2: 创建会话")
        session_id = await create_session(client, token)
        print(f"  会话ID: {session_id}")

        tests = [
            {
                "name": "测试1: 'nlp工程师' - 应返回尽可能多的NLP候选人",
                "query": "nlp工程师",
                "expect_min_candidates": 10,
                "expect_keywords": ["nlp", "bert", "pytorch", "transformer"],
            },
            {
                "name": "测试2: '我要十位nlp工程师' - 验证数量",
                "query": "我要十位nlp工程师",
                "expect_min_candidates": 10,
                "expect_keywords": ["nlp"],
            },
            {
                "name": "测试3: 'nlp相关，本科以上，30K以内' - 验证过滤",
                "query": "nlp相关，本科以上，30K以内",
                "expect_min_candidates": 5,
                "expect_keywords": ["nlp", "bert"],
            },
            {
                "name": "测试4: 'RNN工程师' - 验证技能匹配",
                "query": "RNN工程师",
                "expect_min_candidates": 3,
                "expect_keywords": ["rnn", "lstm", "nlp"],
            },
        ]

        all_pass = True
        for test in tests:
            print("\n" + "=" * 60)
            print(test["name"])
            print(f"  查询: '{test['query']}'")

            events = await send_message(client, token, session_id, test["query"])

            event_names = [e["event"] for e in events]
            print(f"  SSE事件: {event_names}")

            candidates = get_candidates_from_events(events)
            print(f"  返回候选人数: {len(candidates)}")

            if "error" in event_names:
                for e in events:
                    if e["event"] == "error":
                        print(f"  ❌ 错误: {e['data']}")
                all_pass = False
                continue

            if len(candidates) < test["expect_min_candidates"]:
                print(f"  ⚠️ 候选人数不足: 期望>={test['expect_min_candidates']}, 实际={len(candidates)}")
                all_pass = False
            else:
                print(f"  ✅ 候选人数达标: >= {test['expect_min_candidates']}")

            print(f"  候选人列表 (前10):")
            for i, c in enumerate(candidates[:10]):
                name = c.get("name", "未知")
                score = c.get("score", 0)
                wy = c.get("work_years", 0)
                edu = c.get("education_level", 0)
                skills = (c.get("skills", []) or [])[:5]
                print(f"    {i+1}. {name} | 分数:{score:.1f} | 经验:{wy}年 | 学历:{edu} | 技能:{skills}")

            all_skills_text = " ".join(
                " ".join(c.get("skills", []) or []) for c in candidates
            ).lower()
            missing_kw = [kw for kw in test["expect_keywords"] if kw.lower() not in all_skills_text]
            if missing_kw:
                print(f"  ⚠️ 缺少关键词: {missing_kw}")
            else:
                print(f"  ✅ 关键词覆盖: {test['expect_keywords']}")

            retrieval_info = get_filters_from_logs(events)
            if retrieval_info:
                print(f"  检索信息: {retrieval_info}")

        print("\n" + "=" * 60)
        if all_pass:
            print("✅ 所有测试通过！")
        else:
            print("⚠️ 部分测试未达标，请检查输出详情")


if __name__ == "__main__":
    asyncio.run(main())
