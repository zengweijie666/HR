<!--
  文件名: components/common/EmptyState.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 空状态占位组件
    - 基于 el-empty 自定义实现
    - 装饰性 SVG 几何插画（墨绿圆环 + 琥珀点）
    - 衬线字体文案增加质感
-->
<template>
  <div class="empty-state" role="status" aria-live="polite">
    <div class="empty-state__visual">
      <svg
        class="empty-state__art"
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <!-- 墨绿圆环 -->
        <circle cx="60" cy="60" r="38" stroke="var(--color-primary)" stroke-width="1.5" opacity="0.35" />
        <circle cx="60" cy="60" r="26" stroke="var(--color-primary-soft)" stroke-width="1" opacity="0.55" stroke-dasharray="3 4" />
        <!-- 琥珀点 -->
        <circle cx="60" cy="22" r="4" fill="var(--color-accent)" />
        <circle cx="98" cy="60" r="3" fill="var(--color-accent-soft)" />
        <circle cx="60" cy="98" r="2.5" fill="var(--color-accent-deep)" />
        <!-- 中心文档图标 -->
        <g v-if="!icon" transform="translate(48 48)">
          <rect x="0" y="0" width="24" height="30" rx="3" fill="var(--color-bg-card)" stroke="var(--color-primary)" stroke-width="1.4" />
          <line x1="5" y1="8" x2="19" y2="8" stroke="var(--color-primary-soft)" stroke-width="1.2" stroke-linecap="round" />
          <line x1="5" y1="13" x2="19" y2="13" stroke="var(--color-primary-soft)" stroke-width="1.2" stroke-linecap="round" />
          <line x1="5" y1="18" x2="14" y2="18" stroke="var(--color-primary-soft)" stroke-width="1.2" stroke-linecap="round" />
        </g>
        <g v-else transform="translate(48 48)">
          <component :is="icon" />
        </g>
      </svg>
    </div>
    <p class="empty-state__text">{{ text }}</p>
    <div v-if="$slots.default" class="empty-state__action">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * EmptyState 空状态组件
 * 用于列表/卡片无数据时的优雅占位
 */
import type { Component } from 'vue'

interface EmptyStateProps {
  /** 提示文案，默认 '暂无数据' */
  text?: string
  /** 自定义图标组件（覆盖默认文档图标），可选 */
  icon?: Component
}

withDefaults(defineProps<EmptyStateProps>(), {
  text: '暂无数据',
  icon: undefined,
})
</script>

<style scoped lang="scss">
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10) var(--space-6);
  text-align: center;
  animation: fadeIn var(--duration-base) var(--ease-out) both;

  &__visual {
    margin-bottom: var(--space-5);
    opacity: 0.92;
  }

  &__art {
    width: 120px;
    height: 120px;
  }

  &__text {
    font-family: var(--font-display);
    font-size: var(--text-md);
    color: var(--color-ink-mute);
    letter-spacing: 0.01em;
    margin: 0;
  }

  &__action {
    margin-top: var(--space-5);
  }
}
</style>
