/**
 * 文件名: stores/app.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 应用全局状态（侧边栏/加载/主题）
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

/** 主题类型 */
export type Theme = 'light' | 'dark'

export const useAppStore = defineStore('app', () => {
  /** 侧边栏是否折叠 */
  const sidebarCollapsed = ref<boolean>(false)
  /** 全局加载状态 */
  const loading = ref<boolean>(false)
  /** 当前主题，默认 light */
  const theme = ref<Theme>('light')

  /** 切换侧边栏折叠状态 */
  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  /**
   * 设置全局加载状态
   * @param v 是否加载中
   */
  function setLoading(v: boolean): void {
    loading.value = v
  }

  /**
   * 设置主题
   * @param t 主题名
   */
  function setTheme(t: Theme): void {
    theme.value = t
  }

  return { sidebarCollapsed, loading, theme, toggleSidebar, setLoading, setTheme }
})
