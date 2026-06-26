/**
 * 文件名: tests/stores/test_resume_store.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 测试 resume store 与 app store
 *   - setList
 *   - setFilters 合并
 *   - updateFavorite
 *   - app store toggleSidebar
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useResumeStore } from '@/stores/resume'
import { useAppStore } from '@/stores/app'
import type { ResumeListItem } from '@/types/resume'

function makeItem(id: string, fav: boolean): ResumeListItem {
  return {
    resume_id: id,
    candidate_id: 'c' + id,
    name: '候选人' + id,
    education: '本科',
    education_level: 1,
    work_years: 3,
    skills: [],
    expected_salary: { min: 10, max: 20 },
    tags: [],
    is_favorite: fav,
    parse_status: 'completed',
    created_at: '',
  }
}

describe('stores/resume', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('setList 设置列表', () => {
    const store = useResumeStore()
    store.setList([makeItem('r1', false)])
    expect(store.list).toHaveLength(1)
    expect(store.list[0].resume_id).toBe('r1')
  })

  it('setFilters 合并筛选条件', () => {
    const store = useResumeStore()
    store.setFilters({ keyword: 'java' })
    store.setFilters({ work_years_min: 3 })
    expect(store.filters.keyword).toBe('java')
    expect(store.filters.work_years_min).toBe(3)
  })

  it('resetFilters 清空筛选条件', () => {
    const store = useResumeStore()
    store.setFilters({ keyword: 'java' })
    store.resetFilters()
    expect(store.filters).toEqual({})
  })

  it('updateFavorite 更新收藏状态', () => {
    const store = useResumeStore()
    store.setList([makeItem('r1', false)])
    store.updateFavorite('r1', true)
    expect(store.list[0].is_favorite).toBe(true)
  })

  it('updateTags 更新标签', () => {
    const store = useResumeStore()
    store.setList([makeItem('r1', false)])
    store.updateTags('r1', ['高优', 'Java'])
    expect(store.list[0].tags).toEqual(['高优', 'Java'])
  })
})

describe('stores/app', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('toggleSidebar 切换侧边栏折叠状态', () => {
    const app = useAppStore()
    expect(app.sidebarCollapsed).toBe(false)
    app.toggleSidebar()
    expect(app.sidebarCollapsed).toBe(true)
    app.toggleSidebar()
    expect(app.sidebarCollapsed).toBe(false)
  })

  it('setTheme 设置主题', () => {
    const app = useAppStore()
    expect(app.theme).toBe('light')
    app.setTheme('dark')
    expect(app.theme).toBe('dark')
  })
})
