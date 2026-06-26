/**
 * 文件名: stores/auth.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 认证状态管理（Composition API 风格）
 *   - token / refreshToken 持久化到 localStorage
 *   - user 当前用户信息
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types/auth'

/** localStorage 键名 */
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const useAuthStore = defineStore('auth', () => {
  /** 访问令牌，初始从 localStorage 读取 */
  const token = ref<string>(localStorage.getItem(ACCESS_TOKEN_KEY) || '')
  /** 刷新令牌 */
  const refreshToken = ref<string>(localStorage.getItem(REFRESH_TOKEN_KEY) || '')
  /** 当前用户信息 */
  const user = ref<UserInfo | null>(null)

  /** 是否已登录（token 非空） */
  const isLoggedIn = computed(() => !!token.value)

  /**
   * 设置 token 并持久化
   * @param access 访问令牌
   * @param refresh 刷新令牌
   */
  function setToken(access: string, refresh: string): void {
    token.value = access
    refreshToken.value = refresh
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  }

  /**
   * 设置当前用户信息
   * @param u 用户信息，传 null 清空
   */
  function setUser(u: UserInfo | null): void {
    user.value = u
  }

  /** 退出登录：清空内存与本地凭证 */
  function logout(): void {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  return { token, refreshToken, user, isLoggedIn, setToken, setUser, logout }
})
