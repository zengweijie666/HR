/**
 * 文件名: tests/views/test_workbench.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 工作台测试
 *   - mock @/api/chat 的 getSessions / getMessages / createSession / deleteSession / sendMessageStream
 *   - mock vue-router 的 useRouter
 *   - 渲染对话区 .chat-section 与候选人区 .candidate-section
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('@/api/chat', () => ({
  getSessions: vi.fn(() =>
    Promise.resolve({
      list: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }),
  ),
  getMessages: vi.fn(() => Promise.resolve([])),
  createSession: vi.fn(() =>
    Promise.resolve({
      session_id: 's1',
      title: '新会话',
      created_at: '2026-06-26T00:00:00Z',
      updated_at: '2026-06-26T00:00:00Z',
    }),
  ),
  deleteSession: vi.fn(() => Promise.resolve()),
  sendMessageStream: vi.fn(() => Promise.resolve()),
}))

import Workbench from '@/views/Workbench.vue'

describe('views/Workbench', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('渲染对话区 .chat-section 与候选人区 .candidate-section', async () => {
    const wrapper = mount(Workbench)
    await flushPromises()
    expect(wrapper.find('.chat-section').exists()).toBe(true)
    expect(wrapper.find('.candidate-section').exists()).toBe(true)
  })

  it('渲染会话列表区 .workbench__sessions', async () => {
    const wrapper = mount(Workbench)
    await flushPromises()
    expect(wrapper.find('.workbench__sessions').exists()).toBe(true)
  })

  it('无候选人时渲染 EmptyState 提示', async () => {
    const wrapper = mount(Workbench)
    await flushPromises()
    expect(wrapper.text()).toContain('对话后将显示推荐候选人')
  })

  it('渲染推荐候选人区标题', async () => {
    const wrapper = mount(Workbench)
    await flushPromises()
    expect(wrapper.find('.candidate-section__title').text()).toContain('推荐候选人')
  })
})
