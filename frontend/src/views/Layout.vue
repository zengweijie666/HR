<!--
  文件名: views/Layout.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 主布局容器
    - 左侧 aside 侧边栏（深墨绿背景，白色文字，可折叠）
    - 顶部 header（折叠按钮 + 当前页面标题 + 用户头像下拉）
    - 主区域 router-view，奶白背景
    - 侧边栏宽度：展开 240px / 折叠 72px，过渡 0.3s ease-out
-->
<template>
  <div class="layout" :class="{ 'is-collapsed': appStore.sidebarCollapsed }">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar__logo">
        <span class="sidebar__logo-dot" />
        <span v-if="!appStore.sidebarCollapsed" class="sidebar__logo-text">
          TalentSense
          <em class="sidebar__logo-sub">HR</em>
        </span>
      </div>

      <el-menu
        class="sidebar__menu"
        :default-active="activeMenu"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        router
      >
        <el-menu-item index="/workbench" @mouseenter="handleMenuHover('/workbench')">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>
        <el-menu-item index="/resumes" @mouseenter="handleMenuHover('/resumes')">
          <el-icon><Document /></el-icon>
          <template #title>简历库</template>
        </el-menu-item>
        <el-menu-item index="/jd-match" @mouseenter="handleMenuHover('/jd-match')">
          <el-icon><Connection /></el-icon>
          <template #title>JD 匹配</template>
        </el-menu-item>
        <el-menu-item index="/email" @mouseenter="handleMenuHover('/email')">
          <el-icon><Promotion /></el-icon>
          <template #title>邮件中心</template>
        </el-menu-item>
        <el-menu-item index="/dashboard" @mouseenter="handleMenuHover('/dashboard')">
          <el-icon><DataLine /></el-icon>
          <template #title>数据看板</template>
        </el-menu-item>
        <el-menu-item v-if="authStore.user?.role === 'admin'" index="/settings" @mouseenter="handleMenuHover('/settings')">
          <el-icon><Setting /></el-icon>
          <template #title>设置</template>
        </el-menu-item>
        <el-menu-item v-if="authStore.user?.role === 'admin'" index="/users" @mouseenter="handleMenuHover('/users')">
          <el-icon><UserFilled /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 右侧主区域 -->
    <div class="layout__main">
      <!-- 顶栏 -->
      <header class="header">
        <div class="header__left">
          <button
            type="button"
            class="collapse-btn"
            :aria-label="appStore.sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
            @click="appStore.toggleSidebar"
          >
            <el-icon><Fold v-if="!appStore.sidebarCollapsed" /><Expand v-else /></el-icon>
          </button>
          <h1 class="header__title">{{ pageTitle }}</h1>
        </div>

        <div class="header__right">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="header__user">
              <span class="header__avatar">{{ avatarLetter }}</span>
              <span class="header__username">{{ displayName }}</span>
              <el-tag v-if="authStore.user?.role === 'admin'" type="danger" size="small" effect="plain">管理员</el-tag>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 路由出口 -->
      <main class="layout__content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Layout 主布局
 * 整合 useAppStore（折叠态）与 useAuthStore（用户信息/退出登录）
 * 支持菜单悬停预加载路由组件，提升页面切换速度
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ChatDotRound,
  Document,
  Connection,
  DataLine,
  Setting,
  Fold,
  Expand,
  SwitchButton,
  UserFilled,
  Promotion,
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

/** 已预加载的路由集合（避免重复加载） */
const preloadedRoutes = new Set<string>()

/**
 * 鼠标悬停时预加载路由组件
 * 在用户点击菜单项前提前加载 JS chunk，消除点击延迟感
 * @param path 路由路径
 */
function handleMenuHover(path: string): void {
  if (preloadedRoutes.has(path)) return
  const found = router.resolve(path)
  if (found?.matched.length) {
    const component = found.matched[found.matched.length - 1].components?.default
    if (typeof component === 'function') {
      component()
      preloadedRoutes.add(path)
    }
  }
}

/** 当前激活的菜单（用于高亮） */
const activeMenu = computed(() => {
  if (route.path.startsWith('/resumes')) return '/resumes'
  return route.path
})

/** 当前页面标题（取自 route.meta.title） */
const pageTitle = computed(() => {
  const t = route.meta.title
  return t ? String(t) : 'TalentSense'
})

/** 头像首字母（取 username / name 首字符） */
const avatarLetter = computed(() => {
  const name = authStore.user?.name || authStore.user?.username || 'U'
  return name.charAt(0).toUpperCase()
})

/** 顶栏显示的用户名 */
const displayName = computed(() => {
  return authStore.user?.name || authStore.user?.username || '未登录'
})

/**
 * 处理下拉菜单命令
 * @param command 命令名
 */
function handleCommand(command: string): void {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped lang="scss">
.layout {
  display: flex;
  width: 100%;
  height: 100vh;
  background-color: var(--color-bg);

  &__main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    height: 100vh;
  }

  &__content {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: var(--space-6) var(--space-8);
    background-color: var(--color-bg);
  }
}

/* ============ 侧边栏 ============ */
.sidebar {
  flex-shrink: 0;
  width: 240px;
  display: flex;
  flex-direction: column;
  background-color: var(--color-bg-deep);
  color: #fff;
  transition: width var(--duration-base) var(--ease-out);

  .layout.is-collapsed & {
    width: 72px;
  }

  &__logo {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-5) var(--space-5);
    height: 64px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  &__logo-dot {
    flex-shrink: 0;
    width: 10px;
    height: 10px;
    background: var(--color-accent);
    border-radius: 50%;
    box-shadow: 0 0 12px var(--color-accent-glow);
  }

  &__logo-text {
    font-family: var(--font-display);
    font-size: 22px;
    font-weight: 500;
    color: #fff;
    letter-spacing: -0.01em;
    white-space: nowrap;
  }

  &__logo-sub {
    margin-left: 6px;
    font-family: var(--font-body);
    font-style: normal;
    font-size: var(--text-xs);
    font-weight: 600;
    letter-spacing: 0.18em;
    color: var(--color-accent-soft);
  }

  &__menu {
    flex: 1;
    margin-top: var(--space-3);
    padding: 0 var(--space-3);
    background-color: transparent !important;
    border-right: none !important;

    :deep(.el-menu-item) {
      height: 44px;
      line-height: 44px;
      margin: 2px 0;
      border-radius: var(--radius-md);
      color: rgba(255, 255, 255, 0.7);
      background-color: transparent !important;
      position: relative;
      transition: color var(--duration-fast) var(--ease-out),
        background-color var(--duration-fast) var(--ease-out);

      &:hover {
        color: #fff;
        background-color: rgba(255, 255, 255, 0.08) !important;
      }

      &.is-active {
        color: #fff;
        background-color: rgba(255, 255, 255, 0.12) !important;

        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 8px;
          bottom: 8px;
          width: 3px;
          background: var(--color-accent);
          border-radius: 0 2px 2px 0;
        }
      }

      .el-icon {
        color: inherit;
        font-size: 18px;
      }
    }
  }

  /* 折叠态菜单居中 */
  .layout.is-collapsed & {
    :deep(.el-menu-item) {
      padding: 0 !important;
      justify-content: center;
    }
    :deep(.el-menu--collapse) {
      width: 100%;
    }
  }
}

/* ============ 顶栏 ============ */
.header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 var(--space-8);
  background-color: var(--color-bg-card);
  border-bottom: 1px solid var(--color-line);

  &__left {
    display: flex;
    align-items: center;
    gap: var(--space-4);
  }

  &__title {
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-weight: 500;
    color: var(--color-primary);
    margin: 0;
    letter-spacing: -0.01em;
  }

  &__right {
    display: flex;
    align-items: center;
  }

  &__user {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    cursor: pointer;
    padding: 6px 10px;
    border-radius: var(--radius-md);
    transition: background-color var(--duration-fast) var(--ease-out);

    &:hover {
      background-color: var(--color-bg-overlay);
    }
  }

  &__avatar {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: var(--color-accent);
    color: #fff;
    font-family: var(--font-display);
    font-weight: 600;
    font-size: var(--text-sm);
  }

  &__username {
    font-size: var(--text-sm);
    color: var(--color-ink);
    font-weight: 500;
  }
}

/* 折叠按钮 */
.collapse-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid var(--color-line);
  background-color: var(--color-bg-card);
  color: var(--color-ink-soft);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: color var(--duration-fast) var(--ease-out),
    border-color var(--duration-fast) var(--ease-out),
    background-color var(--duration-fast) var(--ease-out);

  &:hover {
    color: var(--color-primary);
    border-color: var(--color-accent-soft);
    background-color: var(--color-primary-tint);
  }

  .el-icon {
    font-size: 18px;
  }
}
</style>
