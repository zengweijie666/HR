<!--
  文件名: components/candidate/CandidateCard.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 候选人卡片
    - 顶部：姓名（衬线）+ 评分（大数字 scoreLevel 颜色）+ 五角星（score/20）
    - 中部：工作年限·学历·薪资（mono）meta
    - 技能标签
    - 匹配理由（斜体衬线 + 琥珀引号装饰）
    - hover 上浮 + 阴影加深，整卡可点击
-->
<template>
  <article
    class="candidate-card"
    tabindex="0"
    @click="handleSelect"
    @keyup.enter="handleSelect"
  >
    <!-- 顶部：姓名 + 评分 -->
    <header class="candidate-card__head">
      <h3 class="candidate-card__name">{{ candidate.name || '候选人' }}</h3>
      <div class="candidate-card__score" :style="{ color: level.color }">
        <span class="candidate-card__score-num">{{ candidate.score }}</span>
        <span class="candidate-card__score-label">{{ level.label }}</span>
      </div>
    </header>

    <!-- 五角星评分（score/20 → 5 星） -->
    <div class="candidate-card__stars" aria-label="匹配星级">
      <el-icon v-for="i in 5" :key="i" class="candidate-card__star" :class="{ 'is-on': i <= starCount }">
        <StarFilled v-if="i <= starCount" />
        <Star v-else />
      </el-icon>
    </div>

    <!-- 中部 meta -->
    <div class="candidate-card__meta">
      <span>{{ candidate.work_years }}年经验</span>
      <span class="candidate-card__dot">·</span>
      <span>{{ candidate.education || '学历未知' }}</span>
      <span class="candidate-card__dot">·</span>
      <span class="candidate-card__salary">{{ formatSalary(candidate.expected_salary) }}</span>
    </div>

    <!-- 技能标签 -->
    <div v-if="candidate.skills && candidate.skills.length" class="candidate-card__skills">
      <el-tag
        v-for="skill in displaySkills"
        :key="skill"
        size="small"
        class="candidate-card__skill"
      >
        {{ skill }}
      </el-tag>
      <span v-if="extraCount > 0" class="candidate-card__more">+{{ extraCount }}</span>
    </div>

    <!-- 匹配理由 -->
    <p v-if="candidate.reason" class="candidate-card__reason">
      <span class="candidate-card__quote" aria-hidden="true">“</span>
      <span class="candidate-card__reason-text">{{ candidate.reason }}</span>
    </p>
  </article>
</template>

<script setup lang="ts">
/**
 * CandidateCard 候选人卡片
 * 展示候选人摘要与匹配理由，点击 emit select
 */
import { computed } from 'vue'
import { Star, StarFilled } from '@element-plus/icons-vue'
import { formatSalary, scoreLevel } from '@/utils/format'
import type { CandidateCard as CandidateCardType } from '@/types/candidate'

interface CandidateCardProps {
  /** 候选人数据 */
  candidate: CandidateCardType
}

const props = defineProps<CandidateCardProps>()

const emit = defineEmits<{
  /** 选中候选人 */
  (e: 'select', candidate: CandidateCardType): void
}>()

/** 评分等级（颜色/标签） */
const level = computed(() => scoreLevel(props.candidate.score))

/** 五角星数量（score/20，向上取整，最多 5） */
const starCount = computed(() => {
  const raw = Math.ceil(props.candidate.score / 20)
  return Math.min(5, Math.max(0, raw))
})

/** 技能展示前 4 个 */
const MAX = 4
const displaySkills = computed(() => props.candidate.skills.slice(0, MAX))
const extraCount = computed(() => Math.max(0, props.candidate.skills.length - MAX))

/** 选中 */
function handleSelect(): void {
  emit('select', props.candidate)
}
</script>

<style scoped lang="scss">
.candidate-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-5);
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  outline: none;
  transition: transform var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out);

  &:hover,
  &:focus-visible {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg);
    border-color: var(--color-accent-soft);
  }

  &__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-3);
  }

  &__name {
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-weight: 500;
    color: var(--color-primary);
    margin: 0;
  }

  &__score {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    line-height: 1;
  }

  &__score-num {
    font-family: var(--font-mono);
    font-size: var(--text-2xl);
    font-weight: 700;
  }

  &__score-label {
    margin-top: 4px;
    font-size: var(--text-xs);
    letter-spacing: 0.04em;
  }

  &__stars {
    display: flex;
    gap: 2px;
  }

  &__star {
    font-size: 14px;
    color: var(--color-ink-mute);
    &.is-on {
      color: var(--color-accent);
    }
  }

  &__meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
  }

  &__dot {
    margin: 0 6px;
    color: var(--color-ink-mute);
  }

  &__salary {
    font-family: var(--font-mono);
    color: var(--color-accent-deep);
    font-weight: 600;
  }

  &__skills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
  }

  &__skill {
    background-color: var(--color-primary-tint);
    border-color: transparent;
    color: var(--color-primary);
  }

  &__more {
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
    font-family: var(--font-mono);
  }

  &__reason {
    position: relative;
    margin: 0;
    padding-top: var(--space-3);
    border-top: 1px solid var(--color-line-soft);
    font-family: var(--font-display);
    font-style: italic;
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
    line-height: 1.55;
  }

  &__quote {
    color: var(--color-accent);
    font-size: var(--text-xl);
    font-weight: 700;
    margin-right: 4px;
    font-style: normal;
  }

  &__reason-text {
    font-style: italic;
  }
}
</style>
