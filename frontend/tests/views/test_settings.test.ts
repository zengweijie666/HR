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

describe('views/Settings', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
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
    const hostInput = wrapper.find('input[placeholder="如 smtp.example.com"]')
    expect((hostInput.element as HTMLInputElement).value).toBe('smtp.example.com')
  })

  it('渲染保存按钮', async () => {
    const wrapper = mount(Settings)
    await flushPromises()
    const btn = wrapper.findAll('button').find((b) => /保存配置/.test(b.text() || ''))
    expect(btn).toBeTruthy()
  })
})
