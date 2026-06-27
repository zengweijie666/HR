/**
 * 文件名: api/sse.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: SSE 流式响应封装
 *   - parseSSEBlock: 解析单个 SSE 事件块
 *   - dispatch: 按事件名分发到对应 handler
 *   - sseChat: 基于 fetch + ReadableStream 的流式请求
 */
import type { SSEHandlers } from '@/types/chat'
import type { CandidateCard } from '@/types/candidate'

/** 解析后的事件结构，data 在 SSE 场景为允许的临时数据 */
export interface SSEParsed {
  event: string
  data: unknown
}

/**
 * 解析单个 SSE 事件块
 * @param block 单个事件块字符串（按 \n 分隔的行）
 * @returns { event, data } event 默认 'message'，data 尝试 JSON.parse，失败则保留原始字符串
 */
export function parseSSEBlock(block: string): SSEParsed {
  const lines = block.split('\n')
  let event = 'message'
  const dataLines: string[] = []
  for (const line of lines) {
    if (line.startsWith('event:')) {
      event = line.slice('event:'.length).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice('data:'.length).replace(/^ /, ''))
    }
  }
  const dataRaw = dataLines.join('\n')
  let data: unknown = dataRaw
  if (dataRaw) {
    try {
      data = JSON.parse(dataRaw)
    } catch {
      data = dataRaw
    }
  }
  return { event, data }
}

/**
 * 根据 event 名将 data 分发到对应 handler
 * @param event 事件名
 * @param data 事件数据
 * @param handlers 处理器集合
 */
export function dispatch(event: string, data: unknown, handlers: SSEHandlers): void {
  switch (event) {
    case 'intent':
      handlers.onIntent?.(data as { intent: string; strategy: string })
      break
    case 'rewrite':
      handlers.onRewrite?.(data as { query: string; rewrites: string[] })
      break
    case 'retrieval':
      handlers.onRetrieval?.(data as { count: number; candidate_ids: string[] })
      break
    case 'rank':
      handlers.onRank?.(data as { ranked: { candidate_id: string; score: number }[] })
      break
    case 'token':
      handlers.onToken?.((data as { delta: string }).delta)
      break
    case 'candidates':
      handlers.onCandidates?.(data as CandidateCard[])
      break
    case 'done':
      handlers.onDone?.(data as { message_id: string; response: string; title?: string | null })
      break
    case 'error':
      handlers.onError?.(data as { code: number; message: string })
      break
    default:
      break
  }
}

/**
 * 基于 fetch + ReadableStream 的 SSE 流式请求
 * @param url 请求地址
 * @param body 请求体（JSON 序列化）
 * @param handlers SSE 事件处理器集合
 * @param signal 可选 AbortSignal，用于中止流
 * @returns Promise<void>，流读取完毕后 resolve
 */
export async function sseChat(
  url: string,
  body: Record<string, unknown>,
  handlers: SSEHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const token = localStorage.getItem('access_token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const resp = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
    signal,
  })
  if (!resp.ok) {
    throw new Error(`SSE 请求失败: HTTP ${resp.status}`)
  }
  if (!resp.body) {
    throw new Error('SSE 响应无 body 流')
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const block = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      if (!block.trim()) continue
      const { event, data } = parseSSEBlock(block)
      dispatch(event, data, handlers)
    }
  }

  // 刷新缓冲区中剩余内容
  if (buffer.trim()) {
    const { event, data } = parseSSEBlock(buffer)
    dispatch(event, data, handlers)
  }
}
