/**
 * 文件名: tests/stores/test_chat_store.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 测试 chat store
 *   - 初始为空
 *   - setSessions
 *   - addMessage
 *   - appendToken
 *   - startStream/stopStream
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'
import type { ChatSession, ChatMessage } from '@/types/chat'

function makeMessage(role: 'user' | 'assistant', content: string): ChatMessage {
  return {
    message_id: 'm1',
    session_id: 's1',
    role,
    content,
    intent: null,
    strategy: null,
    candidates: null,
    created_at: '',
  }
}

describe('stores/chat', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('初始状态为空', () => {
    const chat = useChatStore()
    expect(chat.sessions).toEqual([])
    expect(chat.messages).toEqual([])
    expect(chat.streaming).toBe(false)
    expect(chat.currentSessionId).toBe('')
    expect(chat.intent).toBe('')
    expect(chat.strategy).toBe('')
  })

  it('setSessions 设置会话列表', () => {
    const chat = useChatStore()
    const sessions: ChatSession[] = [
      { session_id: 's1', title: '会话一', created_at: '', updated_at: '' },
    ]
    chat.setSessions(sessions)
    expect(chat.sessions).toHaveLength(1)
    expect(chat.sessions[0].session_id).toBe('s1')
  })

  it('addMessage 追加消息到列表', () => {
    const chat = useChatStore()
    chat.addMessage(makeMessage('user', 'hi'))
    expect(chat.messages).toHaveLength(1)
    expect(chat.messages[0].content).toBe('hi')
  })

  it('appendToken 追加到最后一条 assistant 消息', () => {
    const chat = useChatStore()
    chat.addMessage(makeMessage('user', '你好'))
    chat.addMessage(makeMessage('assistant', ''))
    chat.appendToken('你')
    chat.appendToken('好')
    expect(chat.messages[1].content).toBe('你好')
  })

  it('appendToken 不影响非 assistant 末尾消息', () => {
    const chat = useChatStore()
    chat.addMessage(makeMessage('user', 'hi'))
    chat.appendToken('X')
    expect(chat.messages[0].content).toBe('hi')
  })

  it('startStream/stopStream 控制 streaming 状态', () => {
    const chat = useChatStore()
    expect(chat.streaming).toBe(false)
    chat.startStream()
    expect(chat.streaming).toBe(true)
    chat.stopStream()
    expect(chat.streaming).toBe(false)
  })

  it('reset 清空消息与意图/策略/流式状态', () => {
    const chat = useChatStore()
    chat.addMessage(makeMessage('user', 'hi'))
    chat.setIntent('search')
    chat.setStrategy('direct')
    chat.startStream()
    chat.reset()
    expect(chat.messages).toEqual([])
    expect(chat.intent).toBe('')
    expect(chat.strategy).toBe('')
    expect(chat.streaming).toBe(false)
  })
})
