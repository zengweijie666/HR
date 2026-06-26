<!--
  文件名: views/JdMatch.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: JD 匹配页
    - 顶部页头：eyebrow + 大标题 + 副文案
    - 上半区：JD 输入卡片（textarea + 字符计数 + Top K + 开始匹配按钮）
    - 下半区：匹配结果（无结果 EmptyState / 有结果 JD 信息卡片 + 候选人卡片网格）
    - 匹配逻辑：调 matchJd(jdText, topK) API
-->
<template>
  <div class="page-jd-match">
    <!-- 页头 -->
    <header class="page-jd-match__head">
      <span class="eyebrow">JD INTELLIGENCE</span>
      <h1 class="page-jd-match__title decor-line">JD 匹配</h1>
      <p class="page-jd-match__subtitle">
        粘贴招聘需求，AI 自动解析并推荐最匹配的候选人
      </p>
    </header>

    <!-- JD 输入卡片 -->
    <section class="jd-input">
      <div class="jd-input__head">
        <h3 class="jd-input__title">招聘需求</h3>
        <span class="jd-input__count mono">{{ jdText.length }} 字</span>
      </div>

      <el-input
        v-model="jdText"
        type="textarea"
        :rows="8"
        resize="none"
        placeholder="粘贴招聘需求（JD）..."
        class="jd-input__textarea"
      />

      <div class="jd-input__footer">
        <div class="jd-input__topk">
          <span class="jd-input__topk-label">Top K</span>
          <el-input-number v-model="topK" :min="1" :max="50" size="small" />
        </div>
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!jdText.trim()"
          class="jd-input__submit"
          @click="handleMatch"
        >
          <el-icon><Search /></el-icon>
          开始匹配
        </el-button>
      </div>
    </section>

    <!-- 匹配结果 -->
    <section class="jd-result">
      <LoadingOverlay :visible="loading" />

      <EmptyState v-if="!result" text="粘贴 JD 后开始匹配" />

      <div v-else class="jd-result__body">
        <!-- JD 信息卡片 -->
        <div class="jd-info">
          <span class="eyebrow">PARSED JD</span>
          <h3 class="jd-info__title decor-line">{{ result.jd.title || '未命名岗位' }}</h3>
          <div class="jd-info__meta">
            <span v-if="result.jd.work_years_min" class="jd-info__meta-item">
              <span class="jd-info__meta-label">最低经验</span>
              <span class="jd-info__meta-value mono">{{ result.jd.work_years_min }}年</span>
            </span>
            <span v-if="result.jd.salary_max" class="jd-info__meta-item">
              <span class="jd-info__meta-label">最高薪资</span>
              <span class="jd-info__meta-value mono">≤{{ result.jd.salary_max }}K</span>
            </span>
          </div>
          <div v-if="result.jd.skills?.length" class="jd-info__skills">
            <el-tag v-for="skill in result.jd.skills" :key="skill" size="small">
              {{ skill }}
            </el-tag>
          </div>
        </div>

        <!-- 候选人列表 -->
        <div v-if="result.candidates?.length" class="jd-result__candidates">
          <h4 class="jd-result__sub-title">推荐候选人 · {{ result.candidates.length }} 位</h4>
          <el-row :gutter="16">
            <el-col
              v-for="c in result.candidates"
              :key="c.candidate_id"
              :span="8"
              class="jd-result__col"
            >
              <CandidateCard :candidate="c" @select="handleSelectCandidate" />
            </el-col>
          </el-row>
        </div>

        <EmptyState v-else text="未匹配到合适的候选人" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
/**
 * JdMatch JD 匹配页
 * 输入 JD 文本，调用 matchJd 接口，展示解析结果与候选人
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import CandidateCard from '@/components/candidate/CandidateCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import { useRouter } from 'vue-router'
import { matchJd } from '@/api/jd'
import type { JdMatchResult } from '@/types/jd'
import type { CandidateCard as CandidateCardType } from '@/types/candidate'

const router = useRouter()

const jdText = ref<string>('')
const topK = ref<number>(10)
const loading = ref<boolean>(false)
const result = ref<JdMatchResult | null>(null)

/**
 * 触发 JD 匹配
 */
async function handleMatch(): Promise<void> {
  const text = jdText.value.trim()
  if (!text) {
    ElMessage.warning('请先粘贴招聘需求')
    return
  }
  loading.value = true
  try {
    const data = await matchJd(text, topK.value)
    result.value = data
    if (!data.candidates?.length) {
      ElMessage.info('未匹配到合适的候选人')
    } else {
      ElMessage.success(`已推荐 ${data.candidates.length} 位候选人`)
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : '匹配失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

/**
 * 点击候选人卡片跳转详情
 * @param candidate 候选人对象
 */
function handleSelectCandidate(candidate: CandidateCardType): void {
  if (candidate.resume_id) {
    router?.push(`/resumes/${candidate.resume_id}`)
  }
}
</script>

<style scoped lang="scss">
.page-jd-match {
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
    max-width: 640px;
  }
}

/* ============ JD 输入卡片 ============ */
.jd-input {
  position: relative;
  padding: var(--space-5) var(--space-6);
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--space-3);
  }

  &__title {
    font-family: var(--font-display);
    font-size: var(--text-lg);
    font-weight: 500;
    color: var(--color-primary);
    margin: 0;
    padding-bottom: 6px;
  }

  &__count {
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
    letter-spacing: 0.04em;
  }

  &__textarea {
    :deep(.el-textarea__inner) {
      font-family: var(--font-body);
      font-size: var(--text-base);
      line-height: 1.7;
    }
  }

  &__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: var(--space-4);
    gap: var(--space-4);

    @media (max-width: 768px) {
      flex-direction: column;
      align-items: stretch;
    }
  }

  &__topk {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  &__topk-label {
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
    letter-spacing: 0.04em;
  }

  &__submit {
    min-width: 140px;
  }
}

/* ============ 匹配结果 ============ */
.jd-result {
  position: relative;
  min-height: 240px;

  &__body {
    display: flex;
    flex-direction: column;
    gap: var(--space-5);
  }

  &__sub-title {
    font-family: var(--font-display);
    font-size: var(--text-md);
    font-weight: 500;
    color: var(--color-primary);
    margin: 0 0 var(--space-4) 0;
  }

  &__col {
    margin-bottom: var(--space-4);
  }
}

/* ============ JD 信息卡片 ============ */
.jd-info {
  padding: var(--space-5) var(--space-6);
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);

  &__title {
    margin-top: var(--space-3);
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-weight: 500;
    color: var(--color-primary);
    padding-bottom: 6px;
  }

  &__meta {
    display: flex;
    gap: var(--space-6);
    margin-top: var(--space-4);
    flex-wrap: wrap;
  }

  &__meta-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  &__meta-label {
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
    letter-spacing: 0.04em;
  }

  &__meta-value {
    font-size: var(--text-md);
    color: var(--color-accent-deep);
    font-weight: 600;
  }

  &__skills {
    margin-top: var(--space-4);
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
}
</style>
