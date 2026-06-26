<!--
  文件名: components/resume/ResumeCard.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 简历列表卡片
    - 顶部：姓名（衬线）+ 性别·年龄·经验 + 收藏星标
    - 中部：技能标签
    - 底部：学历·地点 + 薪资（琥珀 mono）
    - 解析中状态显示左上角徽章
-->
<template>
  <article
    class="resume-card"
    :class="{ 'is-parsing': isParsing }"
    tabindex="0"
    @click="handleClick"
    @keyup.enter="handleClick"
  >
    <!-- 解析状态徽章 -->
    <div
      v-if="resume.parse_status !== 'completed'"
      class="resume-card__badge"
      :class="`is-${resume.parse_status}`"
    >
      <span class="resume-card__badge-dot" />
      {{ parseLabel }}
    </div>

    <!-- 收藏星标 -->
    <button
      type="button"
      class="resume-card__fav"
      :class="{ 'is-active': resume.is_favorite }"
      :aria-label="resume.is_favorite ? '取消收藏' : '收藏简历'"
      @click.stop="handleToggleFav"
    >
      <el-icon v-if="resume.is_favorite"><StarFilled /></el-icon>
      <el-icon v-else><Star /></el-icon>
    </button>

    <!-- 顶部：姓名 + meta -->
    <header class="resume-card__head">
      <h3 class="resume-card__name">{{ resume.name || '未命名' }}</h3>
      <p class="resume-card__meta">
        <span v-if="resume.gender">{{ resume.gender }}</span>
        <span v-if="resume.age != null" class="resume-card__dot">·</span>
        <span v-if="resume.age != null">{{ resume.age }}岁</span>
        <span v-if="resume.work_years != null" class="resume-card__dot">·</span>
        <span v-if="resume.work_years != null">{{ resume.work_years }}年经验</span>
      </p>
    </header>

    <!-- 中部：技能标签 -->
    <div class="resume-card__skills">
      <el-tag
        v-for="skill in displaySkills"
        :key="skill"
        size="small"
        class="resume-card__skill"
      >
        {{ skill }}
      </el-tag>
      <span v-if="extraSkillCount > 0" class="resume-card__skill-more">+{{ extraSkillCount }}</span>
    </div>

    <!-- 底部：学历·地点 + 薪资 -->
    <footer class="resume-card__foot">
      <div class="resume-card__foot-left">
        <span class="resume-card__edu">{{ resume.education || '学历未知' }}</span>
        <span v-if="resume.location" class="resume-card__dot">·</span>
        <span v-if="resume.location" class="resume-card__loc">{{ resume.location }}</span>
      </div>
      <div class="resume-card__salary">{{ formatSalary(resume.expected_salary) }}</div>
    </footer>
  </article>
</template>

<script setup lang="ts">
/**
 * ResumeCard 简历卡片
 * 展示单条简历摘要信息，可点击与收藏
 */
import { computed } from 'vue'
import { Star, StarFilled } from '@element-plus/icons-vue'
import { formatSalary } from '@/utils/format'
import { PARSE_STATUS } from '@/utils/constant'
import type { ResumeListItem } from '@/types/resume'

interface ResumeCardProps {
  /** 简历列表项数据 */
  resume: ResumeListItem
}

const props = defineProps<ResumeCardProps>()

const emit = defineEmits<{
  /** 点击卡片 */
  (e: 'click', resumeId: string): void
  /** 切换收藏 */
  (e: 'toggle-favorite', resumeId: string): void
}>()

/** 是否解析中（非完成状态） */
const isParsing = computed(() => props.resume.parse_status !== 'completed')

/** 解析状态中文标签 */
const parseLabel = computed(
  () => PARSE_STATUS[props.resume.parse_status] ?? '未知',
)

/** 展示前 4 个技能，超出折叠 */
const MAX_SKILLS = 4
const skillsList = computed<string[]>(() => props.resume.skills ?? [])
const displaySkills = computed(() => skillsList.value.slice(0, MAX_SKILLS))
const extraSkillCount = computed(
  () => Math.max(0, skillsList.value.length - MAX_SKILLS),
)

/** 处理卡片点击 */
function handleClick(): void {
  emit('click', props.resume.resume_id)
}

/** 处理收藏切换 */
function handleToggleFav(): void {
  emit('toggle-favorite', props.resume.resume_id)
}
</script>

<style scoped lang="scss">
.resume-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-5) var(--space-4);
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  transition: transform var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out);
  outline: none;

  &:hover,
  &:focus-visible {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--color-accent-soft);
  }

  &.is-parsing {
    background-color: var(--color-bg-overlay);
  }

  &__badge {
    position: absolute;
    top: var(--space-4);
    left: var(--space-4);
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 8px;
    font-size: var(--text-xs);
    font-weight: 600;
    letter-spacing: 0.04em;
    color: var(--color-ink-soft);
    background-color: var(--color-bg-card);
    border: 1px solid var(--color-line);
    border-radius: 999px;

    &.is-parsing .resume-card__badge-dot {
      background: var(--color-accent);
      animation: pulse-soft 1.2s ease-in-out infinite;
    }
    &.is-failed {
      color: var(--color-coral);
      border-color: var(--color-coral);
    }
    &.is-failed .resume-card__badge-dot {
      background: var(--color-coral);
    }
  }

  &__badge-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-ink-mute);
  }

  &__fav {
    position: absolute;
    top: var(--space-4);
    right: var(--space-4);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    padding: 0;
    border: none;
    background: transparent;
    cursor: pointer;
    color: var(--color-ink-mute);
    border-radius: 50%;
    transition: color var(--duration-fast) var(--ease-out),
      background-color var(--duration-fast) var(--ease-out);

    &:hover {
      background-color: var(--color-primary-tint);
      color: var(--color-accent);
    }
    &.is-active {
      color: var(--color-coral);
    }
    .el-icon {
      font-size: 18px;
    }
  }

  &__head {
    padding-right: var(--space-8);
    margin-top: var(--space-2);
  }

  &__name {
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-weight: 500;
    color: var(--color-primary);
    margin: 0 0 4px 0;
    letter-spacing: -0.01em;
  }

  &__meta {
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
    margin: 0;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
  }

  &__dot {
    margin: 0 6px;
    color: var(--color-ink-mute);
  }

  &__skills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
    min-height: 26px;
  }

  &__skill {
    background-color: var(--color-primary-tint);
    border-color: transparent;
    color: var(--color-primary);
  }

  &__skill-more {
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
    font-family: var(--font-mono);
  }

  &__foot {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: var(--space-3);
    padding-top: var(--space-3);
    border-top: 1px solid var(--color-line-soft);
  }

  &__foot-left {
    display: flex;
    align-items: center;
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
  }

  &__edu {
    color: var(--color-ink);
  }

  &__salary {
    font-family: var(--font-mono);
    font-size: var(--text-md);
    font-weight: 600;
    color: var(--color-accent-deep);
    letter-spacing: 0.01em;
  }
}
</style>
