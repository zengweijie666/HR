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

import ResumeList from '@/views/ResumeList.vue'

describe('views/ResumeList', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
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
})
