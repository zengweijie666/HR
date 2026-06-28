/**
 * 文件名: tests/views/test_jd_match.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: JD 匹配页测试
 *   - 渲染 JD 输入区 .jd-input
 *   - 无需 mock（按钮触发才请求）
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { ElMessage } from 'element-plus'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('@/api/jd', () => ({
  matchJd: vi.fn(() =>
    Promise.resolve({
      jd: { title: '', skills: [], work_years_min: 0, salary_max: 0 },
      candidates: [],
    }),
  ),
}))

import JdMatch from '@/views/JdMatch.vue'
import { matchJd } from '@/api/jd'

describe('views/JdMatch', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('渲染 JD 输入区 .jd-input', () => {
    const wrapper = mount(JdMatch)
    expect(wrapper.find('.jd-input').exists()).toBe(true)
  })

  it('渲染页头标题 "JD 匹配"', () => {
    const wrapper = mount(JdMatch)
    expect(wrapper.find('.page-jd-match__title').text()).toBe('JD 匹配')
  })

  it('渲染字符计数与 Top K 输入', () => {
    const wrapper = mount(JdMatch)
    expect(wrapper.find('.jd-input__count').exists()).toBe(true)
    expect(wrapper.find('.jd-input__topk').exists()).toBe(true)
  })

  it('初始无结果时渲染 EmptyState 提示', () => {
    const wrapper = mount(JdMatch)
    expect(wrapper.text()).toContain('粘贴 JD 后开始匹配')
  })

  it('渲染 JD 输入 textarea', () => {
    const wrapper = mount(JdMatch)
    expect(wrapper.find('textarea').exists()).toBe(true)
  })

  // ===== 以下为补充用例：字符计数/API触发/结果渲染/loading/错误/空结果/TopK =====

  it('输入 JD 文本后字符计数实时更新', async () => {
    const wrapper = mount(JdMatch)
    expect(wrapper.find('.jd-input__count').text()).toBe('0 字')
    await wrapper.find('textarea').setValue('招聘资深前端工程师')
    expect(wrapper.find('.jd-input__count').text()).toBe('9 字')
  })

  it('点击匹配按钮触发 matchJd API 调用', async () => {
    vi.mocked(matchJd).mockResolvedValueOnce({
      jd: { title: '前端工程师', skills: ['Vue'], work_years_min: 3, salary_max: 30 },
      candidates: [],
    })
    const wrapper = mount(JdMatch)
    await wrapper.find('textarea').setValue('需要一名 Vue 工程师')
    await wrapper.find('.jd-input__submit').trigger('click')
    await flushPromises()
    expect(matchJd).toHaveBeenCalledWith('需要一名 Vue 工程师', 10)
  })

  it('匹配成功后渲染候选人列表与 JD 信息', async () => {
    vi.mocked(matchJd).mockResolvedValueOnce({
      jd: { title: '前端工程师', skills: ['Vue', 'TypeScript'], work_years_min: 3, salary_max: 30 },
      candidates: [
        { candidate_id: 'c1', resume_id: 'r1', name: '张三', work_years: 5, education: '本科', skills: ['Vue'], expected_salary: { min: 20, max: 30 }, score: 88, reason: '技能匹配', tags: [], is_favorite: false, match_score: 88 },
        { candidate_id: 'c2', resume_id: 'r2', name: '李四', work_years: 4, education: '硕士', skills: ['React'], expected_salary: { min: 25, max: 35 }, score: 75, reason: '经验丰富', tags: [], is_favorite: false, match_score: 75 },
      ],
    })
    const wrapper = mount(JdMatch)
    await wrapper.find('textarea').setValue('招聘前端工程师')
    await wrapper.find('.jd-input__submit').trigger('click')
    await flushPromises()
    expect(wrapper.find('.jd-result__candidates').exists()).toBe(true)
    expect(wrapper.findAll('.candidate-card').length).toBe(2)
    expect(wrapper.find('.jd-result__sub-title').text()).toContain('2')
    expect(wrapper.find('.jd-info__title').text()).toBe('前端工程师')
  })

  it('匹配过程中按钮与遮罩显示 loading 状态', async () => {
    let resolveMatch!: (v: unknown) => void
    vi.mocked(matchJd).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveMatch = resolve as (v: unknown) => void
      }),
    )
    const wrapper = mount(JdMatch)
    await wrapper.find('textarea').setValue('招聘工程师')
    await wrapper.find('.jd-input__submit').trigger('click')
    await flushPromises()
    expect(wrapper.find('.jd-input__submit').classes()).toContain('is-loading')
    expect(wrapper.find('.loading-overlay').exists()).toBe(true)
    resolveMatch({ jd: { title: '', skills: [], work_years_min: 0, salary_max: 0 }, candidates: [] })
    await flushPromises()
    expect(wrapper.find('.jd-input__submit').classes()).not.toContain('is-loading')
  })

  it('匹配 API 报错时显示错误提示', async () => {
    const errorSpy = vi.spyOn(ElMessage, 'error').mockImplementation(() => ({}) as never)
    vi.mocked(matchJd).mockRejectedValueOnce(new Error('服务异常'))
    const wrapper = mount(JdMatch)
    await wrapper.find('textarea').setValue('招聘工程师')
    await wrapper.find('.jd-input__submit').trigger('click')
    await flushPromises()
    expect(errorSpy).toHaveBeenCalledWith('服务异常')
    errorSpy.mockRestore()
  })

  it('匹配结果候选人为空时提示未匹配到', async () => {
    const infoSpy = vi.spyOn(ElMessage, 'info').mockImplementation(() => ({}) as never)
    vi.mocked(matchJd).mockResolvedValueOnce({
      jd: { title: '测试岗', skills: [], work_years_min: 0, salary_max: 0 },
      candidates: [],
    })
    const wrapper = mount(JdMatch)
    await wrapper.find('textarea').setValue('招聘测试岗')
    await wrapper.find('.jd-input__submit').trigger('click')
    await flushPromises()
    expect(infoSpy).toHaveBeenCalledWith('未匹配到合适的候选人')
    expect(wrapper.text()).toContain('未匹配到合适的候选人')
    infoSpy.mockRestore()
  })

  it('Top K 值变更后随匹配请求一起传入', async () => {
    vi.mocked(matchJd).mockResolvedValueOnce({
      jd: { title: '', skills: [], work_years_min: 0, salary_max: 0 },
      candidates: [],
    })
    const wrapper = mount(JdMatch)
    const topkInput = wrapper.find('.jd-input__topk input')
    await topkInput.setValue('20')
    await topkInput.trigger('blur')
    await wrapper.find('textarea').setValue('招聘工程师')
    await wrapper.find('.jd-input__submit').trigger('click')
    await flushPromises()
    expect(matchJd).toHaveBeenCalledWith('招聘工程师', 20)
  })
})
