<!--
  文件名: components/common/LoadingOverlay.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 加载遮罩组件
    - absolute 定位半透明白底遮罩
    - 居中旋转图标 + 文字
    - 用 --color-primary 做图标颜色
-->
<template>
  <transition name="loading-fade">
    <div v-if="visible" class="loading-overlay" role="status" aria-live="polite">
      <div class="loading-overlay__inner">
        <span class="loading-overlay__spinner" aria-hidden="true">
          <svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <circle cx="20" cy="20" r="15" fill="none" stroke="var(--color-primary-tint)" stroke-width="3" />
            <circle
              cx="20"
              cy="20"
              r="15"
              fill="none"
              stroke="var(--color-primary)"
              stroke-width="3"
              stroke-linecap="round"
              stroke-dasharray="70 40"
            />
          </svg>
        </span>
        <span class="loading-overlay__text">{{ text }}</span>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
/**
 * LoadingOverlay 加载遮罩组件
 * 用于在容器内覆盖一层加载状态指示
 */
interface LoadingOverlayProps {
  /** 是否显示遮罩 */
  visible?: boolean
  /** 加载提示文案，默认 '加载中...' */
  text?: string
}

withDefaults(defineProps<LoadingOverlayProps>(), {
  visible: false,
  text: '加载中...',
})
</script>

<style scoped lang="scss">
.loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(2px);

  &__inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-3);
  }

  &__spinner {
    width: 40px;
    height: 40px;
    display: inline-flex;

    svg {
      width: 100%;
      height: 100%;
      animation: loading-spin 0.9s linear infinite;
    }
  }

  &__text {
    font-family: var(--font-display);
    font-size: var(--text-sm);
    color: var(--color-primary);
    letter-spacing: 0.02em;
  }
}

@keyframes loading-spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: opacity var(--duration-fast) var(--ease-out);
}
.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}
</style>
