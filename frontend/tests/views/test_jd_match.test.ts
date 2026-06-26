/**
 * 文件名: tests/views/test_jd_match.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: JD 匹配页测试
 *   - 渲染 JD 输入区 .jd-input
 *   - 无需 mock（按钮触发才请求）
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

import JdMatch from '@/views/JdMatch.vue'

describe('views/JdMatch', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
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
})
