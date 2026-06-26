<!--
  文件名: components/candidate/TagInput.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 标签输入组件
    - 现有标签列表（closable）+ 输入框
    - 回车添加，失焦也添加
    - 标签用 --color-primary-tint 背景
-->
<template>
  <div class="tag-input">
    <el-tag
      v-for="(tag, idx) in modelValue"
      :key="`${tag}-${idx}`"
      class="tag-input__tag"
      closable
      @close="removeTag(idx)"
    >
      {{ tag }}
    </el-tag>
    <el-input
      v-model="inputValue"
      class="tag-input__input"
      :placeholder="modelValue.length ? '' : '输入标签后回车'"
      size="small"
      @keyup.enter="addTag"
      @blur="addTag"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * TagInput 标签输入组件
 * 通过 v-model 双向绑定字符串数组
 */
import { ref } from 'vue'

interface TagInputProps {
  /** 标签数组（v-model） */
  modelValue: string[]
}

const props = defineProps<TagInputProps>()

const emit = defineEmits<{
  /** 更新 v-model */
  (e: 'update:modelValue', value: string[]): void
}>()

const inputValue = ref<string>('')

/** 添加标签 */
function addTag(): void {
  const val = inputValue.value.trim()
  if (!val) return
  if (props.modelValue.includes(val)) {
    inputValue.value = ''
    return
  }
  emit('update:modelValue', [...props.modelValue, val])
  inputValue.value = ''
}

/** 删除标签 */
function removeTag(idx: number): void {
  const next = [...props.modelValue]
  next.splice(idx, 1)
  emit('update:modelValue', next)
}
</script>

<style scoped lang="scss">
.tag-input {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background-color: var(--color-bg-card);
  min-height: 36px;

  &:focus-within {
    border-color: var(--color-accent);
  }

  &__tag {
    background-color: var(--color-primary-tint);
    border-color: transparent;
    color: var(--color-primary);
  }

  &__input {
    flex: 1;
    min-width: 120px;

    :deep(.el-input__wrapper) {
      box-shadow: none !important;
      background: transparent;
      padding: 0;
    }
  }
}
</style>
