/**
 * 文件名: main.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 应用入口，挂载 Pinia / Router / ElementPlus / 错误监控
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import { initMonitor, manualError } from './utils/monitor'
import './styles/variables.scss'

initMonitor()

const app = createApp(App)

app.config.errorHandler = (err, instance, info) => {
  try {
    manualError(err instanceof Error ? err : String(err), { info, component: instance?.$options?.name || '' })
  } catch {}
  console.error('[Vue Error]', err, info)
}

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
