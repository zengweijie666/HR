/**
 * 文件名: tests/views/test_settings.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 设置页测试
 *   - mock @/api/email 的 getConfig / updateConfig
 *   - 渲染设置容器 .page-settings
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { ElMessage } from 'element-plus'

vi.mock('@/api/email', () => ({
  getConfig: vi.fn(() =>
    Promise.resolve({
      smtp_host: 'smtp.example.com',
      smtp_port: 465,
      smtp_user: 'hr@example.com',
    }),
  ),
  updateConfig: vi.fn(() => Promise.resolve({
    smtp_host: 'smtp.example.com',
    smtp_port: 465,
    smtp_user: 'hr@example.com',
  })),
}))

import Settings from '@/views/Settings.vue'
import { updateConfig } from '@/api/email'

describe('views/Settings', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('渲染设置容器 .page-settings', async () => {
    const wrapper = mount(Settings)
    await flushPromises()
    expect(wrapper.find('.page-settings').exists()).toBe(true)
  })

  it('渲染页头标题 "设置"', async () => {
    const wrapper = mount(Settings)
    await flushPromises()
    expect(wrapper.find('.page-settings__title').text()).toBe('设置')
  })

  it('渲染邮件配置卡片 .settings-card', async () => {
    const wrapper = mount(Settings)
    await flushPromises()
    expect(wrapper.find('.settings-card').exists()).toBe(true)
    expect(wrapper.find('.settings-card__title').text()).toContain('邮件服务器')
  })

  it('加载配置后回填 SMTP 主机', async () => {
    const wrapper = mount(Settings)
    await flushPromises()
    const hostInput = wrapper.find('input[placeholder*="smtp.qq.com"]')
    expect((hostInput.element as HTMLInputElement).value).toBe('smtp.example.com')
  })

  it('渲染保存按钮', async () => {
    const wrapper = mount(Settings)
    await flushPromises()
    const btn = wrapper.findAll('button').find((b) => /保存配置/.test(b.text() || ''))
    expect(btn).toBeTruthy()
  })

  // ===== 以下为补充用例：保存触发/成功提示/错误提示/字段回填/loading/校验 =====

  it('点击保存按钮触发 updateConfig API 调用', async () => {
    const wrapper = mount(Settings)
    await flushPromises()
    const saveBtn = wrapper.findAll('button').find((b) => /保存配置/.test(b.text() || ''))
    await saveBtn!.trigger('click')
    await flushPromises()
    expect(updateConfig).toHaveBeenCalled()
    expect(updateConfig).toHaveBeenCalledWith(
      expect.objectContaining({
        smtp_host: 'smtp.example.com',
        smtp_port: 465,
        smtp_user: 'hr@example.com',
        use_ssl: true,
      }),
    )
  })

  it('保存成功后显示成功提示', async () => {
    const successSpy = vi.spyOn(ElMessage, 'success').mockImplementation(() => ({}) as never)
    const wrapper = mount(Settings)
    await flushPromises()
    const saveBtn = wrapper.findAll('button').find((b) => /保存配置/.test(b.text() || ''))
    await saveBtn!.trigger('click')
    await flushPromises()
    expect(successSpy).toHaveBeenCalledWith('配置已保存')
    successSpy.mockRestore()
  })

  it('保存失败时显示错误提示', async () => {
    const errorSpy = vi.spyOn(ElMessage, 'error').mockImplementation(() => ({}) as never)
    vi.mocked(updateConfig).mockRejectedValueOnce(new Error('保存失败'))
    const wrapper = mount(Settings)
    await flushPromises()
    const saveBtn = wrapper.findAll('button').find((b) => /保存配置/.test(b.text() || ''))
    await saveBtn!.trigger('click')
    await flushPromises()
    expect(errorSpy).toHaveBeenCalledWith('保存失败')
    errorSpy.mockRestore()
  })

  it('加载配置后回填端口/用户名/加密方式', async () => {
    const wrapper = mount(Settings)
    await flushPromises()
    // 端口（el-input-number 的 input）
    const portInput = wrapper.find('.el-input-number input')
    expect((portInput.element as HTMLInputElement).value).toBe('465')
    // 用户名
    const userInput = wrapper.find('input[placeholder*="hr@company.com"]')
    expect((userInput.element as HTMLInputElement).value).toBe('hr@example.com')
    // 加密方式 use_ssl=true（端口 465）→ SSL/TLS 单选项选中
    const radios = wrapper.findAll('.el-radio')
    expect(radios.length).toBeGreaterThanOrEqual(2)
    expect(radios[0].classes()).toContain('is-checked')
  })

  it('保存过程中按钮显示 loading 状态', async () => {
    let resolveSave!: (v: unknown) => void
    vi.mocked(updateConfig).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveSave = resolve as (v: unknown) => void
      }),
    )
    const wrapper = mount(Settings)
    await flushPromises()
    const saveBtn = wrapper.findAll('button').find((b) => /保存配置/.test(b.text() || ''))
    await saveBtn!.trigger('click')
    await flushPromises()
    expect(saveBtn!.classes()).toContain('is-loading')
    resolveSave({ smtp_host: 'smtp.example.com', smtp_port: 465, smtp_user: 'hr@example.com' })
    await flushPromises()
    expect(saveBtn!.classes()).not.toContain('is-loading')
  })

  it('表单校验：空主机名时不触发 updateConfig', async () => {
    const warningSpy = vi.spyOn(ElMessage, 'warning').mockImplementation(() => ({}) as never)
    const wrapper = mount(Settings)
    await flushPromises()
    const hostInput = wrapper.find('input[placeholder*="smtp.qq.com"]')
    await hostInput.setValue('')
    const saveBtn = wrapper.findAll('button').find((b) => /保存配置/.test(b.text() || ''))
    await saveBtn!.trigger('click')
    await flushPromises()
    expect(updateConfig).not.toHaveBeenCalled()
    expect(warningSpy).toHaveBeenCalledWith('请填写 SMTP 主机')
    warningSpy.mockRestore()
  })
})
