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
import { ElMessage } from 'element-plus'
import { getStats } from '@/api/dashboard'

describe('views/Dashboard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
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

  it('渲染 7 个图表卡片 ChartWidget', async () => {
    const wrapper = mount(Dashboard)
    await flushPromises()
    const charts = wrapper.findAllComponents({ name: 'ChartWidget' })
    expect(charts.length).toBe(7)
  })

  // ===== 以下为补充用例：覆盖接口失败/加载状态/图表初始化/空数据/窗口 resize =====

  it('接口失败时显示错误提示', async () => {
    const errorSpy = vi.spyOn(ElMessage, 'error').mockImplementation(() => ({}))
    vi.mocked(getStats).mockRejectedValueOnce(new Error('网络连接失败'))
    mount(Dashboard)
    await flushPromises()
    expect(errorSpy).toHaveBeenCalledWith('网络连接失败')
    errorSpy.mockRestore()
  })

  it('加载中显示 loading 遮罩，加载完成后消失', async () => {
    let resolveStats!: (v: unknown) => void
    vi.mocked(getStats).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveStats = resolve as (v: unknown) => void
      }),
    )
    const wrapper = mount(Dashboard)
    await flushPromises()
    // loading 中显示遮罩
    expect(wrapper.find('.loading-overlay').exists()).toBe(true)
    // 解析后遮罩消失
    resolveStats({
      total_resumes: 0,
      favorite_count: 0,
      parsing_count: 0,
      total_sessions: 0,
      top_skills: [],
      education_distribution: [],
      salary_distribution: [],
      recruitment_funnel: [],
      resume_trend: [],
      work_years_distribution: [],
      interview_result_distribution: [],
    })
    await flushPromises()
    expect(wrapper.find('.loading-overlay').exists()).toBe(false)
  })

  it('图表初始化调用 echarts init 和 setOption', async () => {
    const echarts = await import('echarts')
    // 为第一个 ChartWidget 返回带 spy 的 chart 实例
    const setOptionSpy = vi.fn()
    vi.mocked(echarts.init).mockReturnValueOnce({
      setOption: setOptionSpy,
      resize: vi.fn(),
      dispose: vi.fn(),
    } as never)
    mount(Dashboard)
    await flushPromises()
    // echarts.init 被调用（每个 ChartWidget 调用一次）
    expect(echarts.init).toHaveBeenCalled()
    // setOption 在 onMounted 中被调用
    expect(setOptionSpy).toHaveBeenCalled()
  })

  it('空数据场景下统计卡片显示 0 且页面正常渲染', async () => {
    vi.mocked(getStats).mockResolvedValueOnce({
      total_resumes: 0,
      favorite_count: 0,
      parsing_count: 0,
      total_sessions: 0,
      top_skills: [],
      education_distribution: [],
      salary_distribution: [],
      recruitment_funnel: [],
      resume_trend: [],
      work_years_distribution: [],
      interview_result_distribution: [],
    })
    const wrapper = mount(Dashboard)
    await flushPromises()
    // 4 个统计卡片均显示 0
    const nums = wrapper.findAll('.stat-card__num').map((n) => n.text())
    expect(nums).toEqual(['0', '0', '0', '0'])
    // 页面容器与图表卡片仍正常渲染
    expect(wrapper.find('.page-dashboard').exists()).toBe(true)
    expect(wrapper.findAllComponents({ name: 'ChartWidget' }).length).toBe(7)
  })

  it('窗口 resize 触发图表 resize', async () => {
    const echarts = await import('echarts')
    const resizeSpy = vi.fn()
    vi.mocked(echarts.init).mockReturnValueOnce({
      setOption: vi.fn(),
      resize: resizeSpy,
      dispose: vi.fn(),
    } as never)
    mount(Dashboard)
    await flushPromises()
    // 派发 resize 事件，ChartWidget 内 handleResize 调用 chart.resize()
    window.dispatchEvent(new Event('resize'))
    expect(resizeSpy).toHaveBeenCalled()
  })
})
