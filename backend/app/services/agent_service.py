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
    query_decompose_node,
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
            消息列表（assistant 消息的 intent_type 映射为 intent，保持前后端字段名一致）
        """
        doc = await self.sessions_coll.find_one({"session_id": session_id})
        if not doc:
            return []
        messages = doc.get("messages", [])
        # 将 MongoDB 中 assistant 消息的 intent_type 映射为 intent，保持前端 ChatMessage.intent 一致
        for msg in messages:
            if msg.get("role") == "assistant" and "intent_type" in msg:
                msg["intent"] = msg.pop("intent_type")
        return messages

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
        # 加载历史（取最后 20 条作为上下文，避免 token 过多）
        doc = await self.sessions_coll.find_one({"session_id": session_id})
        history = doc.get("messages", [])[-20:] if doc else []
        message_id = f"m_{uuid.uuid4().hex[:16]}"

        # 从历史消息中提取最近一次候选人列表（供 compare/detail/qa 复用，避免重复检索）
        last_candidates = self._extract_last_candidates(history)

        state = make_state(
            query=query,
            session_id=session_id,
            history=history,
            filters=filters,
            user_id=user_id,
            last_candidates=last_candidates,
        )

        # 【关键修复】提前保存 user 消息，确保精排期间刷新页面不丢失对话
        # 原先 _save_message 在流结束后才保存，精排耗时较长时刷新会丢失整条对话
        first_msg_title = await self._save_user_message(session_id, message_id, query)

        try:
            # 1. 意图识别事件
            intent_result = await intent_node(state)
            state.update(intent_result)
            yield _sse_event("intent", {
                "intent": state.get("intent_type"),
                "strategy": state.get("strategy"),
            })

            # 2. 检索事件
            # - search: 始终触发新检索
            # - compare/qa/detail: 优先复用历史 candidates，无历史时才触发新检索
            intent_type = state.get("intent_type")
            need_retrieve = False
            if intent_type == "search":
                need_retrieve = True
            elif intent_type in ("compare", "detail"):
                # 从历史 candidates 中筛选被提及的候选人
                matched = self._match_candidates_by_query(query, last_candidates)
                if intent_type == "compare":
                    if len(matched) >= 2:
                        state["candidates"] = matched
                    elif len(matched) == 1:
                        state["candidates"] = last_candidates[:10]
                    elif last_candidates:
                        # 有历史 candidates 但姓名匹配失败（如"对比一下他们"），复用全部历史
                        state["candidates"] = last_candidates[:10]
                    else:
                        need_retrieve = True
                elif intent_type == "detail":
                    if matched:
                        state["candidates"] = matched
                    elif last_candidates:
                        state["candidates"] = last_candidates[:10]
                    else:
                        need_retrieve = True
            elif intent_type == "qa":
                # qa 带上历史 candidates 作为上下文（不新检索），让 LLM 能解释评分差异
                state["candidates"] = last_candidates
                need_retrieve = False

            if need_retrieve:
                # 2.1 查询分解（合并过滤提取 + 查询分解，输出 decomposed + filters）
                yield _sse_event("progress", {"stage": "analyzing", "message": "正在分析查询..."})
                decompose_result = await query_decompose_node(state)
                state.update(decompose_result)
                logger.info(f"提取的过滤条件: {state.get('filters', {})}, 分解: {state.get('decomposed', {})}")

                # 2.2 检索+精排
                yield _sse_event("progress", {"stage": "searching", "message": "正在检索候选人..."})
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
                yield _sse_event("candidates", candidates)
            else:
                # 复用历史/筛选结果，也发 candidates 事件让前端更新卡片
                candidates = state.get("candidates", [])
                if candidates:
                    yield _sse_event("candidates", candidates)

            # 3. 流式 token（将检索到的候选人作为上下文传入，LLM 基于 RAG 结果回答）
            full_response = ""
            candidates = state.get("candidates", [])
            intent_type = state.get("intent_type", "chitchat")

            # 构建回答 messages
            if intent_type in ("search", "compare", "detail") and candidates:
                from app.agent.prompts import SEARCH_RESPOND_PROMPT, DETAIL_PROMPT, COMPARE_PROMPT
                if intent_type == "detail":
                    target_candidate = None
                    for c in candidates:
                        cid = c.get("candidate_id", "")
                        c_name = c.get("name", "")
                        if (cid and cid in query) or (c_name and self._name_in_query(c_name, query)):
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
                elif intent_type == "compare":
                    matched_names = self._extract_names_from_query(query)
                    compare_candidates = candidates
                    if matched_names:
                        exact_matched = [
                            c for c in candidates
                            if c.get("name", "") in matched_names
                        ]
                        if exact_matched:
                            compare_candidates = exact_matched
                        else:
                            compare_candidates = candidates[:10]
                    system_prompt = (
                        "你是 TalentSense HR 招聘助手。严格遵守以下规则：\n"
                        "1. 只能使用提供的候选人数据对比，绝对禁止编造信息\n"
                        "2. 从工作年限、核心技能、项目经验、学历、评分等维度对比\n"
                        "3. 给出明确结论：各自优势、推荐优先级\n"
                        "4. 评分差异必须解释原因\n"
                        "5. 用中文专业简洁回答\n"
                    )
                    user_prompt = COMPARE_PROMPT.format(
                        query=query,
                        candidates=json.dumps(compare_candidates[:10], ensure_ascii=False),
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
                # qa 分支：通用问答，如有历史候选人数据则带上作为上下文
                from app.agent.prompts import QA_PROMPT
                if candidates:
                    qa_prompt = QA_PROMPT.format(query=query)
                    messages = [
                        {"role": "system", "content": (
                            "你是 TalentSense 智能招聘助手。回答 HR 流程咨询、系统使用帮助、候选人评分解释等问题。\n"
                            "以下是当前会话中最近检索到的候选人数据，可用于回答评分/对比等问题，"
                            "但禁止编造不存在的候选人信息：\n"
                            + json.dumps(candidates[:10], ensure_ascii=False)
                        )},
                        {"role": "user", "content": qa_prompt},
                    ]
                else:
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
                yield _sse_event("progress", {"stage": "generating", "message": "正在生成回复..."})
                async for tok in llm_client.chat_stream(messages):
                    full_response += tok
                    yield _sse_event("token", {"delta": tok})
            except Exception as e:
                logger.error(f"流式生成失败: {e}")
                full_response = "抱歉，生成回复时出错。"

            # 4. 保存 assistant 消息（user 消息已在流开始时提前保存）
            await self._save_assistant_message(session_id, message_id, full_response, state)
            # 首条消息标题已在 _save_user_message 中设置
            new_title = first_msg_title

            yield _sse_event("done", {
                "message_id": message_id,
                "response": full_response,
                "title": new_title,  # 仅首条消息时非 None
            })

        except Exception as e:
            logger.error(f"对话流式失败: {e}")
            yield _sse_event("error", {"code": 5001, "message": str(e)})

    async def _save_user_message(self, session_id: str, message_id: str, query: str) -> str | None:
        """流开始时立即保存 user 消息，确保精排期间刷新页面不丢失对话

        入参:
            session_id: 会话 ID
            message_id: 关联的 assistant 消息 ID（user 消息 ID 为 {message_id}_u）
            query: 用户查询
        出参:
            首条消息时返回新标题，非首条返回 None
        """
        now = datetime.now(timezone.utc).isoformat()
        new_title = None
        try:
            # 检查是否首条消息，首条时同步更新标题
            session = await self.sessions_coll.find_one(
                {"session_id": session_id}, {"messages": 1}
            )
            update = {
                "$push": {
                    "messages": {
                        "$each": [
                            {
                                "message_id": f"{message_id}_u",
                                "role": "user",
                                "content": query,
                                "created_at": now,
                            }
                        ],
                        "$slice": -50,
                    }
                },
                "$set": {"updated_at": now},
            }
            if session and not session.get("messages"):
                new_title = query[:20].strip() or "新会话"
                update["$set"]["title"] = new_title
            await self.sessions_coll.update_one({"session_id": session_id}, update=update)
        except Exception as e:
            logger.error(f"保存 user 消息失败: {e}")
        return new_title

    async def _save_assistant_message(
        self,
        session_id: str,
        message_id: str,
        response: str,
        state: dict,
    ) -> dict:
        """流结束后保存 assistant 消息

        入参:
            session_id: 会话 ID
            message_id: 消息 ID
            response: 助手回复
            state: 当前 AgentState
        出参:
            {"title": None} 标题已在 _save_user_message 首条消息时设置，此处返回 None
        """
        now = datetime.now(timezone.utc).isoformat()
        try:
            update = {
                "$push": {
                    "messages": {
                        "$each": [
                        {
                            "message_id": message_id,
                            "role": "assistant",
                            "content": response,
                            "intent_type": state.get("intent_type"),
                            "strategy": state.get("strategy"),
                            "candidates": state.get("candidates"),
                            "created_at": now,
                        }
                    ],
                    "$slice": -50,
                    }
                },
                "$set": {"updated_at": now},
            }
            await self.sessions_coll.update_one({"session_id": session_id}, update=update)
        except Exception as e:
            logger.error(f"保存 assistant 消息失败: {e}")
        return {"title": None}

    @staticmethod
    def _extract_last_candidates(history: list[dict]) -> list[dict]:
        """从对话历史中提取最近一次 assistant 消息中的 candidates

        入参:
            history: 对话消息列表（从 MongoDB 读取）
        出参:
            最近一次候选人列表，无则返回空列表
        """
        for msg in reversed(history):
            if msg.get("role") == "assistant" and msg.get("candidates"):
                return msg["candidates"]
        return []

    @staticmethod
    def _extract_names_from_query(query: str) -> list[str]:
        """从用户查询中提取中文姓名（优先从已知候选人名单匹配，fallback 用正则）

        入参:
            query: 用户查询文本，如"对比李志鹏和温佳蕊"
        出参:
            姓名列表，如 ["李志鹏", "温佳蕊"]
        设计:
            不直接用 r'[\u4e00-\u9fa5]{2,4}' 贪婪匹配（会把"对比李志"也截出来），
            而是由 _match_candidates_by_query 中根据 candidates 名单做精确匹配。
            此方法仅返回通用正则结果，实际姓名匹配优先走候选名单匹配。
        """
        import re
        # 先去掉常见连接词和动词前缀，避免"对比李志"被截出
        cleaned = re.sub(r'(对比|比较|和|与|跟|看看|查询|详情|介绍|谁|哪个|为什么|评分|比)', ' ', query)
        # 匹配2-3个连续汉字（中文姓名通常2-3字），过滤掉4字以上的词（通常是词组）
        candidates = re.findall(r'[\u4e00-\u9fa5]{2,3}', cleaned)
        # 过滤明显不是姓名的词
        stop_words = {'什么', '怎么', '为什么', '请问', '可以', '一下', '这个', '那个', '工程师', '方向'}
        return [n for n in candidates if n not in stop_words]

    @staticmethod
    def _name_in_query(name: str, query: str) -> bool:
        """检查姓名是否出现在 query 中

        入参:
            name: 候选人姓名
            query: 用户查询文本
        出参:
            True 表示姓名在 query 中
        """
        return name in query

    @staticmethod
    def _match_candidates_by_query(query: str, candidates: list[dict]) -> list[dict]:
        """根据查询中的姓名匹配候选人列表

        入参:
            query: 用户查询文本
            candidates: 候选人列表（从历史中提取）
        出参:
            匹配到的候选人列表（可能为空）
        设计:
            1. 优先从原始 query 直接查找候选人全名（c_name in query）
            2. 消除歧义：如果短名是长名的子串且长名也在query中，丢弃短名
               （避免"李志"误匹配"李志鹏"）
            3. fallback 到正则提取姓名后精确匹配
        """
        if not candidates:
            return []

        # 第一轮：找出所有名字出现在 query 中的候选人
        raw_matches = []
        for c in candidates:
            c_name = c.get("name", "")
            if c_name and c_name in query:
                raw_matches.append(c)

        # 第二轮：消除歧义——如果短名是长名的子串且长名也匹配，保留长名
        matched = []
        for c in raw_matches:
            c_name = c.get("name", "")
            is_substring_of_other = False
            for other in raw_matches:
                other_name = other.get("name", "")
                if other_name != c_name and c_name in other_name and other_name in query:
                    is_substring_of_other = True
                    break
            if not is_substring_of_other:
                matched.append(c)

        if matched:
            return matched

        # fallback: 正则提取姓名后精确匹配
        names = AgentService._extract_names_from_query(query)
        seen = set()
        for c in candidates:
            c_name = c.get("name", "")
            cid = c.get("candidate_id", "")
            if c_name in names and cid not in seen:
                matched.append(c)
                seen.add(cid)
        return matched


agent_service = AgentService()
