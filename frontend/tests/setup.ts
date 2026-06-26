/**
 * 文件名: tests/setup.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: Vitest 全局测试环境初始化，注册 ElementPlus
 */
import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'

config.global.plugins = [ElementPlus]
