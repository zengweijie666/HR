/**
 * 文件名: stores/chat.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 对话状态管理（Composition API 风格）
 *   - sessions 会话列表 / currentSessionId 当前会话
 *   - messages 当前会话消息 / streaming 流式状态
 *   - intent / strategy 当前意图与策略
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatSession, ChatMessage } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  /** 会话列表 */
  const sessions = ref<ChatSession[]>([])
  /** 当前会话 ID */
  const currentSessionId = ref<string>('')
  /** 当前会话消息列表 */
  const messages = ref<ChatMessage[]>([])
  /** 是否正在流式输出 */
  const streaming = ref<boolean>(false)
  /** 当前意图 */
  const intent = ref<string>('')
  /** 当前检索策略 */
  const strategy = ref<string>('')

  /**
   * 设置会话列表
   * @param list 会话数组
   */
  function setSessions(list: ChatSession[]): void {
    sessions.value = list
  }

  /**
   * 设置当前会话 ID
   * @param id 会话 ID
   */
  function setCurrentSession(id: string): void {
    currentSessionId.value = id
  }

  /**
   * 设置当前会话消息列表
   * @param list 消息数组
   */
  function setMessages(list: ChatMessage[]): void {
    messages.value = list
  }

  /**
   * 追加一条消息
   * @param msg 消息对象
   */
  function addMessage(msg: ChatMessage): void {
    messages.value.push(msg)
  }

  /**
   * 将 token 追加到最后一条 assistant 消息的 content
   * @param delta 增量文本
   */
  function appendToken(delta: string): void {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content += delta
    }
  }

  /**
   * 设置当前意图
   * @param i 意图名
   */
  function setIntent(i: string): void {
    intent.value = i
  }

  /**
   * 设置当前策略
   * @param s 策略名
   */
  function setStrategy(s: string): void {
    strategy.value = s
  }

  /**
   * 更新指定会话的标题（用于首条消息后由后端 done 事件回传新标题）
   * @param sessionId 会话 ID
   * @param title 新标题
   */
  function updateSessionTitle(sessionId: string, title: string): void {
    if (!sessionId || !title) return
    const target = sessions.value.find((s) => s.session_id === sessionId)
    if (target) {
      target.title = title
    }
  }

  /** 标记流式输出开始 */
  function startStream(): void {
    streaming.value = true
  }

  /** 标记流式输出结束 */
  function stopStream(): void {
    streaming.value = false
  }

  /** 重置：清空消息与意图/策略/流式状态 */
  function reset(): void {
    messages.value = []
    intent.value = ''
    strategy.value = ''
    streaming.value = false
  }

  return {
    sessions,
    currentSessionId,
    messages,
    streaming,
    intent,
    strategy,
    setSessions,
    setCurrentSession,
    setMessages,
    addMessage,
    appendToken,
    setIntent,
    setStrategy,
    updateSessionTitle,
    startStream,
    stopStream,
    reset,
  }
})
