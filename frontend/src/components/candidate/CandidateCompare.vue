<!--
  文件名: components/candidate/CandidateCompare.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 候选人对比雷达图
    - ECharts 雷达图：工作年限/学历/技能数/薪资上限/匹配分
    - 多候选人叠加，主色调系列
    - 高度 400px，宽度自适应
-->
<template>
  <div ref="chartRef" class="candidate-compare" />
</template>

<script setup lang="ts">
/**
 * CandidateCompare 候选人对比雷达图
 * 基于 ECharts 渲染多候选人维度对比
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { CandidateCard } from '@/types/candidate'

interface CandidateCompareProps {
  /** 候选人列表 */
  candidates: CandidateCard[]
}

const props = defineProps<CandidateCompareProps>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

/** 主色调系列（深墨绿系递进） */
const PALETTE = ['#1a3a32', '#c8924a', '#2d5247', '#9c6f2e', '#87a878', '#d97757']

/** 学历等级映射为数值 */
function educationLevel(edu: string): number {
  const map: Record<string, number> = { 专科: 1, 本科: 2, 硕士: 3, 博士: 4 }
  return map[edu] ?? 1
}

/** 构建 ECharts option */
function buildOption(): echarts.EChartsCoreOption {
  const indicators = [
    { name: '工作年限', max: 20 },
    { name: '学历', max: 4 },
    { name: '技能数', max: 10 },
    { name: '薪资上限', max: 80 },
    { name: '匹配分', max: 100 },
  ]

  const series = props.candidates.map((c, idx) => ({
    name: c.name,
    value: [
      c.work_years,
      educationLevel(c.education),
      c.skills.length,
      c.expected_salary?.max ?? 0,
      c.score,
    ],
    itemStyle: { color: PALETTE[idx % PALETTE.length] },
    areaStyle: { opacity: 0.12 },
    lineStyle: { width: 2 },
  }))

  return {
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      textStyle: { color: '#5c5751', fontFamily: 'Manrope' },
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: '#2d5247',
        fontFamily: 'Fraunces',
        fontSize: 13,
      },
      splitLine: { lineStyle: { color: '#e3ddd2' } },
      splitArea: { areaStyle: { color: ['#faf7f1', '#ffffff'] } },
      axisLine: { lineStyle: { color: '#e3ddd2' } },
    },
    series: [
      {
        type: 'radar',
        data: series,
      },
    ],
  }
}

/** 渲染图表 */
function render(): void {
  if (!chart) return
  chart.setOption(buildOption(), true)
}

/** 处理窗口缩放 */
function handleResize(): void {
  chart?.resize()
}

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    render()
    window.addEventListener('resize', handleResize)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})

watch(
  () => props.candidates,
  () => render(),
  { deep: true },
)
</script>

<style scoped lang="scss">
.candidate-compare {
  width: 100%;
  height: 400px;
}
</style>
