/**
 * 文件名: vite.config.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: Vite 构建配置，含别名与开发代理
 */
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
