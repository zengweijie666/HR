/**
 * 文件名: tests/components/test_chat_panel.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 对话主面板测试
 *   - ChatPanel 可挂载
 *   - 渲染输入区与发送按钮
 *   - 无会话时显示提示标题
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

// mock 流式发送接口，避免真实网络请求
vi.mock('@/api/chat', () => ({
  sendMessageStream: vi.fn(() => Promise.resolve()),
  createSession: vi.fn(),
  getSessions: vi.fn(),
  getMessages: vi.fn(),
  deleteSession: vi.fn(),
}))

import ChatPanel from '@/components/chat/ChatPanel.vue'
import { useChatStore } from '@/stores/chat'

describe('components/chat/ChatPanel', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('可挂载并渲染输入区（textarea）与发送按钮', () => {
    const wrapper = mount(ChatPanel)
    expect(wrapper.find('textarea').exists()).toBe(true)
    const sendBtn = wrapper
      .findAll('button')
      .find((b) => /发送/.test(b.text() || ''))
    expect(sendBtn).toBeTruthy()
  })

  it('无会话时标题显示提示语', () => {
    const wrapper = mount(ChatPanel)
    expect(wrapper.find('.chat-panel__title').text()).toContain(
      '请选择或新建会话',
    )
  })

  it('发送按钮初始为禁用（无内容/无会话）', () => {
    const wrapper = mount(ChatPanel)
    const sendBtn = wrapper.find('.chat-panel__send')
    expect(sendBtn.attributes('disabled')).toBeDefined()
  })

  it('存在会话且有输入时发送按钮启用', async () => {
    const chat = useChatStore()
    chat.setCurrentSession('s1')
    const wrapper = mount(ChatPanel)
    await wrapper.find('textarea').setValue('推荐一个前端工程师')
    await flushPromises()
    const sendBtn = wrapper.find('.chat-panel__send')
    expect(sendBtn.attributes('disabled')).toBeUndefined()
  })
})
