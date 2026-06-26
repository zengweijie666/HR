/**
 * 文件名: tests/components/test_chart_widget.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 看板图表组件测试
 *   - mock echarts 模块避免 jsdom 报错
 *   - ChartWidget 渲染标题与默认高度
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'

// mock echarts：init 返回含 setOption/resize/dispose 的桩对象
vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
  })),
}))

import ChartWidget from '@/components/dashboard/ChartWidget.vue'

describe('components/dashboard/ChartWidget', () => {
  it('渲染标题', () => {
    const wrapper = mount(ChartWidget, {
      props: { title: '招聘漏斗', option: {} },
    })
    expect(wrapper.find('.chart-widget__title').text()).toBe('招聘漏斗')
  })

  it('默认高度 300px', () => {
    const wrapper = mount(ChartWidget, {
      props: { title: '趋势图', option: {} },
    })
    const style = wrapper.find('.chart-widget__body').attributes('style') || ''
    expect(style).toContain('300px')
  })

  it('自定义高度生效', () => {
    const wrapper = mount(ChartWidget, {
      props: { title: '来源', option: {}, height: 420 },
    })
    const style = wrapper.find('.chart-widget__body').attributes('style') || ''
    expect(style).toContain('420px')
  })

  it('挂载时调用 echarts.init 与 setOption', async () => {
    const echarts = await import('echarts')
    mount(ChartWidget, { props: { title: '概览', option: { series: [] } } })
    expect(echarts.init).toHaveBeenCalled()
  })
})
