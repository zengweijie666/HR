/**
 * 文件名: tests/components/test_resume_components.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 简历组件测试
 *   - ResumeCard 渲染姓名/技能/点击收藏
 *   - FilterBar 输入触发 search
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ResumeCard from '@/components/resume/ResumeCard.vue'
import FilterBar from '@/components/resume/FilterBar.vue'
import type { ResumeListItem } from '@/types/resume'

const resume: ResumeListItem = {
  resume_id: 'r1',
  candidate_id: 'c1',
  name: '张三',
  gender: '男',
  age: 28,
  education: '本科',
  education_level: 1,
  work_years: 5,
  skills: ['Vue', 'TypeScript', 'Node', 'Python', 'Go'],
  expected_salary: { min: 20, max: 30 },
  tags: [],
  is_favorite: false,
  parse_status: 'completed',
  location: '上海',
  created_at: '2026-06-01',
}

describe('components/resume/ResumeCard', () => {
  it('渲染姓名与技能标签（超出折叠 +N）', () => {
    const wrapper = mount(ResumeCard, { props: { resume } })
    expect(wrapper.find('.resume-card__name').text()).toBe('张三')
    expect(wrapper.text()).toContain('Vue')
    expect(wrapper.text()).toContain('TypeScript')
    // 5 个技能，最多展示 4 个 → +1
    expect(wrapper.text()).toContain('+1')
  })

  it('渲染薪资范围', () => {
    const wrapper = mount(ResumeCard, { props: { resume } })
    expect(wrapper.find('.resume-card__salary').text()).toBe('20-30K')
  })

  it('点击收藏触发 toggle-favorite 且不触发卡片 click', async () => {
    const wrapper = mount(ResumeCard, { props: { resume } })
    await wrapper.find('.resume-card__fav').trigger('click')
    expect(wrapper.emitted('toggle-favorite')).toBeTruthy()
    expect(wrapper.emitted('toggle-favorite')![0]).toEqual(['r1'])
    expect(wrapper.emitted('click')).toBeFalsy()
  })

  it('点击卡片触发 click 事件', async () => {
    const wrapper = mount(ResumeCard, { props: { resume } })
    await wrapper.find('.resume-card').trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
    expect(wrapper.emitted('click')![0]).toEqual(['r1'])
  })

  it('解析中状态显示徽章', () => {
    const wrapper = mount(ResumeCard, {
      props: { resume: { ...resume, parse_status: 'parsing' } },
    })
    expect(wrapper.find('.resume-card__badge').exists()).toBe(true)
    expect(wrapper.text()).toContain('解析中')
  })

  it('点击邮件按钮触发 send-email 且不触发卡片 click', async () => {
    const wrapper = mount(ResumeCard, { props: { resume } })
    await wrapper.find('.resume-card__email').trigger('click')
    expect(wrapper.emitted('send-email')).toBeTruthy()
    expect(wrapper.emitted('send-email')![0]).toEqual(['r1'])
    expect(wrapper.emitted('click')).toBeFalsy()
  })
})

describe('components/resume/FilterBar', () => {
  it('输入关键词后点击搜索触发 search 事件', async () => {
    const wrapper = mount(FilterBar)
    const keywordInput = wrapper.find('input[placeholder*="搜索姓名"]')
    await keywordInput.setValue('vue')
    const searchBtn = wrapper
      .findAll('button')
      .find((b) => /搜索/.test(b.text() || ''))
    expect(searchBtn).toBeTruthy()
    await searchBtn!.trigger('click')
    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')![0][0]).toMatchObject({ keyword: 'vue' })
  })

  it('重置按钮触发 reset 事件且清空条件', async () => {
    const wrapper = mount(FilterBar)
    const resetBtn = wrapper
      .findAll('button')
      .find((b) => /重置/.test(b.text() || ''))
    await resetBtn!.trigger('click')
    expect(wrapper.emitted('reset')).toBeTruthy()
    expect(wrapper.emitted('search')).toBeFalsy()
  })

  it('点击搜索按钮触发 search 携带 sort_by 和 sort_order 默认值', async () => {
    const wrapper = mount(FilterBar)
    const searchBtn = wrapper
      .findAll('button')
      .find((b) => /搜索/.test(b.text() || ''))
    await searchBtn!.trigger('click')
    const emitted = wrapper.emitted('search')
    expect(emitted).toBeTruthy()
    expect(emitted![0][0]).toHaveProperty('sort_by')
    expect(emitted![0][0]).toHaveProperty('sort_order')
  })

  it('渲染日期范围选择器', () => {
    const wrapper = mount(FilterBar)
    expect(wrapper.find('.filter-bar__field--date').exists()).toBe(true)
  })

  it('渲染排序选项下拉', () => {
    const wrapper = mount(FilterBar)
    expect(wrapper.find('.filter-bar__field--sort').exists()).toBe(true)
  })

  it('渲染收藏筛选下拉', () => {
    const wrapper = mount(FilterBar)
    expect(wrapper.find('.filter-bar__field--fav').exists()).toBe(true)
  })
})
