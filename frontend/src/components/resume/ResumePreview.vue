<!--
  文件名: components/resume/ResumePreview.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 简历文件预览
    - PDF 用 iframe，图片用 img
    - 外层细微边框 + 阴影
-->
<template>
  <div class="resume-preview">
    <iframe
      v-if="isPdf"
      :src="previewUrl"
      class="resume-preview__frame"
      :title="title"
    />
    <img
      v-else-if="isImage"
      :src="previewUrl"
      :alt="title"
      class="resume-preview__image"
    />
    <div v-else class="resume-preview__unsupported">
      <el-icon class="resume-preview__unsupported-icon"><Document /></el-icon>
      <span>暂不支持预览该文件类型</span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ResumePreview 简历预览组件
 * 根据 fileType 选择 iframe（PDF）或 img（图片）渲染
 */
import { computed } from 'vue'
import { Document } from '@element-plus/icons-vue'

interface ResumePreviewProps {
  /** 预览文件地址 */
  previewUrl?: string
  /** 文件类型，如 'pdf' | 'png' | 'jpg' */
  fileType?: string
}

const props = defineProps<ResumePreviewProps>()

/** 是否 PDF */
const isPdf = computed(() => {
  const t = (props.fileType || '').toLowerCase()
  return !!props.previewUrl && t === 'pdf'
})

/** 是否图片 */
const isImage = computed(() => {
  const t = (props.fileType || '').toLowerCase()
  return !!props.previewUrl && ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(t)
})

/** 预览标题 */
const title = computed(() => `简历预览 · ${props.fileType || '文件'}`)
</script>

<style scoped lang="scss">
.resume-preview {
  width: 100%;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  background-color: var(--color-bg-card);

  &__frame {
    display: block;
    width: 100%;
    min-height: 520px;
    border: none;
  }

  &__image {
    display: block;
    width: 100%;
    height: auto;
    max-height: 720px;
    object-fit: contain;
  }

  &__unsupported {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--space-3);
    min-height: 320px;
    color: var(--color-ink-mute);
    font-family: var(--font-display);
    font-size: var(--text-sm);
  }

  &__unsupported-icon {
    font-size: 36px;
    color: var(--color-primary-soft);
  }
}
</style>
