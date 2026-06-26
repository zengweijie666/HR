/**
 * 文件名: stores/resume.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 简历列表状态管理（Composition API 风格）
 *   - list 简历列表 / total 总数 / filters 查询条件
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ResumeListItem, ResumeListQuery } from '@/types/resume'

export const useResumeStore = defineStore('resume', () => {
  /** 简历列表 */
  const list = ref<ResumeListItem[]>([])
  /** 总数 */
  const total = ref<number>(0)
  /** 当前查询条件 */
  const filters = ref<ResumeListQuery>({})

  /**
   * 设置列表
   * @param l 简历数组
   */
  function setList(l: ResumeListItem[]): void {
    list.value = l
  }

  /**
   * 设置总数
   * @param t 总数
   */
  function setTotal(t: number): void {
    total.value = t
  }

  /**
   * 合并查询条件
   * @param f 待合并的筛选字段
   */
  function setFilters(f: Partial<ResumeListQuery>): void {
    filters.value = { ...filters.value, ...f }
  }

  /** 重置查询条件 */
  function resetFilters(): void {
    filters.value = {}
  }

  /**
   * 更新单条简历的收藏状态
   * @param id 简历 ID
   * @param isFav 是否收藏
   */
  function updateFavorite(id: string, isFav: boolean): void {
    const item = list.value.find((i) => i.resume_id === id)
    if (item) item.is_favorite = isFav
  }

  /**
   * 更新单条简历的标签
   * @param id 简历 ID
   * @param tags 标签数组
   */
  function updateTags(id: string, tags: string[]): void {
    const item = list.value.find((i) => i.resume_id === id)
    if (item) item.tags = tags
  }

  /**
   * 更新单条简历（存在则替换，不存在则追加）
   * @param item 简历项
   */
  function updateOne(item: ResumeListItem): void {
    const idx = list.value.findIndex((i) => i.resume_id === item.resume_id)
    if (idx !== -1) {
      list.value[idx] = item
    } else {
      list.value.push(item)
    }
  }

  return {
    list,
    total,
    filters,
    setList,
    setTotal,
    setFilters,
    resetFilters,
    updateFavorite,
    updateTags,
    updateOne,
  }
})
