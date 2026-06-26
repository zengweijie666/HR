/**
 * 文件名: tests/views/test_layout.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 主布局测试
 *   - mock vue-router（useRoute / useRouter）
 *   - 渲染侧边栏 .sidebar 与顶栏 .header
 *   - 折叠按钮 .collapse-btn 点击切换折叠态
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

const pushMock = vi.fn()
vi.mock('vue-router', () => ({
  useRoute: () => ({
    path: '/workbench',
    meta: { title: '工作台' },
    startsWith: () => false,
  }),
  useRouter: () => ({ push: pushMock }),
}))

import Layout from '@/views/Layout.vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

/** mount 选项：stub 掉 router-view 避免 vue-router 缺失警告 */
const mountOptions = {
  global: {
    stubs: {
      'router-view': true,
    },
  },
}

describe('views/Layout', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    pushMock.mockClear()
  })

  it('渲染侧边栏与顶栏', () => {
    const wrapper = mount(Layout, mountOptions)
    expect(wrapper.find('.sidebar').exists()).toBe(true)
    expect(wrapper.find('.header').exists()).toBe(true)
  })

  it('渲染折叠按钮 .collapse-btn', () => {
    const wrapper = mount(Layout, mountOptions)
    expect(wrapper.find('.collapse-btn').exists()).toBe(true)
  })

  it('点击折叠按钮切换 sidebarCollapsed 状态', async () => {
    const app = useAppStore()
    expect(app.sidebarCollapsed).toBe(false)
    const wrapper = mount(Layout, mountOptions)
    await wrapper.find('.collapse-btn').trigger('click')
    expect(app.sidebarCollapsed).toBe(true)
    // 再次点击恢复
    await wrapper.find('.collapse-btn').trigger('click')
    expect(app.sidebarCollapsed).toBe(false)
  })

  it('侧边栏菜单包含工作台/简历库/JD 匹配/数据看板/设置', () => {
    const wrapper = mount(Layout, mountOptions)
    const text = wrapper.find('.sidebar').text()
    expect(text).toContain('工作台')
    expect(text).toContain('简历库')
    expect(text).toContain('JD 匹配')
    expect(text).toContain('数据看板')
    expect(text).toContain('设置')
  })

  it('未登录用户顶栏显示 "未登录"', () => {
    const auth = useAuthStore()
    auth.logout()
    const wrapper = mount(Layout, mountOptions)
    expect(wrapper.find('.header__username').text()).toBe('未登录')
  })
})
