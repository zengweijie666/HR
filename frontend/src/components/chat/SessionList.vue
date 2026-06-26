<!--
  文件名: components/chat/SessionList.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 对话会话列表
    - 顶部"新建会话"按钮（全宽 + Plus 图标）
    - 列表项：title + 相对时间
    - 选中态：左侧 2px 琥珀边框 + tint 背景
    - hover 显示删除按钮
-->
<template>
  <div class="session-list">
    <el-button type="primary" class="session-list__new" @click="handleNew">
      <el-icon class="session-list__new-icon"><Plus /></el-icon>
      新建会话
    </el-button>

    <div class="session-list__items">
      <div
        v-for="s in sessions"
        :key="s.session_id"
        class="session-list__item"
        :class="{ 'is-active': s.session_id === currentId }"
        @click="handleSelect(s.session_id)"
      >
        <div class="session-list__item-main">
          <div class="session-list__item-title">{{ s.title || '未命名会话' }}</div>
          <div class="session-list__item-time">{{ formatRelative(s.updated_at || s.created_at) }}</div>
        </div>
        <button
          type="button"
          class="session-list__del"
          aria-label="删除会话"
          @click.stop="handleDelete(s.session_id)"
        >
          <el-icon><Delete /></el-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * SessionList 对话会话列表
 * 管理会话项的展示与选择/删除交互
 */
import { Plus, Delete } from '@element-plus/icons-vue'
import { formatRelative } from '@/utils/format'
import type { ChatSession } from '@/types/chat'

interface SessionListProps {
  /** 会话列表 */
  sessions: ChatSession[]
  /** 当前选中会话 ID */
  currentId?: string
}

defineProps<SessionListProps>()

const emit = defineEmits<{
  /** 新建会话 */
  (e: 'new'): void
  /** 选择会话 */
  (e: 'select', id: string): void
  /** 删除会话 */
  (e: 'delete', id: string): void
}>()

/** 新建会话 */
function handleNew(): void {
  emit('new')
}

/** 选择会话 */
function handleSelect(id: string): void {
  emit('select', id)
}

/** 删除会话 */
function handleDelete(id: string): void {
  emit('delete', id)
}
</script>

<style scoped lang="scss">
.session-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);

  &__new {
    width: 100%;
    justify-content: center;
  }

  &__new-icon {
    margin-right: 4px;
  }

  &__items {
    display: flex;
    flex-direction: column;
    gap: 2px;
    overflow-y: auto;
  }

  &__item {
    position: relative;
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-3) var(--space-3) var(--space-3) var(--space-4);
    cursor: pointer;
    border-radius: var(--radius-md);
    border-left: 2px solid transparent;
    transition: background-color var(--duration-fast) var(--ease-out),
      border-color var(--duration-fast) var(--ease-out);

    &:hover {
      background-color: var(--color-bg-overlay);
    }

    &.is-active {
      background-color: var(--color-primary-tint);
      border-left-color: var(--color-accent);
    }
  }

  &__item-main {
    flex: 1;
    min-width: 0;
  }

  &__item-title {
    font-size: var(--text-sm);
    color: var(--color-ink);
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__item-time {
    margin-top: 2px;
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
  }

  &__del {
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    padding: 0;
    border: none;
    background: transparent;
    color: var(--color-ink-mute);
    cursor: pointer;
    border-radius: 50%;
    opacity: 0;
    transition: opacity var(--duration-fast) var(--ease-out),
      color var(--duration-fast) var(--ease-out),
      background-color var(--duration-fast) var(--ease-out);

    &:hover {
      color: var(--color-coral);
      background-color: var(--color-bg-card);
    }
  }

  &__item:hover &__del {
    opacity: 1;
  }
}
</style>
