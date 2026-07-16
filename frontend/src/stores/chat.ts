/**
 * 文件名: stores/chat.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 对话状态管理（Composition API 风格）
 *   - sessions 会话列表 / currentSessionId 当前会话
 *   - messages 当前会话消息列表 / streaming 流式状态
 *   - intent / strategy 当前意图与策略
 *   - startStreamSession 集中管理 SSE 生命周期，组件卸载不中止流
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatSession, ChatMessage, SSEHandlers } from '@/types/chat'
import { sendMessageStream } from '@/api/chat'

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
  /** 当前精排阶段进度提示 */
  const progressMessage = ref<string>('')

  /**
   * 当前进行中的 SSE 请求 AbortController
   * 保存在 store 而非组件，组件卸载不会触发中止，切换路由后回来仍能继续接收
   */
  let currentAbortController: AbortController | null = null

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
   * 设置当前进度提示
   * @param msg 进度提示文本
   */
  function setProgressMessage(msg: string): void {
    progressMessage.value = msg
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
    progressMessage.value = ''
    streaming.value = false
  }

  /**
   * 启动 SSE 流式会话（在 store 层管理生命周期）
   *
   * 将 SSE 请求的 AbortController 存于 store 而非组件实例，
   * 组件卸载（切换路由）不会自动中止流，回到工作台仍能继续接收回复。
   * 只有用户主动切换会话或重新发送时才中止上一个流。
   *
   * @param sessionId 会话 ID
   * @param query 用户查询
   * @param context 上下文（如 user_id）
   * @param handlers SSE 事件处理器
   * @returns Promise<void>，流读取完毕后 resolve
   */
  async function startStreamSession(
    sessionId: string,
    query: string,
    context: Record<string, unknown>,
    handlers: SSEHandlers,
  ): Promise<void> {
    // 中止上一个进行中的流（切换会话或重新发送场景）
    abortStream()
    const abortController = new AbortController()
    currentAbortController = abortController
    try {
      await sendMessageStream(
        sessionId,
        query,
        context,
        handlers,
        abortController.signal,
      )
    } finally {
      if (currentAbortController === abortController) {
        currentAbortController = null
      }
      stopStream()
    }
  }

  /**
   * 主动中止当前进行中的 SSE 流（用于切换会话等场景）
   *
   * 与组件卸载不同：切换会话时旧会话的 SSE 应被中止，
   * 避免旧回复串入新会话消息列表。
   */
  function abortStream(): void {
    if (currentAbortController) {
      currentAbortController.abort()
      currentAbortController = null
      stopStream()
    }
  }

  return {
    sessions,
    currentSessionId,
    messages,
    streaming,
    intent,
    strategy,
    progressMessage,
    setSessions,
    setCurrentSession,
    setMessages,
    addMessage,
    appendToken,
    setIntent,
    setStrategy,
    setProgressMessage,
    updateSessionTitle,
    startStream,
    stopStream,
    reset,
    startStreamSession,
    abortStream,
  }
})
