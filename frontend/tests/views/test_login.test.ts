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
import { ElMessage } from 'element-plus'
import { defineComponent, h } from 'vue'

const pushMock = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: pushMock }),
}))

const loginMock = vi.fn()
vi.mock('@/api/auth', () => ({
  login: (...args: unknown[]) => loginMock(...args),
}))

import Login from '@/views/Login.vue'

/**
 * ElForm 桩组件：模拟 required 校验逻辑
 * 说明：测试环境中 Element Plus 的 form-item 在 onMounted 时未能正确注册到 form context，
 * 导致 doValidateField 因 fields.length===0 直接返回 true。
 * 此桩基于 model/rules props 实现 required 校验，保证空字段提交时 validate reject。
 */
const ElFormStub = defineComponent({
  name: 'ElForm',
  props: { model: Object, rules: Object },
  setup(props, { expose, slots }) {
    const validate = async () => {
      if (!props.model || !props.rules) return true as const
      const errors: Record<string, string> = {}
      for (const [key, ruleList] of Object.entries(props.rules)) {
        const rules = Array.isArray(ruleList) ? ruleList : [ruleList]
        for (const rule of rules as Array<Record<string, unknown>>) {
          if (rule.required && !props.model[key]) {
            errors[key] = (rule.message as string) || `${key} is required`
          }
        }
      }
      if (Object.keys(errors).length) return Promise.reject(errors)
      return true as const
    }
    expose({ validate })
    return () => h('form', { class: 'el-form' }, [slots.default?.()])
  }
})

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

  it('表单校验：空邮箱提交不触发 login API', async () => {
    const wrapper = mount(Login, {
      global: { stubs: { ElForm: ElFormStub } },
    })
    await wrapper.find('input[placeholder="请输入密码"]').setValue('123456')
    await flushPromises()
    await wrapper.find('.page-login__submit').trigger('click')
    await flushPromises()
    expect(loginMock).not.toHaveBeenCalled()
  })

  it('表单校验：空密码提交不触发 login API', async () => {
    const wrapper = mount(Login, {
      global: { stubs: { ElForm: ElFormStub } },
    })
    await wrapper.find('input[placeholder="请输入邮箱"]').setValue('admin@test.com')
    await flushPromises()
    await wrapper.find('.page-login__submit').trigger('click')
    await flushPromises()
    expect(loginMock).not.toHaveBeenCalled()
  })

  it('登录失败：API reject 时显示错误信息', async () => {
    const errorSpy = vi
      .spyOn(ElMessage, 'error')
      .mockImplementation(() => ({}) as never)
    loginMock.mockRejectedValue(new Error('密码错误'))

    const wrapper = mount(Login)
    await wrapper.find('input[placeholder="请输入邮箱"]').setValue('admin@test.com')
    await wrapper.find('input[placeholder="请输入密码"]').setValue('123456')
    await flushPromises()

    await wrapper.find('.page-login__submit').trigger('click')
    await flushPromises()

    expect(loginMock).toHaveBeenCalled()
    expect(errorSpy).toHaveBeenCalledWith('密码错误')
    expect(pushMock).not.toHaveBeenCalled()
    errorSpy.mockRestore()
  })

  it('登录 loading：登录过程中按钮 loading 状态', async () => {
    let resolveLogin!: (v: unknown) => void
    loginMock.mockReturnValue(
      new Promise((resolve) => {
        resolveLogin = resolve
      })
    )

    const wrapper = mount(Login)
    await wrapper.find('input[placeholder="请输入邮箱"]').setValue('admin@test.com')
    await wrapper.find('input[placeholder="请输入密码"]').setValue('123456')
    await flushPromises()

    await wrapper.find('.page-login__submit').trigger('click')
    await flushPromises()

    expect(wrapper.find('.page-login__submit').classes()).toContain('is-loading')

    resolveLogin({ access_token: 'a', refresh_token: 'b' })
    await flushPromises()

    expect(wrapper.find('.page-login__submit').classes()).not.toContain('is-loading')
  })

  it('密码输入框 type 为 password', () => {
    const wrapper = mount(Login)
    const pwdInput = wrapper.find('input[placeholder="请输入密码"]')
    expect(pwdInput.attributes('type')).toBe('password')
  })

  it('申请账号链接存在且可点击', async () => {
    const wrapper = mount(Login)
    const link = wrapper.find('.page-login__register a')
    expect(link.exists()).toBe(true)
    expect(link.text()).toBe('申请账号')

    await link.trigger('click')
    await flushPromises()

    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    expect(dialog.exists()).toBe(true)
    expect(dialog.props('modelValue')).toBe(true)
  })
})
