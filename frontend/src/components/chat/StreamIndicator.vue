<!--
  文件名: components/chat/StreamIndicator.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 流式输出指示器
    - 显示当前意图与策略中文标签
    - 脉冲动画 + 旋转点表示流式进行中
    - 标签：琥珀色边框 + 透明背景
-->
<template>
  <div class="stream-indicator">
    <span class="stream-indicator__dot" aria-hidden="true" />
    <span v-if="progressMessage" class="stream-indicator__text">{{ progressMessage }}</span>
    <span v-else class="stream-indicator__text">生成中</span>
    <span v-if="intentLabel" class="stream-indicator__tag">{{ intentLabel }}</span>
    <span v-if="strategyLabel" class="stream-indicator__tag">{{ strategyLabel }}</span>
  </div>
</template>

<script setup lang="ts">
/**
 * StreamIndicator 流式输出指示器
 * 根据 intent / strategy 显示中文标签，配合脉冲动画
 * 精排阶段显示 progressMessage 进度提示
 */
import { computed } from 'vue'
import { INTENT_TYPES, STRATEGY_TYPES } from '@/utils/constant'

interface StreamIndicatorProps {
  /** 意图类型（英文 key） */
  intent?: string
  /** 检索策略（英文 key） */
  strategy?: string
  /** 精排阶段进度提示 */
  progressMessage?: string
}

const props = defineProps<StreamIndicatorProps>()

/** 意图中文标签 */
const intentLabel = computed(() => {
  const key = props.intent as keyof typeof INTENT_TYPES | undefined
  return key ? INTENT_TYPES[key] : ''
})

/** 策略中文标签 */
const strategyLabel = computed(() => {
  const key = props.strategy as keyof typeof STRATEGY_TYPES | undefined
  return key ? STRATEGY_TYPES[key] : ''
})
</script>

<style scoped lang="scss">
.stream-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 4px 12px;
  font-size: var(--text-xs);
  color: var(--color-ink-soft);
  font-family: var(--font-display);

  &__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-accent);
    animation: pulse-soft 1.1s ease-in-out infinite,
      stream-spin 1.2s linear infinite;
  }

  &__text {
    letter-spacing: 0.04em;
    animation: pulse-soft 1.4s ease-in-out infinite;
  }

  &__tag {
    padding: 1px 8px;
    border: 1px solid var(--color-accent);
    border-radius: 999px;
    color: var(--color-accent-deep);
    background: transparent;
    font-size: var(--text-xs);
    letter-spacing: 0.02em;
  }
}

@keyframes stream-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
