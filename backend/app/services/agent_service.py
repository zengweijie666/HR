"""
文件名: app/services/agent_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 对话服务 - 会话 CRUD + SSE 流式编排（调用 LangGraph 节点）
入参: session_id / query / user_id / filters
出参: SSE 事件流（intent/retrieval/rank/candidates/token/done/error）
对应 Business-Requirements F10/F12
"""
import uuid
import json
from datetime import datetime, timezone
from app.core.database import MongoDB
from app.core.logger import logger
from app.core.llm_client import llm_client
from app.agent.state import make_state
from app.agent.nodes import (
    intent_node,
    retrieve_rank_node,
)


def _sse_event(event: str, data: dict) -> str:
    """构造 SSE 事件块

    入参:
        event: 事件类型
        data: 事件数据
    出参:
        SSE 格式字符串
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class AgentService:
    """对话服务：会话 CRUD + SSE 流式编排"""

    def __init__(self):
        pass

    @property
    def sessions_coll(self):
        """延迟获取 MongoDB chat_sessions collection（避免模块导入时 MongoDB 未连接）"""
        if hasattr(self, "_sessions_coll"):
            return self._sessions_coll
        return MongoDB.db.chat_sessions if MongoDB.db is not None else None

    @sessions_coll.setter
    def sessions_coll(self, value):
        """测试注入用"""
        self._sessions_coll = value

    async def create_session(self, user_id: str, title: str = "新会话") -> dict:
        """AC10.1: 创建会话

        入参:
            user_id: 用户 ID
            title: 会话标题
        出参:
            {"session_id": "...", "title": "..."}
        """
        session_id = f"s_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "session_id": session_id,
            "user_id": user_id,
            "title": title,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        await self.sessions_coll.insert_one(doc)
        return {"session_id": session_id, "title": title}

    async def get_sessions(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        """AC10.2: 会话列表

        入参:
            user_id: 用户 ID
            page: 页码
            page_size: 每页数量
        出参:
            {"list": [...], "total": N, "page": page, "page_size": page_size, "total_pages": N}
        """
        skip = (page - 1) * page_size
        cursor = (
            self.sessions_coll.find({"user_id": user_id})
            .sort("updated_at", -1)
            .skip(skip)
            .limit(page_size)
        )
        list_data = await cursor.to_list(length=page_size)
        total = await self.sessions_coll.count_documents({"user_id": user_id})
        for s in list_data:
            s.pop("_id", None)
        return {
            "list": list_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    async def get_messages(self, session_id: str) -> list[dict]:
        """AC10.3: 获取消息历史

        入参:
            session_id: 会话 ID
        出参:
            消息列表
        """
        doc = await self.sessions_coll.find_one({"session_id": session_id})
        if not doc:
            return []
        return doc.get("messages", [])

    async def delete_session(self, session_id: str) -> None:
        """AC10.4: 删除会话

        入参:
            session_id: 会话 ID
        """
        await self.sessions_coll.delete_one({"session_id": session_id})

    async def send_message_stream(
        self,
        session_id: str,
        user_id: str,
        query: str,
        filters: dict = None,
    ):
        """AC12.1-12.3: SSE 流式响应

        入参:
            session_id: 会话 ID
            user_id: 用户 ID
            query: 用户查询
            filters: 过滤条件
        出参:
            异步生成器，yield SSE 事件字符串
        事件类型: intent / retrieval / rank / candidates / token / done / error
        """
        # 加载历史
        doc = await self.sessions_coll.find_one({"session_id": session_id})
        history = doc.get("messages", [])[-10:] if doc else []
        message_id = f"m_{uuid.uuid4().hex[:16]}"

        state = make_state(
            query=query,
            session_id=session_id,
            history=history,
            filters=filters,
            user_id=user_id,
        )

        try:
            # 1. 意图识别事件
            intent_result = await intent_node(state)
            state.update(intent_result)
            yield _sse_event("intent", {
                "intent": state.get("intent_type"),
                "strategy": state.get("strategy"),
            })

            # 2. 检索事件（所有非 chitchat/qa 意图都需要检索：search/compare/detail）
            intent_type = state.get("intent_type")
            if intent_type in ("search", "compare", "detail"):
                retrieve_result = await retrieve_rank_node(state)
                state.update(retrieve_result)
                candidates = state.get("candidates", [])
                yield _sse_event("retrieval", {
                    "count": len(candidates),
                    "candidate_ids": [c.get("candidate_id") for c in candidates],
                })
                if candidates:
                    ranked = [
                        {"candidate_id": c.get("candidate_id"), "score": c.get("score", 0)}
                        for c in candidates
                    ]
                    yield _sse_event("rank", {"ranked": ranked})
                # 无论是否为空都 yield candidates 事件，便于前端区分'没触发检索'和'检索为空'
                yield _sse_event("candidates", candidates)

            # 3. 流式 token（将检索到的候选人作为上下文传入，LLM 基于 RAG 结果回答）
            full_response = ""
            candidates = state.get("candidates", [])
            intent_type = state.get("intent_type", "chitchat")

            # 构建回答 messages
            if intent_type in ("search", "compare", "detail") and candidates:
                from app.agent.prompts import SEARCH_RESPOND_PROMPT, DETAIL_PROMPT
                if intent_type == "detail":
                    target_candidate = None
                    for c in candidates:
                        cid = c.get("candidate_id", "")
                        name = c.get("name", "")
                        if (cid and cid in query) or (name and name in query):
                            target_candidate = c
                            break
                    if target_candidate:
                        system_prompt = (
                            "你是 TalentSense HR 招聘助手。严格遵守以下规则：\n"
                            "1. 只能使用提供的候选人数据回答，绝对禁止编造信息\n"
                            "2. 详细介绍该候选人的背景、技能、工作经验等\n"
                            "3. 用中文专业简洁地回答\n"
                        )
                        user_prompt = DETAIL_PROMPT.format(
                            query=query,
                            candidate=json.dumps(target_candidate, ensure_ascii=False),
                        )
                    else:
                        system_prompt = (
                            "你是 TalentSense HR 招聘助手。严格遵守以下规则：\n"
                            "1. 只能使用提供的候选人数据回答，绝对禁止编造不存在的候选人\n"
                            "2. 请列出候选人名单让用户选择想查看谁的详情\n"
                            "3. 用中文简洁回答\n"
                        )
                        user_prompt = SEARCH_RESPOND_PROMPT.format(
                            query=query,
                            candidates=json.dumps(candidates[:10], ensure_ascii=False),
                        )
                else:
                    system_prompt = (
                        "你是 TalentSense HR 招聘助手。严格遵守以下规则：\n"
                        "1. 只能使用提供的候选人数据回答，绝对禁止编造不存在的候选人\n"
                        "2. 不要生成'理想候选人简历描述'等虚构内容\n"
                        "3. 用户要求N名候选人时，只展示前N名\n"
                        "4. 用中文简洁回答，引用候选人姓名与核心技能\n"
                    )
                    user_prompt = SEARCH_RESPOND_PROMPT.format(
                        query=query,
                        candidates=json.dumps(candidates[:10], ensure_ascii=False),
                    )
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            elif intent_type in ("search", "compare", "detail") and not candidates:
                from app.agent.prompts import CLARIFY_PROMPT
                clarify_prompt = CLARIFY_PROMPT.format(query=query)
                messages = [
                    {"role": "system", "content": "你是 TalentSense HR 招聘助手。没有检索到候选人时，明确告知用户当前库中没有匹配人员，并引导用户补充需求细节（如技术栈、年限、学历等）或上传更多简历。不要编造候选人。"},
                    {"role": "user", "content": clarify_prompt},
                ]
            elif intent_type == "chitchat":
                from app.agent.prompts import CHITCHAT_PROMPT
                chitchat_prompt = CHITCHAT_PROMPT.format(query=query)
                messages = [
                    {"role": "system", "content": "你是 TalentSense HR 招聘助手。友好回答用户的闲聊。"},
                    {"role": "user", "content": chitchat_prompt},
                ]
            elif intent_type == "qa":
                # qa 分支：通用问答（HR 知识/系统使用/通用问题），跳过检索，走 QA_PROMPT
                from app.agent.prompts import QA_PROMPT
                qa_prompt = QA_PROMPT.format(query=query)
                messages = [
                    {"role": "system", "content": "你是 TalentSense 智能招聘助手。回答 HR 流程咨询、系统使用帮助、通用知识问答。不编造候选人信息。"},
                    {"role": "user", "content": qa_prompt},
                ]
            else:
                messages = [
                    {"role": "system", "content": "你是 TalentSense HR 招聘助手。"},
                    {"role": "user", "content": query},
                ]

            try:
                async for tok in llm_client.chat_stream(messages):
                    full_response += tok
                    yield _sse_event("token", {"delta": tok})
            except Exception as e:
                logger.error(f"流式生成失败: {e}")
                full_response = "抱歉，生成回复时出错。"

            yield _sse_event("done", {
                "message_id": message_id,
                "response": full_response,
            })

            # 4. 保存消息
            await self._save_message(session_id, message_id, query, full_response, state)

        except Exception as e:
            logger.error(f"对话流式失败: {e}")
            yield _sse_event("error", {"code": 5001, "message": str(e)})

    async def _save_message(
        self,
        session_id: str,
        message_id: str,
        query: str,
        response: str,
        state: dict,
    ) -> None:
        """保存用户与助手消息

        入参:
            session_id: 会话 ID
            message_id: 消息 ID
            query: 用户查询
            response: 助手回复
            state: 当前 AgentState
        """
        now = datetime.now(timezone.utc).isoformat()
        await self.sessions_coll.update_one(
            {"session_id": session_id},
            update={
                "$push": {
                    "messages": {
                        "$each": [
                            {
                                "message_id": f"{message_id}_u",
                                "role": "user",
                                "content": query,
                                "created_at": now,
                            },
                            {
                                "message_id": message_id,
                                "role": "assistant",
                                "content": response,
                                "intent_type": state.get("intent_type"),
                                "strategy": state.get("strategy"),
                                "candidates": state.get("candidates"),
                                "created_at": now,
                            },
                        ],
                        "$slice": -20,  # 保留最近 20 条
                    }
                },
                "$set": {"updated_at": now},
            },
        )


agent_service = AgentService()
