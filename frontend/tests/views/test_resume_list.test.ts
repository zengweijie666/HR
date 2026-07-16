/**
 * 文件名: tests/views/test_resume_list.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 简历列表页测试
 *   - mock @/api/resume 的 getResumeList / toggleFavorite / exportExcel / uploadResume
 *   - mock vue-router 的 useRouter
 *   - 渲染筛选条 FilterBar 与上传按钮 .upload-btn
 *   - 点击 .upload-btn 显示上传弹窗
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('@/api/resume', () => ({
  getResumeList: vi.fn(() =>
    Promise.resolve({
      list: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0,
    }),
  ),
  uploadResume: vi.fn(() =>
    Promise.resolve({
      resume_id: 'r1',
      candidate_id: 'c1',
      file_name: 'a.pdf',
      parse_status: 'pending',
      is_duplicate: false,
      duplicate_with: null,
    }),
  ),
  toggleFavorite: vi.fn(() => Promise.resolve()),
  exportExcel: vi.fn(() => Promise.resolve(new Blob(['x'], { type: 'application/vnd.ms-excel' }))),
  getResumeDetail: vi.fn(),
  getPreviewUrl: vi.fn(),
  deleteResume: vi.fn(),
  updateTags: vi.fn(),
  updateNotes: vi.fn(),
}))

vi.mock('@/api/email', () => ({
  listTemplates: vi.fn(() => Promise.resolve([])),
  sendMail: vi.fn(() => Promise.resolve({ status: 'success', message: 'ok' })),
}))

vi.mock('@/api/candidate', () => ({
  exportExcel: vi.fn(() =>
    Promise.resolve(new Blob(['x'], { type: 'application/vnd.ms-excel' })),
  ),
  getSimilar: vi.fn(() => Promise.resolve([])),
  compare: vi.fn(() => Promise.resolve({ candidates: [], dimensions: [] })),
}))

vi.mock('@/utils/download', () => ({
  downloadBlob: vi.fn(),
  defaultFilename: vi.fn(() => 'resumes.xlsx'),
}))

import ResumeList from '@/views/ResumeList.vue'
import { ElMessageBox } from 'element-plus'
import { getResumeList, toggleFavorite, deleteResume } from '@/api/resume'
import { exportExcel } from '@/api/candidate'

describe('views/ResumeList', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('渲染筛选条与上传按钮', async () => {
    const wrapper = mount(ResumeList)
    await flushPromises()
    expect(wrapper.find('.filter-bar').exists()).toBe(true)
    expect(wrapper.find('.upload-btn').exists()).toBe(true)
  })

  it('渲染页头标题 "简历库"', async () => {
    const wrapper = mount(ResumeList)
    await flushPromises()
    expect(wrapper.find('.page-resume-list__title').text()).toBe('简历库')
  })

  it('点击 .upload-btn 显示上传弹窗', async () => {
    const wrapper = mount(ResumeList)
    await flushPromises()
    // 初始无弹窗
    expect(document.body.querySelector('.upload-dialog')).toBeNull()
    await wrapper.find('.upload-btn').trigger('click')
    await flushPromises()
    // 弹窗出现（el-dialog 默认 teleport 到 body）
    expect(document.body.querySelector('.upload-dialog')).not.toBeNull()
  })

  it('无数据时渲染 EmptyState 提示', async () => {
    const wrapper = mount(ResumeList)
    await flushPromises()
    expect(wrapper.text()).toContain('暂无简历，点击上传')
  })

  it('渲染列表总数统计文案', async () => {
    const wrapper = mount(ResumeList)
    await flushPromises()
    expect(wrapper.find('.page-resume-list__stats').exists()).toBe(true)
  })

  // ===== 以下为补充用例：覆盖列表/分页/收藏/导出/删除/加载 =====

  it('加载并渲染多份简历卡片', async () => {
    vi.mocked(getResumeList).mockResolvedValueOnce({
      list: [
        {
          resume_id: 'r1',
          candidate_id: 'c1',
          name: '张三',
          gender: '男',
          age: 28,
          education: '本科',
          education_level: 1,
          work_years: 5,
          skills: ['Vue'],
          expected_salary: { min: 20, max: 30 },
          tags: [],
          is_favorite: false,
          parse_status: 'completed',
          location: '上海',
          created_at: '2026-06-01',
        },
        {
          resume_id: 'r2',
          candidate_id: 'c2',
          name: '李四',
          gender: '女',
          age: 25,
          education: '硕士',
          education_level: 2,
          work_years: 3,
          skills: ['React'],
          expected_salary: { min: 25, max: 35 },
          tags: [],
          is_favorite: false,
          parse_status: 'completed',
          location: '北京',
          created_at: '2026-06-02',
        },
        {
          resume_id: 'r3',
          candidate_id: 'c3',
          name: '王五',
          gender: '男',
          age: 30,
          education: '博士',
          education_level: 3,
          work_years: 8,
          skills: ['Java'],
          expected_salary: { min: 30, max: 50 },
          tags: [],
          is_favorite: false,
          parse_status: 'completed',
          location: '深圳',
          created_at: '2026-06-03',
        },
      ],
      total: 3,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    const wrapper = mount(ResumeList)
    await flushPromises()
    const cards = wrapper.findAll('.resume-card')
    expect(cards).toHaveLength(3)
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('李四')
    expect(wrapper.text()).toContain('王五')
  })

  it('总数大于 pageSize 时渲染分页器', async () => {
    vi.mocked(getResumeList).mockResolvedValueOnce({
      list: Array.from({ length: 20 }, (_, i) => ({
        resume_id: `r${i}`,
        candidate_id: `c${i}`,
        name: `用户${i}`,
        education: '本科',
        education_level: 1,
        work_years: 1,
        skills: [],
        expected_salary: { min: 10, max: 20 },
        tags: [],
        is_favorite: false,
        parse_status: 'completed' as const,
        created_at: '2026-06-01',
      })),
      total: 50,
      page: 1,
      page_size: 20,
      total_pages: 3,
    })
    const wrapper = mount(ResumeList)
    await flushPromises()
    expect(wrapper.find('.el-pagination').exists()).toBe(true)
  })

  it('点击收藏按钮调用 toggleFavorite', async () => {
    vi.mocked(getResumeList).mockResolvedValueOnce({
      list: [
        {
          resume_id: 'r1',
          candidate_id: 'c1',
          name: '张三',
          education: '本科',
          education_level: 1,
          work_years: 5,
          skills: ['Vue'],
          expected_salary: { min: 20, max: 30 },
          tags: [],
          is_favorite: false,
          parse_status: 'completed' as const,
          created_at: '2026-06-01',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    vi.mocked(toggleFavorite).mockResolvedValueOnce(undefined)
    const wrapper = mount(ResumeList)
    await flushPromises()
    await wrapper.find('.resume-card__fav').trigger('click')
    await flushPromises()
    expect(toggleFavorite).toHaveBeenCalledWith('r1', true)
  })

  it('选中简历后点击导出按钮调用 exportExcel', async () => {
    vi.mocked(getResumeList).mockResolvedValueOnce({
      list: [
        {
          resume_id: 'r1',
          candidate_id: 'c1',
          name: '张三',
          education: '本科',
          education_level: 1,
          work_years: 5,
          skills: ['Vue'],
          expected_salary: { min: 20, max: 30 },
          tags: [],
          is_favorite: false,
          parse_status: 'completed' as const,
          created_at: '2026-06-01',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    vi.mocked(exportExcel).mockResolvedValueOnce(
      new Blob(['x'], { type: 'application/vnd.ms-excel' }),
    )
    const wrapper = mount(ResumeList)
    await flushPromises()
    // 选中第一个简历：通过 ElCheckbox 组件触发 v-model 更新与 change 事件
    const checkboxComp = wrapper.findComponent({ name: 'ElCheckbox' })
    expect(checkboxComp.exists()).toBe(true)
    await checkboxComp.setValue(true)
    checkboxComp.vm.$emit('change', true)
    await flushPromises()
    // 点击导出按钮
    const exportBtn = wrapper
      .findAll('button')
      .find((b) => /导出选中/.test(b.text() || ''))
    expect(exportBtn).toBeTruthy()
    await exportBtn!.trigger('click')
    await flushPromises()
    expect(exportExcel).toHaveBeenCalled()
    expect(exportExcel.mock.calls[0][0]).toMatchObject({
      resume_ids: ['r1'],
    })
  })

  it('点击删除按钮并在确认后调用 deleteResume', async () => {
    vi.mocked(getResumeList).mockResolvedValueOnce({
      list: [
        {
          resume_id: 'r1',
          candidate_id: 'c1',
          name: '张三',
          education: '本科',
          education_level: 1,
          work_years: 5,
          skills: ['Vue'],
          expected_salary: { min: 20, max: 30 },
          tags: [],
          is_favorite: false,
          parse_status: 'completed' as const,
          created_at: '2026-06-01',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    vi.mocked(deleteResume).mockResolvedValueOnce(undefined)
    // mock ElMessageBox.confirm 返回 confirm（模拟用户点击确认）
    const confirmSpy = vi
      .spyOn(ElMessageBox, 'confirm')
      .mockResolvedValue('confirm' as never)
    const wrapper = mount(ResumeList)
    await flushPromises()
    await wrapper.find('.resume-card__del').trigger('click')
    await flushPromises()
    expect(deleteResume).toHaveBeenCalledWith('r1')
    confirmSpy.mockRestore()
  })

  it('加载列表时显示 loading 遮罩', async () => {
    let resolveList!: (v: unknown) => void
    vi.mocked(getResumeList).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveList = resolve as (v: unknown) => void
      }),
    )
    const wrapper = mount(ResumeList)
    await flushPromises()
    // loading 中应显示遮罩
    expect(wrapper.find('.loading-overlay').exists()).toBe(true)
    // 解析后遮罩消失
    resolveList({ list: [], total: 0, page: 1, page_size: 20, total_pages: 0 })
    await flushPromises()
    expect(wrapper.find('.loading-overlay').exists()).toBe(false)
  })

  it('总数统计文案显示具体总数', async () => {
    vi.mocked(getResumeList).mockResolvedValueOnce({
      list: Array.from({ length: 5 }, (_, i) => ({
        resume_id: `r${i}`,
        candidate_id: `c${i}`,
        name: `用户${i}`,
        education: '本科',
        education_level: 1,
        work_years: 1,
        skills: [],
        expected_salary: { min: 10, max: 20 },
        tags: [],
        is_favorite: false,
        parse_status: 'completed' as const,
        created_at: '2026-06-01',
      })),
      total: 5,
      page: 1,
      page_size: 20,
      total_pages: 1,
    })
    const wrapper = mount(ResumeList)
    await flushPromises()
    const statsText = wrapper.find('.page-resume-list__stats').text()
    expect(statsText).toContain('共')
    expect(statsText).toContain('5')
    expect(statsText).toContain('份')
  })
})
