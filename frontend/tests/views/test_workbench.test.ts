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
import {
  getSessions,
  getMessages,
  createSession,
  deleteSession,
  sendMessageStream,
} from '@/api/chat'

describe('views/Workbench', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
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

  // ===== 以下为补充用例：覆盖会话/消息/候选人交互 =====

  it('加载并渲染多个会话项', async () => {
    vi.mocked(getSessions).mockResolvedValueOnce({
      list: [
        {
          session_id: 's1',
          title: '前端招聘',
          created_at: '2026-06-26T00:00:00Z',
          updated_at: '2026-06-26T00:00:00Z',
        },
        {
          session_id: 's2',
          title: '后端招聘',
          created_at: '2026-06-26T00:00:00Z',
          updated_at: '2026-06-26T00:00:00Z',
        },
      ],
      total: 2,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    const wrapper = mount(Workbench)
    await flushPromises()
    const items = wrapper.findAll('.session-list__item')
    expect(items).toHaveLength(2)
    expect(wrapper.text()).toContain('前端招聘')
    expect(wrapper.text()).toContain('后端招聘')
  })

  it('点击新建会话按钮调用 createSession', async () => {
    vi.mocked(createSession).mockResolvedValueOnce({
      session_id: 'new-s',
      title: '新会话',
      created_at: '2026-06-26T00:00:00Z',
      updated_at: '2026-06-26T00:00:00Z',
    })
    const wrapper = mount(Workbench)
    await flushPromises()
    await wrapper.find('.session-list__new').trigger('click')
    await flushPromises()
    expect(createSession).toHaveBeenCalledWith('新会话')
  })

  it('点击删除会话按钮调用 deleteSession', async () => {
    vi.mocked(getSessions).mockResolvedValueOnce({
      list: [
        {
          session_id: 's1',
          title: '前端招聘',
          created_at: '2026-06-26T00:00:00Z',
          updated_at: '2026-06-26T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    vi.mocked(deleteSession).mockResolvedValueOnce(undefined)
    const wrapper = mount(Workbench)
    await flushPromises()
    await wrapper.find('.session-list__del').trigger('click')
    await flushPromises()
    expect(deleteSession).toHaveBeenCalledWith('s1')
  })

  it('选择会话时加载消息列表并渲染气泡', async () => {
    vi.mocked(getSessions).mockResolvedValueOnce({
      list: [
        {
          session_id: 's1',
          title: '前端招聘',
          created_at: '2026-06-26T00:00:00Z',
          updated_at: '2026-06-26T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    vi.mocked(getMessages).mockResolvedValueOnce([
      {
        message_id: 'm1',
        session_id: 's1',
        role: 'user',
        content: '推荐一个前端工程师',
        intent: null,
        strategy: null,
        candidates: null,
        created_at: '2026-06-26T00:00:00Z',
      },
      {
        message_id: 'm2',
        session_id: 's1',
        role: 'assistant',
        content: '已为你找到张三',
        intent: 'search',
        strategy: 'direct',
        candidates: null,
        created_at: '2026-06-26T00:00:00Z',
      },
    ])
    const wrapper = mount(Workbench)
    await flushPromises()
    await wrapper.find('.session-list__item').trigger('click')
    await flushPromises()
    const msgs = wrapper.findAll('.msg')
    expect(msgs).toHaveLength(2)
    expect(wrapper.text()).toContain('推荐一个前端工程师')
    expect(wrapper.text()).toContain('已为你找到张三')
  })

  it('发送消息触发 sendMessageStream', async () => {
    vi.mocked(getSessions).mockResolvedValueOnce({
      list: [
        {
          session_id: 's1',
          title: '前端招聘',
          created_at: '2026-06-26T00:00:00Z',
          updated_at: '2026-06-26T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    vi.mocked(sendMessageStream).mockResolvedValueOnce(undefined)
    const wrapper = mount(Workbench)
    await flushPromises()
    // 选择会话
    await wrapper.find('.session-list__item').trigger('click')
    await flushPromises()
    // 输入消息
    await wrapper.find('textarea').setValue('推荐一个前端工程师')
    await flushPromises()
    // 点击发送
    await wrapper.find('.chat-panel__send').trigger('click')
    await flushPromises()
    expect(sendMessageStream).toHaveBeenCalled()
    expect(sendMessageStream.mock.calls[0][0]).toBe('s1')
    expect(sendMessageStream.mock.calls[0][1]).toBe('推荐一个前端工程师')
  })

  it('SSE candidates 事件触发候选人卡片渲染', async () => {
    vi.mocked(getSessions).mockResolvedValueOnce({
      list: [
        {
          session_id: 's1',
          title: '前端招聘',
          created_at: '2026-06-26T00:00:00Z',
          updated_at: '2026-06-26T00:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    const candidate = {
      candidate_id: 'c1',
      resume_id: 'r1',
      name: '张三',
      work_years: 5,
      education: '本科',
      skills: ['Vue', 'TypeScript'],
      expected_salary: { min: 20, max: 30 },
      score: 88,
      reason: '技能匹配度高',
      tags: [],
      is_favorite: false,
    }
    ;(sendMessageStream as unknown as ReturnType<typeof vi.fn>).mockImplementationOnce(
      async (_sid: string, _q: string, _ctx: Record<string, unknown>, handlers: {
        onIntent?: (d: { intent: string; strategy: string }) => void
        onCandidates?: (c: typeof candidate[]) => void
        onDone?: (d: { message_id: string; response: string; title?: string | null }) => void
      }) => {
        handlers.onIntent?.({ intent: 'search', strategy: 'direct' })
        handlers.onCandidates?.([candidate])
        handlers.onDone?.({ message_id: 'm-assistant', response: '已找到', title: null })
      },
    )
    const wrapper = mount(Workbench)
    await flushPromises()
    // 选择会话
    await wrapper.find('.session-list__item').trigger('click')
    await flushPromises()
    // 输入并发送
    await wrapper.find('textarea').setValue('推荐前端')
    await flushPromises()
    await wrapper.find('.chat-panel__send').trigger('click')
    await flushPromises()
    expect(wrapper.find('.candidate-card').exists()).toBe(true)
    expect(wrapper.text()).toContain('张三')
  })
})
