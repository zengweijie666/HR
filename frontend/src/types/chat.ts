/**
 * 文件名: types/chat.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 对话类型，对应 API-Design.md 3.0 / 0.5 SSE
 */
import type { CandidateCard } from './candidate'

export interface ChatSession {
  session_id: string
  title: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  message_id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  intent: string | null
  strategy: string | null
  candidates: CandidateCard[] | null
  created_at: string
}

/** SSE 事件类型，对应 API-Design.md 0.5 */
export type SSEEvent =
  | { event: 'intent'; data: { intent: string; strategy: string } }
  | { event: 'rewrite'; data: { query: string; rewrites: string[] } }
  | { event: 'retrieval'; data: { count: number; candidate_ids: string[] } }
  | { event: 'rank'; data: { ranked: { candidate_id: string; score: number }[] } }
  | { event: 'token'; data: { delta: string } }
  | { event: 'candidates'; data: { candidates: CandidateCard[] } }
  | { event: 'done'; data: { message_id: string; response: string; title?: string | null } }
  | { event: 'error'; data: { code: number; message: string } }

export interface SSEHandlers {
  onIntent?: (data: { intent: string; strategy: string }) => void
  onRewrite?: (data: { query: string; rewrites: string[] }) => void
  onRetrieval?: (data: { count: number; candidate_ids: string[] }) => void
  onRank?: (data: { ranked: { candidate_id: string; score: number }[] }) => void
  onToken?: (delta: string) => void
  onCandidates?: (candidates: CandidateCard[]) => void
  onDone?: (data: { message_id: string; response: string; title?: string | null }) => void
  onError?: (data: { code: number; message: string }) => void
}
