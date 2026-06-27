<!--
  文件名: views/ResumeDetail.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 简历详情页
    - 顶部 el-page-header（返回 + 姓名）+ decor-line
    - 左 16 栏：PROFILE / 摘要 / 工作经历时间线 / 教育经历 / 技能 / 评价（失焦保存）
    - 右 8 栏：简历预览 / 标签管理（变更保存） / 操作区（相似/收藏/面试） / 面试评价历史
    - onMounted：getResumeDetail + getPreviewUrl
-->
<template>
  <div class="page-resume-detail">
    <LoadingOverlay :visible="loading" />

    <!-- 顶部页头 -->
    <el-page-header class="page-resume-detail__header" @back="handleBack">
      <template #content>
        <span class="page-resume-detail__header-name decor-line">
          {{ detail?.basic_info?.name || '简历详情' }}
        </span>
      </template>
    </el-page-header>

    <div v-if="detail" class="page-resume-detail__body">
      <el-row :gutter="20">
        <!-- 左栏 -->
        <el-col :span="16">
          <section class="detail-card">
            <span class="eyebrow">PROFILE</span>
            <h2 class="detail-card__name">{{ detail.basic_info?.name || '未命名' }}</h2>
            <p class="detail-card__meta">
              <span v-if="detail.basic_info?.gender">{{ detail.basic_info.gender }}</span>
              <span v-if="detail.basic_info?.age != null" class="detail-card__dot">·</span>
              <span v-if="detail.basic_info?.age != null">{{ detail.basic_info.age }}岁</span>
              <span v-if="detail.basic_info?.location" class="detail-card__dot">·</span>
              <span v-if="detail.basic_info?.location">{{ detail.basic_info.location }}</span>
              <template v-if="detail.work_years != null">
                <span class="detail-card__dot">·</span>
                <span>{{ detail.work_years }}年经验</span>
              </template>
            </p>
            <div class="detail-card__contact">
              <span class="detail-card__contact-item mono">
                {{ detail.basic_info?.phone || detail.basic_info?.phone_masked || '-' }}
              </span>
              <span
                v-if="detail.basic_info?.email || detail.basic_info?.email_masked"
                class="detail-card__contact-item mono"
              >
                {{ detail.basic_info?.email || detail.basic_info?.email_masked }}
              </span>
            </div>

            <!-- 摘要 -->
            <div v-if="detail.summary" class="detail-card__summary">
              <span class="detail-card__quote" aria-hidden="true">“</span>
              <p class="detail-card__summary-text">{{ detail.summary }}</p>
            </div>

            <!-- 工作经历 -->
            <div v-if="detail.work_experience?.length" class="detail-card__section">
              <h3 class="detail-card__section-title decor-line">工作经历</h3>
              <el-timeline class="detail-card__timeline">
                <el-timeline-item
                  v-for="(work, idx) in detail.work_experience"
                  :key="`work-${idx}`"
                  :timestamp="`${work.start_date} ~ ${work.end_date || '至今'}`"
                  placement="top"
                >
                  <div class="detail-card__work">
                    <div class="detail-card__work-head">
                      <span class="detail-card__work-company">{{ work.company }}</span>
                      <span class="detail-card__work-position">{{ work.position }}</span>
                    </div>
                    <p v-if="work.description" class="detail-card__work-desc">
                      {{ work.description }}
                    </p>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>

            <!-- 项目经历 -->
            <div v-if="detail.projects?.length" class="detail-card__section">
              <h3 class="detail-card__section-title decor-line">项目经历</h3>
              <el-timeline class="detail-card__timeline">
                <el-timeline-item
                  v-for="(proj, idx) in detail.projects"
                  :key="`proj-${idx}`"
                  placement="top"
                >
                  <div class="detail-card__work">
                    <div class="detail-card__work-head">
                      <span class="detail-card__work-company">{{ proj.name }}</span>
                      <span v-if="proj.role" class="detail-card__work-position">{{ proj.role }}</span>
                    </div>
                    <p v-if="proj.description" class="detail-card__work-desc">
                      {{ proj.description }}
                    </p>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>

            <!-- 教育经历 -->
            <div v-if="detail.education_detail?.length" class="detail-card__section">
              <h3 class="detail-card__section-title decor-line">教育经历</h3>
              <div class="detail-card__edu-list">
                <div
                  v-for="(edu, idx) in detail.education_detail"
                  :key="`edu-${idx}`"
                  class="detail-card__edu"
                >
                  <div class="detail-card__edu-head">
                    <span class="detail-card__edu-school">{{ edu.school }}</span>
                    <span class="detail-card__edu-date mono">
                      {{ edu.start_date }} ~ {{ edu.end_date }}
                    </span>
                  </div>
                  <div class="detail-card__edu-meta">
                    <span>{{ edu.major }}</span>
                    <span class="detail-card__dot">·</span>
                    <span>{{ edu.degree }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 技能 -->
            <div v-if="detail.skills?.length" class="detail-card__section">
              <h3 class="detail-card__section-title decor-line">技能标签</h3>
              <div class="detail-card__skills">
                <el-tag v-for="skill in detail.skills" :key="skill" size="small">
                  {{ skill }}
                </el-tag>
              </div>
            </div>

            <!-- 评价区 -->
            <div class="detail-card__section">
              <h3 class="detail-card__section-title decor-line">我的备注</h3>
              <el-input
                v-model="notes"
                type="textarea"
                :rows="4"
                placeholder="记录对该候选人的评价..."
                @blur="handleSaveNotes"
              />
            </div>
          </section>
        </el-col>

        <!-- 右栏 -->
        <el-col :span="8">
          <!-- 简历预览 -->
          <section class="detail-card detail-card--side">
            <h3 class="detail-card__section-title decor-line">简历预览</h3>
            <ResumePreview :preview-url="previewUrl" :file-type="previewFileType" />
          </section>

          <!-- 标签管理 -->
          <section class="detail-card detail-card--side">
            <h3 class="detail-card__section-title decor-line">标签管理</h3>
            <TagInput v-model="tags" @update:model-value="handleSaveTags" />
          </section>

          <!-- 操作区 -->
          <section class="detail-card detail-card--side">
            <h3 class="detail-card__section-title decor-line">操作</h3>
            <div class="detail-card__actions">
              <el-button @click="handleSimilar">
                <el-icon><Connection /></el-icon>
                相似推荐
              </el-button>
              <el-button :type="detail.is_favorite ? 'warning' : 'default'" @click="handleToggleFav">
                <el-icon><StarFilled v-if="detail.is_favorite" /><Star v-else /></el-icon>
                {{ detail.is_favorite ? '已收藏' : '收藏' }}
              </el-button>
              <el-button type="primary" @click="handleSendEmail">
                <el-icon><Promotion /></el-icon>
                发送邮件
              </el-button>
            </div>
          </section>

          <!-- 面试评价历史 -->
          <section v-if="detail.interview_notes?.length" class="detail-card detail-card--side">
            <h3 class="detail-card__section-title decor-line">面试评价历史</h3>
            <el-timeline>
              <el-timeline-item
                v-for="(note, idx) in detail.interview_notes"
                :key="note.note_id || idx"
                :timestamp="note.created_at"
                placement="top"
              >
                <div class="detail-card__note">
                  <div class="detail-card__note-head">
                    <span class="detail-card__note-interviewer">{{ note.interviewer }}</span>
                    <span class="detail-card__note-rating">评分 {{ note.rating }}</span>
                  </div>
                  <p class="detail-card__note-content">{{ note.content }}</p>
                </div>
              </el-timeline-item>
            </el-timeline>
          </section>
        </el-col>
      </el-row>
    </div>

    <EmptyState v-else-if="!loading" text="未找到简历信息" />

    <!-- 发送邮件对话框 -->
    <SendEmailDialog ref="sendEmailDialogRef" />
  </div>
</template>

<script setup lang="ts">
/**
 * ResumeDetail 简历详情
 * 加载详情与预览，支持备注/标签/收藏的更新
 */
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Connection, Star, StarFilled, Promotion } from '@element-plus/icons-vue'
import ResumePreview from '@/components/resume/ResumePreview.vue'
import TagInput from '@/components/candidate/TagInput.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import SendEmailDialog from '@/components/email/SendEmailDialog.vue'
import {
  getPreviewUrl,
  getResumeDetail,
  toggleFavorite,
  updateNotes,
  updateTags,
  type PreviewUrlResult,
} from '@/api/resume'
import type { ResumeDetail } from '@/types/resume'

const route = useRoute()
const router = useRouter()

const loading = ref<boolean>(false)
const detail = ref<ResumeDetail | null>(null)
const previewUrl = ref<string>('')
const previewFileType = ref<string>('')
const notes = ref<string>('')
const tags = ref<string[]>([])
const sendEmailDialogRef = ref<InstanceType<typeof SendEmailDialog>>()

/**
 * 加载简历详情
 */
async function loadDetail(): Promise<void> {
  const id = String(route.params.id || '')
  if (!id) return
  loading.value = true
  try {
    const data = await getResumeDetail(id)
    detail.value = data
    notes.value = data.notes || ''
    tags.value = [...(data.tags || [])]
    await loadPreview(id)
  } catch (err) {
    const msg = err instanceof Error ? err.message : '加载简历详情失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

/**
 * 加载预览地址
 * @param id 简历 ID
 */
async function loadPreview(id: string): Promise<void> {
  try {
    const res: PreviewUrlResult = await getPreviewUrl(id)
    previewUrl.value = res.preview_url || ''
    previewFileType.value = res.file_type || ''
  } catch (err) {
    // 预览失败不阻塞主流程
    const msg = err instanceof Error ? err.message : '加载预览失败'
    console.warn('[ResumeDetail] preview error:', msg)
  }
}

/**
 * 返回上一页
 */
function handleBack(): void {
  router?.push('/resumes')
}

/**
 * 保存备注（失焦触发）
 */
async function handleSaveNotes(): Promise<void> {
  if (!detail.value) return
  try {
    await updateNotes(detail.value.resume_id, notes.value)
    ElMessage.success('备注已保存')
  } catch (err) {
    const msg = err instanceof Error ? err.message : '保存备注失败'
    ElMessage.error(msg)
  }
}

/**
 * 保存标签（变更触发）
 */
async function handleSaveTags(): Promise<void> {
  if (!detail.value) return
  try {
    await updateTags(detail.value.resume_id, tags.value)
    ElMessage.success('标签已保存')
  } catch (err) {
    const msg = err instanceof Error ? err.message : '保存标签失败'
    ElMessage.error(msg)
  }
}

/**
 * 切换收藏
 */
async function handleToggleFav(): Promise<void> {
  if (!detail.value) return
  const next = !detail.value.is_favorite
  try {
    await toggleFavorite(detail.value.resume_id, next)
    detail.value.is_favorite = next
  } catch (err) {
    const msg = err instanceof Error ? err.message : '收藏切换失败'
    ElMessage.error(msg)
  }
}

/**
 * 跳转相似推荐（这里复用 JD 匹配或对比，简单跳回列表）
 */
function handleSimilar(): void {
  ElMessage.info('相似推荐功能开发中')
}

/**
 * 打开发送邮件对话框
 * 预填收件人邮箱和候选人姓名作为模板变量
 */
function handleSendEmail(): void {
  if (!detail.value) return
  sendEmailDialogRef.value?.open({
    to_email: detail.value.basic_info?.email || detail.value.basic_info?.email_masked || '',
    variables: {
      candidate_name: detail.value.basic_info?.name ?? detail.value.name ?? '',
      position: '',
      company: 'TalentSense',
      salary: `${detail.value.expected_salary?.min ?? ''}-${detail.value.expected_salary?.max ?? ''}K`,
      interview_time: '',
    },
  })
}

onMounted(() => {
  void loadDetail()
})
</script>

<style scoped lang="scss">
.page-resume-detail {
  position: relative;
  min-height: 100%;

  &__header {
    margin-bottom: var(--space-5);

    :deep(.el-page-header__content) {
      font-family: var(--font-display);
      font-size: var(--text-xl);
      font-weight: 500;
      color: var(--color-primary);
    }
  }

  &__header-name {
    display: inline-block;
    padding-bottom: 6px;
  }

  &__body {
    animation: fadeInUp var(--duration-slow) var(--ease-out) both;
  }
}

/* ============ 卡片 ============ */
.detail-card {
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: var(--space-6);
  margin-bottom: var(--space-5);

  &--side {
    padding: var(--space-5);
  }

  &__name {
    margin-top: var(--space-3);
    font-family: var(--font-display);
    font-size: 28px;
    font-weight: 500;
    color: var(--color-primary);
    letter-spacing: -0.01em;
  }

  &__meta {
    margin-top: var(--space-2);
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
    display: flex;
    align-items: center;
    flex-wrap: wrap;
  }

  &__dot {
    margin: 0 6px;
    color: var(--color-ink-mute);
  }

  &__contact {
    margin-top: var(--space-3);
    display: flex;
    gap: var(--space-4);
    flex-wrap: wrap;
  }

  &__contact-item {
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
  }

  &__summary {
    position: relative;
    margin-top: var(--space-5);
    padding: var(--space-4) var(--space-5);
    background-color: var(--color-bg-overlay);
    border-left: 3px solid var(--color-accent);
    border-radius: var(--radius-md);
  }

  &__quote {
    position: absolute;
    top: 0;
    left: var(--space-3);
    font-family: var(--font-display);
    font-size: 36px;
    color: var(--color-accent);
    line-height: 1;
  }

  &__summary-text {
    font-family: var(--font-display);
    font-style: italic;
    font-size: var(--text-md);
    color: var(--color-ink-soft);
    line-height: 1.7;
    margin: 0;
    padding-left: var(--space-5);
  }

  &__section {
    margin-top: var(--space-6);
  }

  &__section-title {
    font-family: var(--font-display);
    font-size: var(--text-lg);
    font-weight: 500;
    color: var(--color-primary);
    margin: 0 0 var(--space-4) 0;
    padding-bottom: 6px;
  }

  &__timeline {
    padding-left: var(--space-2);
  }

  &__work {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__work-head {
    display: flex;
    align-items: baseline;
    gap: var(--space-3);
    flex-wrap: wrap;
  }

  &__work-company {
    font-family: var(--font-display);
    font-weight: 500;
    font-size: var(--text-md);
    color: var(--color-primary);
  }

  &__work-position {
    font-size: var(--text-sm);
    color: var(--color-accent-deep);
  }

  &__work-desc {
    margin: 0;
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
    line-height: 1.6;
  }

  &__edu-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  &__edu {
    padding: var(--space-3) var(--space-4);
    background-color: var(--color-bg-overlay);
    border-radius: var(--radius-md);
  }

  &__edu-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--space-3);
  }

  &__edu-school {
    font-family: var(--font-display);
    font-weight: 500;
    color: var(--color-primary);
  }

  &__edu-date {
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
  }

  &__edu-meta {
    margin-top: 4px;
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
  }

  &__skills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  &__actions {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  &__note {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__note-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__note-interviewer {
    font-family: var(--font-display);
    font-weight: 500;
    color: var(--color-primary);
  }

  &__note-rating {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    color: var(--color-accent-deep);
  }

  &__note-content {
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
    line-height: 1.6;
    margin: 0;
  }
}
</style>
