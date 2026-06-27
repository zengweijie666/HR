<!--
  文件名: views/ResumeList.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 简历库列表页
    - 顶部：eyebrow + 大标题 + 副文案
    - 工具栏：FilterBar + 操作按钮（上传/导出选中）
    - 列表：3 列栅格 ResumeCard，支持多选与收藏
    - 分页：底部居中
    - 上传：UploadDialog，uploaded 事件重新加载列表
-->
<template>
  <div class="page-resume-list">
    <!-- 页头 -->
    <header class="page-resume-list__head">
      <span class="eyebrow">RESUME LIBRARY</span>
      <h1 class="page-resume-list__title decor-line">简历库</h1>
      <p class="page-resume-list__subtitle">
        管理所有候选人简历，支持上传、检索、标签与收藏
      </p>
    </header>

    <!-- 工具栏 -->
    <div class="page-resume-list__toolbar">
      <FilterBar class="page-resume-list__filter" @search="handleSearch" @reset="handleReset" />
      <div class="page-resume-list__actions">
        <div class="page-resume-list__stats">
          共 <strong>{{ resumeStore.total }}</strong> 份简历
        </div>
        <el-button type="primary" class="upload-btn" @click="uploadVisible = true">
          <el-icon><Upload /></el-icon>
          上传简历
        </el-button>
        <el-button :disabled="!selectedIds.length" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出选中
        </el-button>
      </div>
    </div>

    <!-- 列表区 -->
    <div class="page-resume-list__body">
      <LoadingOverlay :visible="loading" />

      <el-row v-if="resumeStore.list.length" :gutter="16">
        <el-col
          v-for="resume in resumeStore.list"
          :key="resume.resume_id"
          :span="8"
          class="page-resume-list__col"
        >
          <div class="page-resume-list__card-wrap">
            <el-checkbox
              v-model="selectedMap[resume.resume_id]"
              class="page-resume-list__check"
              @change="handleSelectionChange"
            />
            <ResumeCard
              :resume="resume"
              @click="handleClickResume"
              @toggle-favorite="handleToggleFavorite"
              @delete="handleDeleteResume"
              @send-email="handleSendEmail"
            />
          </div>
        </el-col>
      </el-row>

      <EmptyState v-else-if="!loading" text="暂无简历，点击上传" />
    </div>

    <!-- 分页 -->
    <div v-if="resumeStore.total > 0" class="page-resume-list__pagination">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next"
        :total="resumeStore.total"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :current-page="page"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- 上传对话框 -->
    <UploadDialog
      v-model:visible="uploadVisible"
      @uploaded="handleUploaded"
      @close="uploadVisible = false"
    />

    <!-- 发送邮件对话框 -->
    <SendEmailDialog ref="sendEmailDialogRef" />
  </div>
</template>

<script setup lang="ts">
/**
 * ResumeList 简历库列表
 * 整合筛选/分页/上传/收藏/导出
 */
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Download } from '@element-plus/icons-vue'
import FilterBar, { type ResumeFilters } from '@/components/resume/FilterBar.vue'
import ResumeCard from '@/components/resume/ResumeCard.vue'
import UploadDialog from '@/components/resume/UploadDialog.vue'
import SendEmailDialog from '@/components/email/SendEmailDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import { useResumeStore } from '@/stores/resume'
import { getResumeList, toggleFavorite, deleteResume } from '@/api/resume'
import { exportExcel } from '@/api/candidate'
import { downloadBlob, defaultFilename } from '@/utils/download'
import type { ResumeListQuery } from '@/types/resume'

const resumeStore = useResumeStore()
const router = useRouter()

const loading = ref<boolean>(false)
const uploadVisible = ref<boolean>(false)
const page = ref<number>(1)
const pageSize = ref<number>(20)
const sendEmailDialogRef = ref<InstanceType<typeof SendEmailDialog>>()

/** 多选状态：resume_id → 是否选中 */
const selectedMap = reactive<Record<string, boolean>>({})
/** 选中 ID 列表 */
const selectedIds = ref<string[]>([])

/**
 * 加载简历列表
 */
async function loadList(): Promise<void> {
  loading.value = true
  try {
    const query: ResumeListQuery = {
      page: page.value,
      page_size: pageSize.value,
      ...resumeStore.filters,
    }
    const res = await getResumeList(query)
    resumeStore.setList(res.list || [])
    resumeStore.setTotal(res.total || 0)
  } catch (err) {
    const msg = err instanceof Error ? err.message : '加载简历列表失败'
    ElMessage.error(msg)
    resumeStore.setList([])
  } finally {
    loading.value = false
  }
}

/**
 * 处理筛选
 * @param filters 筛选条件
 */
function handleSearch(filters: ResumeFilters): void {
  resumeStore.setFilters(filters as Partial<ResumeListQuery>)
  page.value = 1
  void loadList()
}

/**
 * 处理重置：完全清空筛选条件并刷新列表
 */
function handleReset(): void {
  resumeStore.replaceFilters({})
  page.value = 1
  void loadList()
}

/**
 * 处理分页变化
 * @param p 目标页码
 */
function handlePageChange(p: number): void {
  page.value = p
  void loadList()
}

/**
 * 处理分页大小变化
 * @param size 新的每页条数
 */
function handleSizeChange(size: number): void {
  pageSize.value = size
  page.value = 1
  void loadList()
}

/**
 * 处理点击简历卡片
 * @param resumeId 简历 ID
 */
function handleClickResume(resumeId: string): void {
  router?.push(`/resumes/${resumeId}`)
}

/**
 * 处理收藏切换
 * @param resumeId 简历 ID
 */
async function handleToggleFavorite(resumeId: string): Promise<void> {
  const item = resumeStore.list.find((r) => r.resume_id === resumeId)
  if (!item) return
  const next = !item.is_favorite
  try {
    await toggleFavorite(resumeId, next)
    resumeStore.updateFavorite(resumeId, next)
  } catch (err) {
    const msg = err instanceof Error ? err.message : '收藏切换失败'
    ElMessage.error(msg)
  }
}

/**
 * 处理删除简历（硬删除，弹确认框）
 * @param resumeId 简历 ID
 */
async function handleDeleteResume(resumeId: string): Promise<void> {
  const item = resumeStore.list.find((r) => r.resume_id === resumeId)
  const name = item?.name || '该简历'
  try {
    await ElMessageBox.confirm(
      `确定要删除「${name}」吗？此操作不可恢复，将同时删除文件、解析数据和向量索引。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return // 用户取消
  }
  try {
    await deleteResume(resumeId)
    ElMessage.success('删除成功')
    // 清理选中状态
    delete selectedMap[resumeId]
    handleSelectionChange()
    // 如果当前页删完，回退到上一页
    if (resumeStore.list.length === 1 && page.value > 1) {
      page.value--
    }
    await loadList()
  } catch (err) {
    const msg = err instanceof Error ? err.message : '删除失败'
    ElMessage.error(msg)
  }
}

/**
 * 处理多选变化
 */
function handleSelectionChange(): void {
  selectedIds.value = Object.keys(selectedMap).filter((k) => selectedMap[k])
}

/**
 * 处理发送邮件（从卡片触发）
 * 预填收件人邮箱和候选人姓名作为模板变量
 * @param resumeId 简历 ID
 */
function handleSendEmail(resumeId: string): void {
  const item = resumeStore.list.find((r) => r.resume_id === resumeId)
  sendEmailDialogRef.value?.open({
    to_email: item?.email || item?.email_masked || '',
    variables: {
      candidate_name: item?.name ?? '',
    },
  })
}

/**
 * 处理导出选中
 */
async function handleExport(): Promise<void> {
  if (!selectedIds.value.length) {
    ElMessage.warning('请先选择要导出的简历')
    return
  }
  try {
    const blob = await exportExcel({
      candidate_ids: selectedIds.value,
      columns: ['name', 'gender', 'age', 'education', 'work_years', 'skills', 'expected_salary', 'tags'],
    })
    downloadBlob(blob, defaultFilename('resumes', 'xlsx'))
    ElMessage.success('导出成功')
  } catch (err) {
    const msg = err instanceof Error ? err.message : '导出失败'
    ElMessage.error(msg)
  }
}

/**
 * 处理上传成功：刷新列表并启动轮询
 */
function handleUploaded(): void {
  page.value = 1
  void loadList().then(() => {
    startPolling()
  })
}

onMounted(() => {
  void loadList().then(() => {
    const hasParsing = resumeStore.list.some((r) => r.parse_status === 'parsing')
    if (hasParsing) {
      startPolling()
    }
  })
})

/**
 * 轮询刷新：上传后后台异步解析时，每 3 秒刷新一次列表，
 * 直到没有 parsing 状态的简历为止。
 * 使用静默刷新（不显示 loading 遮罩）避免闪烁。
 */
const POLL_INTERVAL_MS = 3000
const MAX_POLL_TIMES = 40
let pollTimer: ReturnType<typeof setTimeout> | null = null
let pollCount = 0

function startPolling(): void {
  stopPolling()
  pollCount = 0
  pollTimer = setTimeout(pollTick, POLL_INTERVAL_MS)
}

function stopPolling(): void {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

async function pollTick(): Promise<void> {
  pollCount++
  try {
    // 静默刷新，不触发 loading 遮罩
    const query: ResumeListQuery = {
      page: page.value,
      page_size: pageSize.value,
      ...resumeStore.filters,
    }
    const res = await getResumeList(query)
    resumeStore.setList(res.list || [])
    resumeStore.setTotal(res.total || 0)
    // 仍有 parsing 状态的简历且未超过最大轮询次数 → 继续轮询
    const hasParsing = (res.list || []).some(
      (r: { parse_status?: string }) => r.parse_status === 'parsing',
    )
    if (hasParsing && pollCount < MAX_POLL_TIMES) {
      pollTimer = setTimeout(pollTick, POLL_INTERVAL_MS)
    } else {
      pollTimer = null
    }
  } catch {
    // 轮询失败不提示，停止轮询
    pollTimer = null
  }
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="scss">
.page-resume-list {
  position: relative;
  min-height: 100%;

  &__head {
    margin-bottom: var(--space-6);
    animation: fadeInUp var(--duration-slow) var(--ease-out) both;
  }

  &__title {
    margin-top: var(--space-3);
    font-family: var(--font-display);
    font-size: 32px;
    font-weight: 500;
    color: var(--color-primary);
    padding-bottom: 10px;
    letter-spacing: -0.02em;
  }

  &__subtitle {
    margin-top: var(--space-3);
    font-size: var(--text-md);
    color: var(--color-ink-soft);
    max-width: 600px;
  }

  &__toolbar {
    display: flex;
    align-items: stretch;
    gap: var(--space-4);
    margin-bottom: var(--space-5);

    @media (max-width: 1100px) {
      flex-direction: column;
    }
  }

  &__filter {
    flex: 1;
    min-width: 0;
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    flex-shrink: 0;

    .el-button {
      height: 100%;
    }
  }

  &__stats {
    display: flex;
    align-items: center;
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
    margin-right: var(--space-2);

    strong {
      color: var(--color-primary);
      font-weight: 600;
      margin: 0 4px;
    }
  }

  &__body {
    position: relative;
    min-height: 320px;
  }

  &__col {
    margin-bottom: var(--space-4);
  }

  &__card-wrap {
    position: relative;
  }

  &__check {
    position: absolute;
    top: 10px;
    left: 10px;
    z-index: 2;
    background: var(--color-bg-card);
    padding: 2px 6px;
    border-radius: var(--radius-sm);
    box-shadow: var(--shadow-xs);
  }

  &__pagination {
    display: flex;
    justify-content: center;
    margin-top: var(--space-6);
    padding-top: var(--space-4);
    border-top: 1px solid var(--color-line-soft);
  }
}
</style>
