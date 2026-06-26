"""
文件名: app/api/chat.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 对话路由，对应 API-Design.md 三（含 SSE 流式）
入参: HTTP 请求（session_id / query / context.filters）
出参: 统一响应 success/error 或 SSE 流
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.services.agent_service import AgentService
from app.api.deps import get_current_user
from app.core.response import success

router = APIRouter()


@router.post("/sessions")
async def create_session(body: dict, user: dict = Depends(get_current_user)):
    """AC10.1: 创建会话"""
    result = await AgentService().create_session(
        user_id=user["user_id"], title=body.get("title", "新会话")
    )
    return success(data=result)


@router.get("/sessions")
async def get_sessions(
    page: int = 1, page_size: int = 20,
    user: dict = Depends(get_current_user),
):
    """AC10.2: 会话列表"""
    result = await AgentService().get_sessions(
        user_id=user["user_id"], page=page, page_size=page_size
    )
    return success(data=result)


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, user: dict = Depends(get_current_user)):
    """AC10.3: 会话消息历史"""
    result = await AgentService().get_messages(session_id)
    return success(data=result)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    """AC10.4: 删除会话"""
    await AgentService().delete_session(session_id)
    return success()


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str, body: dict, user: dict = Depends(get_current_user)
):
    """AC12.1-12.3: SSE 流式响应

    请求体:
        {"query": "...", "context": {"filters": {...}}}
    响应:
        text/event-stream，事件类型 intent/retrieval/rank/candidates/token/done/error
    """
    query = body.get("query", "")
    filters = body.get("context", {}).get("filters")

    async def stream():
        async for event in AgentService().send_message_stream(
            session_id=session_id, user_id=user["user_id"], query=query, filters=filters
        ):
            yield event

    return StreamingResponse(stream(), media_type="text/event-stream")
