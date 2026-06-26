/**
 * 文件名: router/index.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 路由表与全局守卫
 *   - /login 公开路由
 *   - / 布局容器，含子路由（工作台/简历库/详情/看板/JD/设置）
 *   - beforeEach：未登录跳 /login，公开路由放行
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/workbench',
    children: [
      {
        path: 'workbench',
        name: 'Workbench',
        component: () => import('@/views/Workbench.vue'),
        meta: { title: '工作台' },
      },
      {
        path: 'resumes',
        name: 'ResumeList',
        component: () => import('@/views/ResumeList.vue'),
        meta: { title: '简历库' },
      },
      {
        path: 'resumes/:id',
        name: 'ResumeDetail',
        component: () => import('@/views/ResumeDetail.vue'),
        meta: { title: '简历详情' },
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据看板' },
      },
      {
        path: 'jd-match',
        name: 'JdMatch',
        component: () => import('@/views/JdMatch.vue'),
        meta: { title: 'JD 匹配' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '设置' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * 全局前置守卫
 * - meta.public 为 true 直接放行
 * - 未登录跳转 /login
 * - 否则放行
 */
router.beforeEach((to) => {
  if (to.meta.public === true) return true
  const auth = useAuthStore()
  if (!auth.isLoggedIn) {
    return { path: '/login' }
  }
  return true
})

export default router
