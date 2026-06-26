/**
 * 文件名: tests/stores/test_auth_store.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 测试 auth store
 *   - 初始未登录
 *   - setToken 持久化
 *   - setUser
 *   - logout 清空
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import type { UserInfo } from '@/types/auth'

describe('stores/auth', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('初始状态为未登录', () => {
    const auth = useAuthStore()
    expect(auth.isLoggedIn).toBe(false)
    expect(auth.token).toBe('')
    expect(auth.user).toBeNull()
  })

  it('setToken 持久化 token 到 localStorage', () => {
    const auth = useAuthStore()
    auth.setToken('access123', 'refresh456')
    expect(auth.token).toBe('access123')
    expect(auth.refreshToken).toBe('refresh456')
    expect(auth.isLoggedIn).toBe(true)
    expect(localStorage.getItem('access_token')).toBe('access123')
    expect(localStorage.getItem('refresh_token')).toBe('refresh456')
  })

  it('setUser 设置用户信息', () => {
    const auth = useAuthStore()
    const u: UserInfo = { user_id: 'u1', username: 'admin', role: 'hr', name: 'HR' }
    auth.setUser(u)
    expect(auth.user).toEqual(u)
  })

  it('logout 清空所有状态与本地凭证', () => {
    const auth = useAuthStore()
    auth.setToken('a', 'b')
    auth.setUser({ user_id: 'u', username: 'x', role: 'hr' })
    auth.logout()
    expect(auth.token).toBe('')
    expect(auth.refreshToken).toBe('')
    expect(auth.user).toBeNull()
    expect(auth.isLoggedIn).toBe(false)
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })
})
