<!--
  文件名: components/resume/UploadDialog.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 简历上传对话框
    - el-dialog + eyebrow 装饰小标签 "RESUME UPLOAD"
    - 拖拽上传区（自定义琥珀色虚线边框）
    - 覆盖重复简历 checkbox
    - 取消 + 上传（带 loading）按钮
-->
<template>
  <el-dialog
    :model-value="visible"
    title="上传简历"
    width="520px"
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
      :auto-upload="false"
      :limit="1"
      :on-change="handleFileChange"
      :on-exceed="handleExceed"
      :file-list="fileList"
      accept=".pdf,.docx,.png,.jpg,.jpeg"
    >
      <el-icon class="upload-dialog__icon"><UploadFilled /></el-icon>
      <div class="upload-dialog__hint-title">将文件拖到此处，或点击上传</div>
      <div class="upload-dialog__hint-sub">支持 PDF / DOCX / PNG / JPG</div>
    </el-upload>

    <div class="upload-dialog__options">
      <el-checkbox v-model="overwrite">覆盖重复简历</el-checkbox>
    </div>

    <template #footer>
      <el-button text @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="handleUpload">
        上传
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * UploadDialog 简历上传对话框
 * 选择文件后调用 uploadResume 上传，成功后 emit uploaded / close
 */
import { ref, watch } from 'vue'
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
  /** 上传成功 */
  (e: 'uploaded', data: UploadResponse): void
}>()

const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadFiles>([])
const selectedFile = ref<File | null>(null)
const overwrite = ref<boolean>(false)
const uploading = ref<boolean>(false)

/** 对话框关闭时重置内部状态 */
watch(
  () => props.visible,
  (val) => {
    if (!val) {
      selectedFile.value = null
      fileList.value = []
      overwrite.value = false
      uploading.value = false
    }
  },
)

/** 处理文件选择变化 */
function handleFileChange(file: UploadFile): void {
  if (file && file.raw) {
    selectedFile.value = file.raw
    fileList.value = [file]
  }
}

/** 超出文件数量限制提示 */
function handleExceed(): void {
  ElMessage.warning('每次只能上传一个文件，请先移除已选文件')
}

/** 处理上传 */
async function handleUpload(): Promise<void> {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择简历文件')
    return
  }
  uploading.value = true
  try {
    const data = await uploadResume(selectedFile.value, overwrite.value)
    ElMessage.success('上传成功')
    emit('uploaded', data)
    emit('close')
  } catch (err) {
    const msg = err instanceof Error ? err.message : '上传失败'
    ElMessage.error(msg)
  } finally {
    uploading.value = false
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

  &__options {
    margin-top: var(--space-4);
  }
}
</style>
