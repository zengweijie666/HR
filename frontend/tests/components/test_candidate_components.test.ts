/**
 * 文件名: tests/components/test_candidate_components.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 候选人组件测试
 *   - CandidateCard 渲染姓名/分数/点击 select
 *   - TagInput 回车添加标签
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CandidateCard from '@/components/candidate/CandidateCard.vue'
import TagInput from '@/components/candidate/TagInput.vue'
import type { CandidateCard as CandidateCardType } from '@/types/candidate'

const candidate: CandidateCardType = {
  candidate_id: 'c1',
  resume_id: 'r1',
  name: '李四',
  work_years: 6,
  education: '硕士',
  skills: ['Java', 'Spring', 'MySQL', 'Redis', 'Kafka'],
  expected_salary: { min: 25, max: 40 },
  score: 85,
  reason: '技术栈与岗位匹配度高',
  tags: [],
  is_favorite: false,
}

describe('components/candidate/CandidateCard', () => {
  it('渲染姓名与匹配分', () => {
    const wrapper = mount(CandidateCard, { props: { candidate } })
    expect(wrapper.find('.candidate-card__name').text()).toBe('李四')
    expect(wrapper.find('.candidate-card__score-num').text()).toBe('85')
  })

  it('渲染匹配理由（含引号装饰）', () => {
    const wrapper = mount(CandidateCard, { props: { candidate } })
    expect(wrapper.find('.candidate-card__reason').exists()).toBe(true)
    expect(wrapper.text()).toContain('技术栈与岗位匹配度高')
  })

  it('点击卡片触发 select 事件', async () => {
    const wrapper = mount(CandidateCard, { props: { candidate } })
    await wrapper.find('.candidate-card').trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')![0]).toEqual([candidate])
  })

  it('根据分数渲染五角星', () => {
    const wrapper = mount(CandidateCard, { props: { candidate } })
    // score 85 → ceil(85/20)=5 星
    const stars = wrapper.findAll('.candidate-card__star.is-on')
    expect(stars.length).toBe(5)
  })

  it('提供 score_detail 时渲染 4 维度评分条', () => {
    const wrapper = mount(CandidateCard, {
      props: {
        candidate: {
          ...candidate,
          score_detail: { skill: 85, experience: 70, education: 90, salary: 60 },
        },
      },
    })
    const dims = wrapper.findAll('.candidate-card__dim')
    expect(dims.length).toBe(4)
    // 第一个维度为 skill=85
    expect(dims[0].find('.candidate-card__dim-label').text()).toBe('技能')
    expect(dims[0].find('.candidate-card__dim-value').text()).toBe('85')
  })

  it('无 score_detail 时不渲染维度区', () => {
    const wrapper = mount(CandidateCard, { props: { candidate } })
    expect(wrapper.find('.candidate-card__dims').exists()).toBe(false)
  })
})

describe('components/candidate/TagInput', () => {
  it('回车添加标签触发 update:modelValue', async () => {
    const wrapper = mount(TagInput, { props: { modelValue: [] } })
    const input = wrapper.find('input')
    await input.setValue('java')
    await input.trigger('keyup', { key: 'Enter' })
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([['java']])
  })

  it('失焦也添加标签', async () => {
    const wrapper = mount(TagInput, { props: { modelValue: [] } })
    const input = wrapper.find('input')
    await input.setValue('vue')
    await input.trigger('blur')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([['vue']])
  })

  it('空内容回车不添加', async () => {
    const wrapper = mount(TagInput, { props: { modelValue: [] } })
    const input = wrapper.find('input')
    await input.setValue('   ')
    await input.trigger('keyup', { key: 'Enter' })
    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
  })

  it('点击标签关闭按钮删除', async () => {
    const wrapper = mount(TagInput, {
      props: { modelValue: ['java', 'vue'] },
    })
    const closeBtns = wrapper.findAll('.tag-input__tag .el-tag__close')
    expect(closeBtns.length).toBeGreaterThan(0)
    await closeBtns[0].trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([['vue']])
  })
})
