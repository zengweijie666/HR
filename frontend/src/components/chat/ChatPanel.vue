<!--
  文件名: components/chat/ChatPanel.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 对话主面板
    - 顶部：当前会话标题区
    - 中部：消息列表（可滚动）
    - 底部：输入区 + 发送按钮
    - 流式输出时显示 StreamIndicator
    - 发送流程：校验 → addMessage(user) → addMessage(assistant占位) → startStream → sendMessageStream → finally stopStream
-->
<template>
  <section class="chat-panel">
    <!-- 顶部标题 -->
    <header class="chat-panel__header">
      <h3 class="chat-panel__title decor-line">{{ currentTitle }}</h3>
      <div v-if="chatStore.streaming" class="chat-panel__indicator">
        <StreamIndicator :intent="chatStore.intent" :strategy="chatStore.strategy" />
      </div>
    </header>

    <!-- 消息列表 -->
    <div ref="messageListRef" class="chat-panel__messages">
      <EmptyState v-if="!chatStore.messages.length" text="开始一段新的对话" />
      <MessageBubble
        v-for="msg in chatStore.messages"
        :key="msg.message_id"
        :message="msg"
      />
    </div>

    <!-- 输入区 -->
    <footer class="chat-panel__input">
      <el-input
        v-model="draft"
        type="textarea"
        :rows="2"
        resize="none"
        placeholder="输入你的问题，回车发送"
        :disabled="chatStore.streaming"
        @keyup.enter="handleSend"
      />
      <el-button
        type="primary"
        class="chat-panel__send"
        :disabled="!canSend"
        :loading="chatStore.streaming"
        @click="handleSend"
      >
        <el-icon class="chat-panel__send-icon"><Promotion /></el-icon>
        发送
      </el-button>
    </footer>
  </section>
</template>

<script setup lang="ts">
/**
 * ChatPanel 对话主面板
 * 串联 useChatStore / useAuthStore，处理发送与流式接收
 */
import { computed, nextTick, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import { sendMessageStream } from '@/api/chat'
import MessageBubble from './MessageBubble.vue'
import StreamIndicator from './StreamIndicator.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { ChatMessage } from '@/types/chat'

const chatStore = useChatStore()
const authStore = useAuthStore()

const draft = ref<string>('')
const messageListRef = ref<HTMLElement | null>(null)

/** 当前会话标题 */
const currentTitle = computed(() => {
  if (!chatStore.currentSessionId) return '请选择或新建会话'
  const session = chatStore.sessions.find(
    (s) => s.session_id === chatStore.currentSessionId,
  )
  return session?.title || '当前会话'
})

/** 是否可发送 */
const canSend = computed(
  () => !!draft.value.trim() && !!chatStore.currentSessionId && !chatStore.streaming,
)

/** 生成消息 ID（前端临时） */
function genMessageId(): string {
  return `tmp-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

/** 滚动到底部 */
function scrollToBottom(): void {
  nextTick(() => {
    const el = messageListRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

/** 监听消息数量变化自动滚动 */
watch(
  () => chatStore.messages.length,
  () => scrollToBottom(),
)

/** 处理发送 */
async function handleSend(): Promise<void> {
  const query = draft.value.trim()
  if (!query) return
  if (!chatStore.currentSessionId) {
    ElMessage.warning('请先选择或新建会话')
    return
  }
  if (chatStore.streaming) return

  const sessionId = chatStore.currentSessionId
  const now = new Date().toISOString()

  // 1. 追加 user 消息
  const userMsg: ChatMessage = {
    message_id: genMessageId(),
    session_id: sessionId,
    role: 'user',
    content: query,
    intent: null,
    strategy: null,
    candidates: null,
    created_at: now,
  }
  chatStore.addMessage(userMsg)

  // 2. 追加 assistant 占位消息
  const assistantMsg: ChatMessage = {
    message_id: genMessageId(),
    session_id: sessionId,
    role: 'assistant',
    content: '',
    intent: null,
    strategy: null,
    candidates: null,
    created_at: now,
  }
  chatStore.addMessage(assistantMsg)

  // 3. 启动流式
  chatStore.startStream()
  draft.value = ''

  // 4. 调用流式接口
  try {
    await sendMessageStream(
      sessionId,
      query,
      { user_id: authStore.user?.user_id },
      {
        onIntent: (data) => {
          chatStore.setIntent(data.intent)
          chatStore.setStrategy(data.strategy)
          // 同步 intent/strategy 到当前 assistant 消息对象，供 Workbench watch 判断意图
          const last = chatStore.messages[chatStore.messages.length - 1]
          if (last && last.role === 'assistant') {
            last.intent = data.intent
            last.strategy = data.strategy
          }
        },
        onToken: (delta) => chatStore.appendToken(delta),
        onCandidates: (candidates) => {
          const last = chatStore.messages[chatStore.messages.length - 1]
          if (last && last.role === 'assistant') {
            last.candidates = candidates
          }
        },
        onDone: (data) => {
          chatStore.setIntent('')
          chatStore.setStrategy('')
          // 首条消息后端会回传新标题，同步到 sessions 列表
          if (data.title) {
            chatStore.updateSessionTitle(sessionId, data.title)
          }
        },
        onError: (data) => {
          ElMessage.error(data.message || '流式响应出错')
        },
      },
    )
  } catch (err) {
    const msg = err instanceof Error ? err.message : '发送失败'
    ElMessage.error(msg)
  } finally {
    // 6. 停止流式
    chatStore.stopStream()
  }
}
</script>

<style scoped lang="scss">
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background-color: var(--color-bg);

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-4);
    padding: var(--space-4) var(--space-5);
    border-bottom: 1px solid var(--color-line);
    background-color: var(--color-bg-card);
  }

  &__title {
    font-family: var(--font-display);
    font-size: var(--text-lg);
    font-weight: 500;
    color: var(--color-primary);
    margin: 0;
    padding-bottom: 6px;
  }

  &__indicator {
    flex-shrink: 0;
  }

  &__messages {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: var(--space-5);
  }

  &__input {
    display: flex;
    align-items: flex-end;
    gap: var(--space-3);
    padding: var(--space-4) var(--space-5);
    border-top: 1px solid var(--color-line);
    background-color: var(--color-bg-card);

    :deep(.el-textarea__inner) {
      border-radius: var(--radius-md);
      font-family: var(--font-body);
    }
  }

  &__send {
    flex-shrink: 0;
    height: 40px;
  }

  &__send-icon {
    margin-right: 4px;
  }
}
</style>
