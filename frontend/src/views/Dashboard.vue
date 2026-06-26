<!--
  文件名: views/Dashboard.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 数据看板
    - 顶部页头：eyebrow + 大标题 + 副文案
    - 4 个统计卡片（简历总数/收藏/解析中/会话数）
    - 3 个图表卡片（Top 技能/学历分布/薪资分布）
    - onMounted 调 getStats，loading 用 LoadingOverlay
-->
<template>
  <div class="page-dashboard">
    <LoadingOverlay :visible="loading" />

    <!-- 页头 -->
    <header class="page-dashboard__head">
      <span class="eyebrow">ANALYTICS</span>
      <h1 class="page-dashboard__title decor-line">数据看板</h1>
      <p class="page-dashboard__subtitle">候选人库全景统计与趋势洞察</p>
    </header>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="page-dashboard__stats">
      <el-col v-for="stat in statCards" :key="stat.key" :span="6">
        <div class="stat-card">
          <div class="stat-card__main">
            <span class="stat-card__num">{{ stat.value }}</span>
            <span class="stat-card__label">{{ stat.label }}</span>
          </div>
          <div class="stat-card__icon">
            <el-icon><component :is="stat.icon" /></el-icon>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表卡片 -->
    <el-row :gutter="16" class="page-dashboard__charts">
      <el-col :span="8">
        <ChartWidget title="Top 技能分布" :option="skillChartOption" :height="320" />
      </el-col>
      <el-col :span="8">
        <ChartWidget title="学历分布" :option="educationChartOption" :height="320" />
      </el-col>
      <el-col :span="8">
        <ChartWidget title="薪资分布" :option="salaryChartOption" :height="320" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
/**
 * Dashboard 数据看板
 * 加载统计数据并渲染统计卡片与图表
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Star, Loading, ChatDotRound } from '@element-plus/icons-vue'
import ChartWidget from '@/components/dashboard/ChartWidget.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import { getStats } from '@/api/dashboard'
import type { DashboardStats } from '@/types/dashboard'

const loading = ref<boolean>(false)
const stats = ref<DashboardStats | null>(null)

/** 统计卡片配置 */
const statCards = computed(() => {
  const s = stats.value
  return [
    { key: 'total', label: '简历总数', value: s?.total_resumes ?? 0, icon: Document },
    { key: 'favorite', label: '收藏数', value: s?.favorite_count ?? 0, icon: Star },
    { key: 'parsing', label: '解析中', value: s?.parsing_count ?? 0, icon: Loading },
    { key: 'sessions', label: '会话数', value: s?.total_sessions ?? 0, icon: ChatDotRound },
  ]
})

/** Top 技能柱状图配置 */
const skillChartOption = computed<Record<string, unknown>>(() => {
  const list = stats.value?.top_skills || []
  return {
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: list.map((i) => i._id),
      axisLabel: { color: '#5c5751', fontSize: 12, rotate: 30 },
      axisLine: { lineStyle: { color: '#e3ddd2' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#918b82', fontSize: 12 },
      splitLine: { lineStyle: { color: '#efeae0' } },
    },
    series: [
      {
        type: 'bar',
        data: list.map((i) => i.count),
        itemStyle: {
          color: '#1a3a32',
          borderRadius: [4, 4, 0, 0],
        },
        barWidth: '48%',
      },
    ],
  }
})

/** 学历分布饼图配置 */
const educationChartOption = computed<Record<string, unknown>>(() => {
  const list = stats.value?.education_distribution || []
  return {
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      textStyle: { color: '#5c5751', fontSize: 12 },
    },
    color: ['#1a3a32', '#c8924a', '#d97757', '#87a878'],
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        label: { show: false },
        labelLine: { show: false },
        data: list.map((i) => ({ name: i._id, value: i.count })),
      },
    ],
  }
})

/** 薪资分布柱状图配置 */
const salaryChartOption = computed<Record<string, unknown>>(() => {
  const list = stats.value?.salary_distribution || []
  return {
    grid: { left: 40, right: 20, top: 20, bottom: 40 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: list.map((i) => i._id),
      axisLabel: { color: '#5c5751', fontSize: 12 },
      axisLine: { lineStyle: { color: '#e3ddd2' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#918b82', fontSize: 12 },
      splitLine: { lineStyle: { color: '#efeae0' } },
    },
    series: [
      {
        type: 'bar',
        data: list.map((i) => i.count),
        itemStyle: {
          color: '#c8924a',
          borderRadius: [4, 4, 0, 0],
        },
        barWidth: '48%',
      },
    ],
  }
})

/**
 * 加载统计数据
 */
async function loadStats(): Promise<void> {
  loading.value = true
  try {
    const data = await getStats()
    stats.value = data
  } catch (err) {
    const msg = err instanceof Error ? err.message : '加载统计数据失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadStats()
})
</script>

<style scoped lang="scss">
.page-dashboard {
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
  }

  &__stats {
    margin-bottom: var(--space-5);
  }

  &__charts {
    margin-top: var(--space-2);
  }
}

/* ============ 统计卡片 ============ */
.stat-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-6) var(--space-5);
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: transform var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out);
  margin-bottom: var(--space-4);

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }

  &__main {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__num {
    font-family: var(--font-display);
    font-size: 40px;
    font-weight: 500;
    color: var(--color-primary);
    line-height: 1.1;
    letter-spacing: -0.02em;
  }

  &__label {
    font-size: var(--text-sm);
    color: var(--color-ink-mute);
    letter-spacing: 0.04em;
  }

  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background-color: var(--color-accent-glow);
    color: var(--color-accent-deep);

    .el-icon {
      font-size: 22px;
    }
  }
}
</style>
