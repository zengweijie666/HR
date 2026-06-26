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
    phone_masked: '138****8888',
    email_masked: 'a**@x.com',
    gender: '男',
    age: 28,
    location: '上海',
  },
  work_experience: [],
  education_detail: [],
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

describe('views/ResumeDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
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
})
