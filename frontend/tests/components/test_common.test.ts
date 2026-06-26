/**
 * 文件名: tests/components/test_common.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 通用组件测试
 *   - EmptyState 默认文案 / 自定义文案
 *   - LoadingOverlay visible 切换
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

describe('components/common/EmptyState', () => {
  it('默认文案为 暂无数据', () => {
    const wrapper = mount(EmptyState)
    expect(wrapper.find('.empty-state__text').text()).toBe('暂无数据')
  })

  it('支持自定义文案', () => {
    const wrapper = mount(EmptyState, { props: { text: '还没有简历' } })
    expect(wrapper.find('.empty-state__text').text()).toBe('还没有简历')
  })

  it('渲染装饰 SVG 插画', () => {
    const wrapper = mount(EmptyState)
    expect(wrapper.find('svg.empty-state__art').exists()).toBe(true)
  })
})

describe('components/common/LoadingOverlay', () => {
  it('visible=false 时不渲染遮罩', () => {
    const wrapper = mount(LoadingOverlay, { props: { visible: false } })
    expect(wrapper.find('.loading-overlay').exists()).toBe(false)
  })

  it('visible=true 时渲染遮罩与文案', () => {
    const wrapper = mount(LoadingOverlay, {
      props: { visible: true, text: '正在加载' },
    })
    expect(wrapper.find('.loading-overlay').exists()).toBe(true)
    expect(wrapper.find('.loading-overlay__text').text()).toBe('正在加载')
  })

  it('visible 切换：true → false 后遮罩消失', async () => {
    const wrapper = mount(LoadingOverlay, { props: { visible: true } })
    expect(wrapper.find('.loading-overlay').exists()).toBe(true)
    await wrapper.setProps({ visible: false })
    expect(wrapper.find('.loading-overlay').exists()).toBe(false)
  })
})
