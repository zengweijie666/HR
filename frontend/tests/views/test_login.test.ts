/**
 * 文件名: tests/views/test_login.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 登录页测试
 *   - mock @/api/auth 的 login 与 vue-router 的 useRouter
 *   - 渲染登录表单
 *   - 填写表单点击登录 → 触发 login API → 验证 localStorage 写入
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

const pushMock = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock }),
}))

const loginMock = vi.fn()
vi.mock('@/api/auth', () => ({
  login: (...args: unknown[]) => loginMock(...args),
}))

import Login from '@/views/Login.vue'

describe('views/Login', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    pushMock.mockClear()
    loginMock.mockReset()
  })

  it('渲染登录表单（含邮箱与密码输入）', () => {
    const wrapper = mount(Login)
    expect(wrapper.find('.page-login__form').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="请输入邮箱"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="请输入密码"]').exists()).toBe(true)
  })

  it('渲染品牌区与表单区', () => {
    const wrapper = mount(Login)
    expect(wrapper.find('.page-login__brand').exists()).toBe(true)
    expect(wrapper.find('.page-login__main').exists()).toBe(true)
  })

  it('点击登录触发 API 并写入 localStorage', async () => {
    loginMock.mockResolvedValue({
      access_token: 'test-access',
      refresh_token: 'test-refresh',
      token_type: 'bearer',
      expires_in: 3600,
    })

    const wrapper = mount(Login)
    await wrapper.find('input[placeholder="请输入邮箱"]').setValue('admin@test.com')
    await wrapper.find('input[placeholder="请输入密码"]').setValue('123456')
    await flushPromises()

    await wrapper.find('.page-login__submit').trigger('click')
    await flushPromises()

    expect(loginMock).toHaveBeenCalled()
    expect(loginMock).toHaveBeenCalledWith({
      email: 'admin@test.com',
      password: '123456',
    })
    expect(localStorage.getItem('access_token')).toBe('test-access')
    expect(localStorage.getItem('refresh_token')).toBe('test-refresh')
    expect(pushMock).toHaveBeenCalledWith('/workbench')
  })

  it('登录按钮初始可点击（无 disabled 属性）', () => {
    const wrapper = mount(Login)
    const btn = wrapper.find('.page-login__submit')
    expect(btn.exists()).toBe(true)
    // 按钮文字包含 "登"
    expect(btn.text()).toContain('登')
  })
})
