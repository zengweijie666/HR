<!--
  文件名: views/Workbench.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 工作台
    - 三栏布局：会话列表 / 对话面板 / 候选人推荐
    - 数据流：watch chatStore.messages 末尾 assistant 消息的 candidates → 同步本地推荐区
    - 会话管理：onMounted 加载 sessions，新建/选择/删除会话调用 chat API
-->
<template>
  <div class="workbench">
    <!-- 左：会话列表 -->
    <section class="workbench__section workbench__sessions">
      <SessionList
        :sessions="chatStore.sessions"
        :current-id="chatStore.currentSessionId"
        @new="handleNewSession"
        @select="handleSelectSession"
        @delete="handleDeleteSession"
      />
    </section>

    <!-- 中：对话面板 -->
    <section class="workbench__section workbench__chat-section chat-section">
      <ChatPanel />
    </section>

    <!-- 右：候选人推荐 -->
    <section class="workbench__section workbench__candidate-section candidate-section">
      <div class="candidate-section__head">
        <span class="eyebrow">RECOMMENDATIONS</span>
        <h3 class="candidate-section__title decor-line">推荐候选人</h3>
      </div>

      <div class="candidate-section__body">
        <div v-if="recommendCandidates.length" class="candidate-section__list">
          <CandidateCard
            v-for="c in recommendCandidates"
            :key="c.candidate_id"
            :candidate="c"
            @select="handleSelectCandidate"
          />
        </div>
        <EmptyState v-else text="对话后将显示推荐候选人" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
/**
 * Workbench 工作台
 * 串联对话会话与候选人推荐展示
 */
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import SessionList from '@/components/chat/SessionList.vue'
import ChatPanel from '@/components/chat/ChatPanel.vue'
import CandidateCard from '@/components/candidate/CandidateCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useChatStore } from '@/stores/chat'
import { createSession, deleteSession, getMessages, getSessions } from '@/api/chat'
import type { ChatSession } from '@/types/chat'
import type { CandidateCard as CandidateCardType } from '@/types/candidate'

const chatStore = useChatStore()
const router = useRouter()

/** 推荐候选人最大展示数量（只展示最相关的 Top N，避免低相关性候选人干扰） */
const MAX_RECOMMEND_CARDS = 5

/** 推荐候选人列表（来自最近一条 assistant 消息，只展示 Top N） */
const recommendCandidates = ref<CandidateCardType[]>([])

/** 从候选人列表中截取 Top N 用于推荐区展示 */
function sliceTopCandidates(candidates: CandidateCardType[] | null | undefined): CandidateCardType[] {
  if (!candidates) return []
  return candidates.slice(0, MAX_RECOMMEND_CARDS)
}

/** 每页会话数 */
const PAGE_SIZE = 20

/**
 * 加载会话列表
 */
async function loadSessions(): Promise<void> {
  try {
    const res = await getSessions({ page: 1, page_size: PAGE_SIZE })
    chatStore.setSessions(res.list || [])
  } catch (err) {
    const msg = err instanceof Error ? err.message : '加载会话列表失败'
    ElMessage.error(msg)
  }
}

/**
 * 加载指定会话的消息
 * @param sessionId 会话 ID
 */
async function loadMessages(sessionId: string): Promise<void> {
  try {
    const list = await getMessages(sessionId)
    chatStore.setMessages(list || [])
    // 切换会话时，用最后一条 assistant 消息的 candidates 初始化推荐区
    const lastAssistant = [...(list || [])].reverse().find((m) => m.role === 'assistant')
    recommendCandidates.value = sliceTopCandidates(lastAssistant?.candidates)
  } catch (err) {
    const msg = err instanceof Error ? err.message : '加载会话消息失败'
    ElMessage.error(msg)
  }
}

/**
 * 新建会话
 */
async function handleNewSession(): Promise<void> {
  try {
    const session: ChatSession = await createSession('新会话')
    chatStore.setSessions([session, ...chatStore.sessions])
    chatStore.setCurrentSession(session.session_id)
    chatStore.reset()
    await loadSessions()
  } catch (err) {
    const msg = err instanceof Error ? err.message : '新建会话失败'
    ElMessage.error(msg)
  }
}

/**
 * 选择会话
 * @param id 会话 ID
 */
async function handleSelectSession(id: string): Promise<void> {
  chatStore.setCurrentSession(id)
  chatStore.reset()
  await loadMessages(id)
}

/**
 * 删除会话
 * @param id 会话 ID
 */
async function handleDeleteSession(id: string): Promise<void> {
  try {
    await deleteSession(id)
    if (chatStore.currentSessionId === id) {
      chatStore.setCurrentSession('')
      chatStore.reset()
    }
    await loadSessions()
    ElMessage.success('已删除会话')
  } catch (err) {
    const msg = err instanceof Error ? err.message : '删除会话失败'
    ElMessage.error(msg)
  }
}

/**
 * 点击候选人卡片跳转详情
 * @param candidate 候选人对象
 */
function handleSelectCandidate(candidate: CandidateCardType): void {
  if (candidate.resume_id) {
    router.push(`/resumes/${candidate.resume_id}`)
  }
}

/**
 * 监听消息变化，同步推荐候选人
 * - 检索类意图（search/compare/detail）：用最新 candidates 覆盖卡片（含空结果，体现'无匹配'）
 * - 非检索类意图（chitchat/qa）：保留既有卡片，避免追问时卡片消失
 *
 * 监听源说明：同时监听 messages.length（新消息加入）和最后一条消息的 candidates
 * （SSE onCandidates 通过 mutate 字段更新，不改变 length），确保两种场景都能触发。
 */
watch(
  () => [
    chatStore.messages.length,
    chatStore.messages[chatStore.messages.length - 1]?.candidates,
  ],
  () => {
    const last = chatStore.messages[chatStore.messages.length - 1]
    if (!last || last.role !== 'assistant') return
    const intent = last.intent
    // 闲聊/通用问答：保留既有推荐卡片
    if (intent === 'chitchat' || intent === 'qa') return
    // 检索类意图：覆盖（含空结果），只展示 Top N
    recommendCandidates.value = sliceTopCandidates(last.candidates)
  },
)

onMounted(() => {
  void loadSessions()
})
</script>

<style scoped lang="scss">
.workbench {
  display: flex;
  gap: var(--space-4);
  height: 100%;
  min-height: 0;

  &__section {
    display: flex;
    flex-direction: column;
    background-color: var(--color-bg-card);
    border: 1px solid var(--color-line);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
    min-height: 0;
  }

  &__sessions {
    flex: 0 0 260px;
    padding: var(--space-4);
  }

  &__chat-section {
    flex: 1;
    min-width: 0;
  }

  &__candidate-section {
    flex: 0 0 380px;
  }
}

/* ============ 候选人区 ============ */
.candidate-section {
  &__head {
    padding: var(--space-5) var(--space-5) var(--space-4);
    border-bottom: 1px solid var(--color-line);
  }

  &__title {
    margin-top: var(--space-2);
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-weight: 500;
    color: var(--color-primary);
    padding-bottom: 8px;
  }

  &__body {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: var(--space-4);
  }

  &__list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }
}
</style>
