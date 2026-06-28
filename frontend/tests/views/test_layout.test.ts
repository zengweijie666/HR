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
import { mount, flushPromises } from '@vue/test-utils'
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
    pushMock.mockReset()
    // el-menu 内部调用 router.push(route).then(...)，push 必须返回 Promise
    pushMock.mockResolvedValue(undefined)
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

  it('侧边栏菜单包含工作台/简历库/JD 匹配/邮件中心/数据看板/设置（admin）', () => {
    const auth = useAuthStore()
    auth.user = { user_id: 'u1', name: 'admin', email: 'admin@test.com', role: 'admin' } as never
    const wrapper = mount(Layout, mountOptions)
    const text = wrapper.find('.sidebar').text()
    expect(text).toContain('工作台')
    expect(text).toContain('简历库')
    expect(text).toContain('JD 匹配')
    expect(text).toContain('邮件中心')
    expect(text).toContain('数据看板')
    expect(text).toContain('设置')
  })

  it('未登录用户顶栏显示 "未登录"', () => {
    const auth = useAuthStore()
    auth.logout()
    const wrapper = mount(Layout, mountOptions)
    expect(wrapper.find('.header__username').text()).toBe('未登录')
  })

  it('hr 角色不显示设置菜单', () => {
    const auth = useAuthStore()
    auth.user = {
      user_id: 'u1',
      name: 'hr',
      username: 'hr',
      email: 'hr@test.com',
      role: 'hr',
    } as never
    const wrapper = mount(Layout, mountOptions)
    expect(wrapper.find('.sidebar').text()).not.toContain('设置')
  })

  it('hr 角色不显示用户管理菜单', () => {
    const auth = useAuthStore()
    auth.user = {
      user_id: 'u1',
      name: 'hr',
      username: 'hr',
      email: 'hr@test.com',
      role: 'hr',
    } as never
    const wrapper = mount(Layout, mountOptions)
    expect(wrapper.find('.sidebar').text()).not.toContain('用户管理')
  })

  it('点击菜单项触发路由跳转', async () => {
    const routerMountOptions = {
      global: {
        stubs: { 'router-view': true },
        config: {
          globalProperties: {
            $router: { push: pushMock },
          },
        },
      },
    }
    const wrapper = mount(Layout, routerMountOptions)
    const menuItems = wrapper.findAll('.el-menu-item')
    const resumeItem = menuItems.find((item) =>
      item.text().includes('简历库')
    )
    expect(resumeItem).toBeTruthy()
    await resumeItem!.trigger('click')
    await flushPromises()
    expect(pushMock).toHaveBeenCalledWith('/resumes')
  })

  it('顶栏显示已登录用户名', () => {
    const auth = useAuthStore()
    auth.user = {
      user_id: 'u1',
      name: '张三',
      username: 'zhangsan',
      email: 'zhangsan@test.com',
      role: 'admin',
    } as never
    const wrapper = mount(Layout, mountOptions)
    expect(wrapper.find('.header__username').text()).toBe('张三')
  })

  it('退出登录按钮存在', () => {
    const wrapper = mount(Layout, mountOptions)
    const allText = wrapper.text() + (document.body.textContent || '')
    expect(allText).toContain('退出登录')
  })
})
