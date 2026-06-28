/**
 * 文件名: vite.config.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: Vite 构建配置，含别名、开发代理、依赖预构建和文件预热
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
    warmup: {
      clientFiles: [
        './src/views/Layout.vue',
        './src/views/Workbench.vue',
        './src/views/ResumeList.vue',
        './src/views/ResumeDetail.vue',
        './src/views/Dashboard.vue',
        './src/views/JdMatch.vue',
        './src/views/EmailCenter.vue',
        './src/components/resume/ResumeCard.vue',
        './src/components/resume/FilterBar.vue',
        './src/components/chat/ChatPanel.vue',
        './src/components/chat/MessageBubble.vue',
        './src/api/request.ts',
        './src/api/resume.ts',
        './src/api/chat.ts',
        './src/stores/auth.ts',
        './src/stores/resume.ts',
        './src/stores/chat.ts',
      ],
    },
  },
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'element-plus',
      '@element-plus/icons-vue',
      'axios',
    ],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
        },
      },
    },
  },
})
