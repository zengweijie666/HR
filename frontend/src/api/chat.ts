/**
 * 文件名: api/chat.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 对话相关接口（含 SSE 流式发送）
 */
import request from './request'
import { sseChat } from './sse'
import type { PageResult, PageQuery } from '@/types/api'
import type { ChatSession, ChatMessage, SSEHandlers } from '@/types/chat'

/**
 * 创建会话
 * @param title 会话标题
 */
export function createSession(title: string): Promise<ChatSession> {
  return request.post('/chat/sessions', { title }) as unknown as Promise<ChatSession>
}

/**
 * 获取会话分页列表
 * @param params 分页参数
 */
export function getSessions(params: PageQuery): Promise<PageResult<ChatSession>> {
  return request.get('/chat/sessions', { params }) as unknown as Promise<PageResult<ChatSession>>
}

/**
 * 获取会话历史消息
 * @param sessionId 会话 ID
 */
export function getMessages(sessionId: string): Promise<ChatMessage[]> {
  return request.get(`/chat/sessions/${sessionId}/messages`) as unknown as Promise<ChatMessage[]>
}

/**
 * 删除会话
 * @param id 会话 ID
 */
export function deleteSession(id: string): Promise<void> {
  return request.delete(`/chat/sessions/${id}`) as unknown as Promise<void>
}

/**
 * 流式发送消息
 * @param sessionId 会话 ID
 * @param query 用户提问
 * @param context 上下文（如候选人 ID 列表）
 * @param handlers SSE 事件处理器
 * @param signal 可选中止信号
 */
export function sendMessageStream(
  sessionId: string,
  query: string,
  context: Record<string, unknown>,
  handlers: SSEHandlers,
  signal?: AbortSignal,
): Promise<void> {
  // 后端路由为 POST /chat/sessions/{id}/messages（返回 SSE 流）
  // sseChat 用 fetch 直接请求，需补全 /api/v1 前缀
  const baseURL = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api/v1'
  return sseChat(
    `${baseURL}/chat/sessions/${sessionId}/messages`,
    { query, context },
    handlers,
    signal,
  )
}
