<!--
  文件名: components/dashboard/ChartWidget.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 看板图表卡片
    - el-card 包裹，自定义头部（标题衬线 + decor-line 下划线）
    - onMounted init ECharts，watch option 重新 setOption
    - 窗口 resize 时 chart.resize()
-->
<template>
  <el-card class="chart-widget" shadow="never">
    <template #header>
      <div class="chart-widget__header">
        <h4 class="chart-widget__title decor-line">{{ title }}</h4>
        <slot name="extra" />
      </div>
    </template>
    <div ref="chartRef" class="chart-widget__body" :style="{ height: bodyHeight }" />
  </el-card>
</template>

<script setup lang="ts">
/**
 * ChartWidget 看板图表容器
 * 接收 ECharts option，负责初始化与响应式更新
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface ChartWidgetProps {
  /** 图表标题 */
  title: string
  /** ECharts 配置项 */
  option: Record<string, unknown>
  /** 图表高度，默认 300 */
  height?: number
}

const props = withDefaults(defineProps<ChartWidgetProps>(), {
  height: 300,
})

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

/** 容器高度样式 */
const bodyHeight = `${props.height}px`

/** 处理窗口缩放 */
function handleResize(): void {
  chart?.resize()
}

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    chart.setOption(props.option, true)
    window.addEventListener('resize', handleResize)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})

watch(
  () => props.option,
  (val) => {
    chart?.setOption(val, true)
  },
  { deep: true },
)
</script>

<style scoped lang="scss">
.chart-widget {
  :deep(.el-card__header) {
    padding: var(--space-4) var(--space-5);
    border-bottom: 1px solid var(--color-line);
  }

  :deep(.el-card__body) {
    padding: var(--space-4) var(--space-5);
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-3);
  }

  &__title {
    font-family: var(--font-display);
    font-size: var(--text-md);
    font-weight: 500;
    color: var(--color-primary);
    margin: 0;
    padding-bottom: 6px;
  }

  &__body {
    width: 100%;
  }
}
</style>
