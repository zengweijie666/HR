/**
 * 文件名: tests/views/test_resume_detail.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 简历详情页测试
 *   - mock @/api/resume 的 getResumeDetail / getPreviewUrl / toggleFavorite / updateNotes / updateTags
 *   - mock vue-router 的 useRoute / useRouter
 *   - 渲染详情页容器 .page-resume-detail
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: 'r1' } }),
  useRouter: () => ({ push: vi.fn() }),
}))

const detailMock = {
  resume_id: 'r1',
  candidate_id: 'c1',
  name: '张三',
  gender: '男',
  age: 28,
  education: '本科',
  education_level: 1,
  work_years: 5,
  skills: ['Vue', 'TypeScript'],
  expected_salary: { min: 20, max: 30 },
  tags: ['前端'],
  is_favorite: false,
  parse_status: 'completed' as const,
  location: '上海',
  created_at: '2026-06-01',
  basic_info: {
    name: '张三',
    phone: '13800138000',
    email: 'zhangsan@test.com',
    phone_masked: '138****8888',
    email_masked: 'a**@x.com',
    gender: '男',
    age: 28,
    location: '上海',
  },
  work_experience: [],
  education_detail: [],
  projects: [
    {
      name: 'HR 招聘系统',
      role: '前端负责人',
      description: '基于 Vue3 + FastAPI 的招聘管理平台，负责简历解析与检索模块。',
    },
  ],
  summary: '5 年前端经验，精通 Vue 全家桶。',
  file_info: { file_name: 'resume.pdf', file_type: 'pdf' },
  parse_info: { parse_status: 'completed' },
  notes: '',
}

vi.mock('@/api/resume', () => ({
  getResumeDetail: vi.fn(() => Promise.resolve(detailMock)),
  getPreviewUrl: vi.fn(() =>
    Promise.resolve({
      preview_url: 'http://example.com/r1.pdf',
      file_type: 'pdf',
      expires_in: 3600,
    }),
  ),
  toggleFavorite: vi.fn(() => Promise.resolve()),
  updateNotes: vi.fn(() => Promise.resolve()),
  updateTags: vi.fn(() => Promise.resolve()),
  uploadResume: vi.fn(),
  getResumeList: vi.fn(),
  deleteResume: vi.fn(),
  exportExcel: vi.fn(),
}))

import ResumeDetail from '@/views/ResumeDetail.vue'
import {
  getResumeDetail,
  getPreviewUrl,
  toggleFavorite,
  updateNotes,
  updateTags,
} from '@/api/resume'
import { useAuthStore } from '@/stores/auth'

describe('views/ResumeDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('渲染详情页容器 .page-resume-detail', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    expect(wrapper.find('.page-resume-detail').exists()).toBe(true)
  })

  it('加载详情后渲染候选人姓名', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    expect(wrapper.find('.detail-card__name').text()).toBe('张三')
  })

  it('渲染工作经历/教育经历/技能/备注等分区', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    const titles = wrapper.findAll('.detail-card__section-title').map((n) => n.text())
    expect(titles).toContain('技能标签')
    expect(titles).toContain('我的备注')
    expect(titles).toContain('简历预览')
    expect(titles).toContain('标签管理')
    expect(titles).toContain('操作')
  })

  it('渲染摘要区域（含引号装饰）', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    expect(wrapper.find('.detail-card__summary').exists()).toBe(true)
    expect(wrapper.find('.detail-card__summary-text').text()).toContain('5 年前端经验')
  })

  it('渲染项目经历分区（名称/角色/描述）', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    const titles = wrapper.findAll('.detail-card__section-title').map((n) => n.text())
    expect(titles).toContain('项目经历')
    expect(wrapper.find('.detail-card__work-company').text()).toBe('HR 招聘系统')
    expect(wrapper.find('.detail-card__work-position').text()).toBe('前端负责人')
    expect(wrapper.find('.detail-card__work-desc').text()).toContain('Vue3 + FastAPI')
  })

  it('详情页优先显示原始手机和邮箱（admin 可见）', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    const contactText = wrapper.find('.detail-card__contact').text()
    expect(contactText).toContain('13800138000')
    expect(contactText).toContain('zhangsan@test.com')
  })

  // ===== 以下为补充用例：覆盖收藏/备注/标签/预览/脱敏/解析失败 =====

  it('点击收藏按钮触发 toggleFavorite 调用', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    // 初始 is_favorite=false，按钮文案为"收藏"
    const favBtn = wrapper
      .findAll('button')
      .find((b) => /收藏/.test(b.text() || ''))
    expect(favBtn).toBeTruthy()
    await favBtn!.trigger('click')
    await flushPromises()
    expect(toggleFavorite).toHaveBeenCalledWith('r1', true)
  })

  it('编辑备注后失焦保存触发 updateNotes 调用', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    // 找到备注 textarea（页面内唯一 textarea）
    const textarea = wrapper.find('textarea')
    expect(textarea.exists()).toBe(true)
    await textarea.setValue('该候选人技术扎实，推荐进入下一轮')
    await textarea.trigger('blur')
    await flushPromises()
    expect(updateNotes).toHaveBeenCalledWith('r1', '该候选人技术扎实，推荐进入下一轮')
  })

  it('添加标签触发 updateTags 调用', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    // 找到 TagInput 组件并触发 update:modelValue
    const tagInput = wrapper.findComponent({ name: 'TagInput' })
    expect(tagInput.exists()).toBe(true)
    await tagInput.vm.$emit('update:modelValue', ['前端', '高潜'])
    await flushPromises()
    expect(updateTags).toHaveBeenCalledWith('r1', ['前端', '高潜'])
  })

  it('挂载时触发 getPreviewUrl 调用并渲染预览 iframe', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    expect(getPreviewUrl).toHaveBeenCalledWith('r1')
    // PDF 类型渲染 iframe，src 为返回的预览地址
    const frame = wrapper.find('.resume-preview__frame')
    expect(frame.exists()).toBe(true)
    expect(frame.attributes('src')).toBe('http://example.com/r1.pdf')
  })

  it('非 admin 用户看到脱敏联系方式', async () => {
    // 设置 authStore user.role='hr'，模拟非 admin 用户
    const authStore = useAuthStore()
    authStore.setUser({
      user_id: 'u2',
      username: 'hr_user',
      role: 'hr',
    })
    expect(authStore.user?.role).toBe('hr')
    // 后端对非 admin 用户仅返回脱敏字段（无原始 phone/email）
    vi.mocked(getResumeDetail).mockResolvedValueOnce({
      ...detailMock,
      basic_info: {
        name: '张三',
        phone_masked: '138****8888',
        email_masked: 'z***@x.com',
        gender: '男',
        age: 28,
        location: '上海',
      },
    })
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    const contactText = wrapper.find('.detail-card__contact').text()
    expect(contactText).toContain('138****8888')
    expect(contactText).toContain('z***@x.com')
    expect(contactText).not.toContain('13800138000')
  })

  it('parse_status 为 failed 时仍能正常展示候选人信息', async () => {
    vi.mocked(getResumeDetail).mockResolvedValueOnce({
      ...detailMock,
      parse_status: 'failed' as const,
      parse_info: { parse_status: 'failed' },
    })
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    // 页面正常渲染，不崩溃
    expect(wrapper.find('.page-resume-detail').exists()).toBe(true)
    expect(wrapper.find('.detail-card__name').text()).toBe('张三')
    // 摘要等区域仍可展示
    expect(wrapper.find('.detail-card__summary').exists()).toBe(true)
  })
})
