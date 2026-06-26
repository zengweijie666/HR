/**
 * 文件名: tests/api/test_sse.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 测试 SSE 解析与分发
 *   - parseSSEBlock 解析 event + data
 *   - dispatch 调用对应 handler
 */
import { describe, it, expect, vi } from 'vitest'
import { parseSSEBlock, dispatch } from '@/api/sse'
import type { SSEHandlers } from '@/types/chat'

describe('api/sse', () => {
  it('parseSSEBlock 解析 event 与 data', () => {
    const block = 'event: token\ndata: {"delta":"你好"}'
    const result = parseSSEBlock(block)
    expect(result.event).toBe('token')
    expect(result.data).toEqual({ delta: '你好' })
  })

  it('parseSSEBlock 解析多行 data 并合并', () => {
    const block = 'event: done\ndata: {"message_id":"m1"\ndata: ,"response":"hi"}'
    const result = parseSSEBlock(block)
    expect(result.event).toBe('done')
    expect(result.data).toEqual({ message_id: 'm1', response: 'hi' })
  })

  it('parseSSEBlock 无 event 行时默认 message', () => {
    const block = 'data: "plain"'
    const result = parseSSEBlock(block)
    expect(result.event).toBe('message')
    expect(result.data).toBe('plain')
  })

  it('dispatch 按 event 调用对应 handler', () => {
    const onToken = vi.fn()
    const onDone = vi.fn()
    const handlers: SSEHandlers = { onToken, onDone }

    dispatch('token', { delta: 'X' }, handlers)
    expect(onToken).toHaveBeenCalledWith('X')

    dispatch('done', { message_id: 'm1', response: 'r' }, handlers)
    expect(onDone).toHaveBeenCalledWith({ message_id: 'm1', response: 'r' })
  })

  it('dispatch 未注册 handler 时不报错', () => {
    expect(() => dispatch('intent', { intent: 'search', strategy: 'direct' }, {})).not.toThrow()
  })
})
