/**
 * 文件名: tests/views/test_dashboard.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 数据看板测试
 *   - mock @/api/dashboard 的 getStats
 *   - mock echarts 模块（避免 jsdom 报错）
 *   - 渲染看板容器 .page-dashboard 与统计卡片 .stat-card
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
  })),
}))

vi.mock('@/api/dashboard', () => ({
  getStats: vi.fn(() =>
    Promise.resolve({
      total_resumes: 120,
      favorite_count: 18,
      parsing_count: 3,
      total_sessions: 25,
      top_skills: [
        { _id: 'Vue', count: 30 },
        { _id: 'Python', count: 22 },
      ],
      education_distribution: [
        { _id: '本科', count: 60 },
        { _id: '硕士', count: 30 },
      ],
      salary_distribution: [
        { _id: '20-30K', count: 40 },
        { _id: '30-50K', count: 20 },
      ],
    }),
  ),
}))

import Dashboard from '@/views/Dashboard.vue'

describe('views/Dashboard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('渲染看板容器 .page-dashboard', async () => {
    const wrapper = mount(Dashboard)
    await flushPromises()
    expect(wrapper.find('.page-dashboard').exists()).toBe(true)
  })

  it('渲染页头标题 "数据看板"', async () => {
    const wrapper = mount(Dashboard)
    await flushPromises()
    expect(wrapper.find('.page-dashboard__title').text()).toBe('数据看板')
  })

  it('渲染 4 个统计卡片', async () => {
    const wrapper = mount(Dashboard)
    await flushPromises()
    const cards = wrapper.findAll('.stat-card')
    expect(cards.length).toBe(4)
  })

  it('加载统计数据后渲染简历总数', async () => {
    const wrapper = mount(Dashboard)
    await flushPromises()
    const nums = wrapper.findAll('.stat-card__num').map((n) => n.text())
    expect(nums).toContain('120')
    expect(nums).toContain('18')
    expect(nums).toContain('3')
    expect(nums).toContain('25')
  })

  it('渲染 3 个图表卡片 ChartWidget', async () => {
    const wrapper = mount(Dashboard)
    await flushPromises()
    const charts = wrapper.findAllComponents({ name: 'ChartWidget' })
    expect(charts.length).toBe(3)
  })
})
