<!--
  文件名: components/chat/MessageBubble.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 对话消息气泡
    - user 靠右（主色背景白字）/ assistant 靠左（卡片背景 + 边框）
    - 头像：user 用首字"我"，assistant 用琥珀点 + "AI"
    - 简单保留换行渲染
    - 有候选人时气泡下方展示缩略列表
-->
<template>
  <div class="msg" :class="`msg--${message.role}`">
    <!-- 头像 -->
    <div class="msg__avatar" :class="`msg__avatar--${message.role}`">
      <template v-if="message.role === 'user'">我</template>
      <template v-else>
        <span class="msg__avatar-dot" />
        <span class="msg__avatar-label">AI</span>
      </template>
    </div>

    <div class="msg__main">
      <div class="msg__bubble" :class="`msg__bubble--${message.role}`">
        <p class="msg__content">{{ message.content || '…' }}</p>
      </div>

      <!-- 候选人缩略列表 -->
      <div v-if="message.candidates && message.candidates.length" class="msg__candidates">
        <div
          v-for="c in message.candidates"
          :key="c.candidate_id"
          class="msg__candidate"
        >
          <span class="msg__candidate-name">{{ c.name }}</span>
          <span class="msg__candidate-score">{{ c.score }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * MessageBubble 对话消息气泡
 * 渲染单条 user/assistant 消息及其候选人附件
 */
import type { ChatMessage } from '@/types/chat'

interface MessageBubbleProps {
  /** 消息对象 */
  message: ChatMessage
}

defineProps<MessageBubbleProps>()
</script>

<style scoped lang="scss">
.msg {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  margin-bottom: var(--space-5);

  &--user {
    flex-direction: row-reverse;
  }

  &__avatar {
    flex-shrink: 0;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-display);
    font-size: var(--text-xs);
    font-weight: 600;

    &--user {
      background-color: var(--color-primary);
      color: #fff;
    }
    &--assistant {
      background-color: var(--color-accent-glow);
      color: var(--color-accent-deep);
      gap: 2px;
    }
  }

  &__avatar-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-accent);
  }

  &__avatar-label {
    font-size: 10px;
    line-height: 1;
  }

  &__main {
    max-width: 78%;
    display: flex;
    flex-direction: column;
  }

  &--user .msg__main {
    align-items: flex-end;
  }

  &__bubble {
    padding: var(--space-3) var(--space-4);
    font-size: var(--text-base);
    line-height: 1.6;
    word-break: break-word;

    &--user {
      background-color: var(--color-primary);
      color: #fff;
      border-radius: var(--radius-lg) var(--radius-sm) var(--radius-lg) var(--radius-lg);
    }
    &--assistant {
      background-color: var(--color-bg-card);
      color: var(--color-ink);
      border: 1px solid var(--color-line);
      border-radius: var(--radius-sm) var(--radius-lg) var(--radius-lg) var(--radius-lg);
    }
  }

  &__content {
    margin: 0;
    white-space: pre-wrap;
  }

  &__candidates {
    margin-top: var(--space-2);
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  &--user .msg__candidates {
    justify-content: flex-end;
  }

  &__candidate {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    background-color: var(--color-primary-tint);
    border-radius: 999px;
    font-size: var(--text-xs);
  }

  &__candidate-name {
    color: var(--color-primary);
    font-weight: 500;
  }

  &__candidate-score {
    color: var(--color-accent-deep);
    font-family: var(--font-mono);
    font-weight: 600;
  }
}
</style>
