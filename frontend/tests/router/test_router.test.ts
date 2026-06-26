/**
 * 文件名: tests/router/test_router.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 测试路由守卫
 *   - 已登录访问 / 重定向到 /workbench
 *   - 未登录访问 / 跳转 /login
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

describe('router', () => {
  beforeEach(async () => {
    localStorage.clear()
    setActivePinia(createPinia())
    // 重置到公开登录页，避免上一轮路由残留导致重复导航短路
    await router.push('/login').catch(() => {})
  })

  it('已登录访问 / 重定向到 /workbench', async () => {
    const auth = useAuthStore()
    auth.setToken('token', 'refresh')
    await router.push('/')
    expect(router.currentRoute.value.path).toBe('/workbench')
  })

  it('未登录访问 / 跳转 /login', async () => {
    await router.push('/')
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('已登录访问未知路径重定向到 /workbench', async () => {
    const auth = useAuthStore()
    auth.setToken('token', 'refresh')
    await router.push('/some/unknown/path')
    expect(router.currentRoute.value.path).toBe('/workbench')
  })
})
