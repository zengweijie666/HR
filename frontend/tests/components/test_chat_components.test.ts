/**
 * 文件名: tests/components/test_chat_components.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 对话组件测试
 *   - MessageBubble 渲染 user/assistant 及候选人缩略
 *   - StreamIndicator 显示意图中文标签
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import StreamIndicator from '@/components/chat/StreamIndicator.vue'
import type { ChatMessage, SSEHandlers } from '@/types/chat'
import type { CandidateCard } from '@/types/candidate'

/** 构造测试消息 */
function makeMessage(
  role: 'user' | 'assistant',
  content: string,
  candidates: CandidateCard[] | null = null,
): ChatMessage {
  return {
    message_id: 'm1',
    session_id: 's1',
    role,
    content,
    intent: null,
    strategy: null,
    candidates,
    created_at: '2026-06-26T10:00:00Z',
  }
}

const candidate: CandidateCard = {
  candidate_id: 'c1',
  resume_id: 'r1',
  name: '张三',
  work_years: 5,
  education: '本科',
  skills: ['Vue'],
  expected_salary: { min: 20, max: 30 },
  score: 88,
  reason: '匹配度高',
  tags: [],
  is_favorite: false,
}

describe('components/chat/MessageBubble', () => {
  it('渲染 user 消息并应用 user 样式', () => {
    const wrapper = mount(MessageBubble, {
      props: { message: makeMessage('user', '你好') },
    })
    expect(wrapper.classes()).toContain('msg--user')
    expect(wrapper.text()).toContain('你好')
    expect(wrapper.find('.msg__avatar--user').exists()).toBe(true)
  })

  it('渲染 assistant 消息并应用 assistant 样式', () => {
    const wrapper = mount(MessageBubble, {
      props: { message: makeMessage('assistant', '我是 AI 助手') },
    })
    expect(wrapper.classes()).toContain('msg--assistant')
    expect(wrapper.find('.msg__avatar--assistant').exists()).toBe(true)
  })

  it('有候选人时渲染候选人缩略列表', () => {
    const wrapper = mount(MessageBubble, {
      props: { message: makeMessage('assistant', '推荐', [candidate]) },
    })
    expect(wrapper.find('.msg__candidates').exists()).toBe(true)
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('88')
  })

  it('无候选人时不渲染缩略列表', () => {
    const wrapper = mount(MessageBubble, {
      props: { message: makeMessage('assistant', '回答') },
    })
    expect(wrapper.find('.msg__candidates').exists()).toBe(false)
  })

  it('类型兼容 SSEHandlers（仅类型校验）', () => {
    const handlers: SSEHandlers = {
      onToken: (delta: string) => delta,
    }
    expect(handlers.onToken).toBeDefined()
  })
})

describe('components/chat/StreamIndicator', () => {
  it('显示意图与策略的中文标签', () => {
    const wrapper = mount(StreamIndicator, {
      props: { intent: 'search', strategy: 'hyde' },
    })
    expect(wrapper.text()).toContain('搜索推荐')
    expect(wrapper.text()).toContain('假设文档')
  })

  it('未传 intent/strategy 时不渲染标签（仍显示生成中）', () => {
    const wrapper = mount(StreamIndicator, {})
    expect(wrapper.text()).toContain('生成中')
    expect(wrapper.findAll('.stream-indicator__tag')).toHaveLength(0)
  })
})
