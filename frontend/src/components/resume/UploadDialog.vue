<!--
  文件名: components/resume/UploadDialog.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 简历上传对话框（支持批量）
    - el-dialog + 拖拽上传区（支持多文件）
    - 覆盖重复简历 checkbox
    - 文件列表展示 + 逐个上传 + 进度反馈
-->
<template>
  <el-dialog
    :model-value="visible"
    title="上传简历"
    width="560px"
    :close-on-click-modal="false"
    append-to-body
    class="upload-dialog"
    @update:model-value="handleVisibleChange"
    @close="handleClose"
  >
    <div class="upload-dialog__eyebrow eyebrow">RESUME UPLOAD</div>

    <el-upload
      ref="uploadRef"
      class="upload-dialog__uploader"
      drag
      multiple
      :auto-upload="false"
      :on-change="handleFileChange"
      :on-remove="handleFileRemove"
      :file-list="fileList"
      accept=".pdf,.docx,.png,.jpg,.jpeg"
    >
      <el-icon class="upload-dialog__icon"><UploadFilled /></el-icon>
      <div class="upload-dialog__hint-title">将文件拖到此处，或点击上传</div>
      <div class="upload-dialog__hint-sub">支持 PDF / DOCX / PNG / JPG，可批量选择多个文件</div>
    </el-upload>

    <div v-if="fileList.length > 0" class="upload-dialog__count">
      已选择 {{ fileList.length }} 个文件
    </div>

    <div class="upload-dialog__options">
      <el-checkbox v-model="overwrite">覆盖重复简历</el-checkbox>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-dialog__progress">
      <el-progress :percentage="uploadProgress" :format="() => `${uploadedCount}/${fileList.length}`" />
    </div>

    <template #footer>
      <el-button text @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="uploading" :disabled="!fileList.length" @click="handleUpload">
        上传（{{ fileList.length }} ）
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * UploadDialog 简历上传对话框（批量）
 * 选择多个文件后逐个调用 uploadResume 上传，全部完成后 emit uploaded
 */
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadFiles, UploadInstance } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadResume } from '@/api/resume'
import type { UploadResponse } from '@/types/resume'

interface UploadDialogProps {
  /** 对话框可见性 */
  visible: boolean
}

const props = defineProps<UploadDialogProps>()

const emit = defineEmits<{
  /** 关闭对话框 */
  (e: 'close'): void
  /** 上传成功（批量） */
  (e: 'uploaded', data: UploadResponse[]): void
}>()

const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadFiles>([])
const overwrite = ref<boolean>(false)
const uploading = ref<boolean>(false)
const uploadedCount = ref<number>(0)

const uploadProgress = computed(() => {
  if (!fileList.value.length) return 0
  return Math.round((uploadedCount.value / fileList.value.length) * 100)
})

/** 对话框关闭时重置内部状态 */
watch(
  () => props.visible,
  (val) => {
    if (!val) {
      fileList.value = []
      overwrite.value = false
      uploading.value = false
      uploadedCount.value = 0
    }
  },
)

/** 处理文件选择变化 */
function handleFileChange(file: UploadFile): void {
  if (file && file.raw) {
    const exists = fileList.value.some(f => f.uid === file.uid)
    if (!exists) {
      fileList.value.push(file)
    }
  }
}

/** 处理文件移除 */
function handleFileRemove(file: UploadFile): void {
  fileList.value = fileList.value.filter(f => f.uid !== file.uid)
}

/** 批量上传：逐个上传 */
async function handleUpload(): Promise<void> {
  if (!fileList.value.length) {
    ElMessage.warning('请先选择简历文件')
    return
  }
  uploading.value = true
  uploadedCount.value = 0
  const results: UploadResponse[] = []
  const errors: string[] = []

  for (const file of fileList.value) {
    if (!file.raw) continue
    try {
      const data = await uploadResume(file.raw, overwrite.value)
      results.push(data)
    } catch (err) {
      const msg = err instanceof Error ? err.message : `${file.name} 上传失败`
      errors.push(msg)
    }
    uploadedCount.value++
  }

  uploading.value = false

  if (results.length > 0) {
    ElMessage.success(`成功上传 ${results.length} 份简历，正在后台解析，列表将自动刷新`)
    emit('uploaded', results)
    emit('close')
  }
  if (errors.length > 0) {
    ElMessage.warning(`${errors.length} 份上传失败：${errors[0]}`)
  }
}

/** 取消 */
function handleCancel(): void {
  emit('close')
}

/** 关闭 */
function handleClose(): void {
  emit('close')
}

/** visible 变化同步 */
function handleVisibleChange(val: boolean): void {
  if (!val) {
    emit('close')
  }
}
</script>

<style scoped lang="scss">
.upload-dialog {
  &__eyebrow {
    margin-bottom: var(--space-4);
  }

  &__uploader {
    :deep(.el-upload-dragger) {
      width: 100%;
      padding: var(--space-8) var(--space-6);
      background-color: var(--color-bg-overlay);
      border: 1.5px dashed var(--color-accent-soft);
      border-radius: var(--radius-lg);
      transition: border-color var(--duration-fast) var(--ease-out),
        background-color var(--duration-fast) var(--ease-out);

      &:hover {
        border-color: var(--color-accent);
        background-color: var(--color-primary-tint);
      }
    }
  }

  &__icon {
    font-size: 40px;
    color: var(--color-primary);
    margin-bottom: var(--space-3);
  }

  &__hint-title {
    font-family: var(--font-display);
    font-size: var(--text-md);
    color: var(--color-ink);
  }

  &__hint-sub {
    margin-top: 4px;
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
    letter-spacing: 0.02em;
  }

  &__count {
    margin-top: var(--space-3);
    font-size: var(--text-sm);
    color: var(--color-accent-deep);
    font-weight: 500;
  }

  &__options {
    margin-top: var(--space-4);
  }

  &__progress {
    margin-top: var(--space-3);
  }
}
</style>
