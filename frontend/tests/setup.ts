/**
 * 文件名: tests/setup.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: Vitest 全局测试环境初始化，注册 ElementPlus + vue-router
 */
import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { createRouter, createMemoryHistory } from 'vue-router'

const router = createRouter({
  history: createMemoryHistory(),
  routes: [],
})

config.global.plugins = [ElementPlus, router]
