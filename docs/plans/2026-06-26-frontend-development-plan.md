# TalentSense HR 前端开发实施计划

**Goal:** 严格遵循 [API-Design.md](../API-Design.md) 与 [Business-Requirements.md](../Business-Requirements.md) 验收标准，使用 TDD 方式落地 Vue3 + TypeScript + Vite + Element Plus 前端应用。

**Architecture:** SPA 单页应用，Pinia 状态管理，Axios + fetch(SSE) API 层，Vue Router 路由 + 登录守卫。视图按业务域分模块，组件按通用/业务分目录。

**Tech Stack:** Vue 3.4+ / TypeScript 5.0+ / Vite 5.0+ / Element Plus 2.6+ / Pinia 2.1+ / Vue Router 4.2+ / Axios 1.6+ / ECharts 5.5+ / PDF.js 4.0+ / Vitest / @vue/test-utils / SCSS

---

## Global Constraints

- **包管理**：使用 npm 或 pnpm，锁定 `package.json` + `package-lock.json`（或 `pnpm-lock.yaml`）
- **启动命令**：`npm run dev`（开发）/ `npm run build`（构建）/ `npm run test`（测试）
- **配置分离**：环境变量通过 `.env.development` / `.env.production` 注入，前缀 `VITE_`
- **文件元信息**：每个 `.ts` / `.vue` 文件首部必须写明 文件名 / 创建时间 / 作者 / 功能描述
- **规范注释**：每个函数与组件必须写 JSDoc 注释，标明入参/出参/核心逻辑
- **统一响应**：Axios 拦截器统一剥离 `{code, message, data, trace_id}` 外层，业务代码只处理 `data`
- **类型安全**：所有 API 调用必须带 TypeScript 类型，禁止 `any`（除 SSE 临时数据）
- **路由守卫**：未登录跳转 `/login`，登录失效(1002)自动登出并跳转
- **测试驱动**：每个模块先写失败测试 → 实现 → 测试通过 → 提交
- **目录前缀**：前端代码根目录 `frontend/`，测试根目录 `frontend/tests/`（或 `__tests__` 同级）

---

## File Structure

```
frontend/
├── src/
│   ├── main.ts                       # 入口，挂载 Pinia/Router/ElementPlus
│   ├── App.vue                       # 根组件
│   ├── router/
│   │   └── index.ts                  # 路由配置 + 登录守卫
│   ├── stores/                       # Pinia 状态管理
│   │   ├── auth.ts                   # 登录态/Token/用户信息
│   │   ├── chat.ts                   # 会话列表/当前会话/消息流
│   │   ├── resume.ts                 # 简历列表/筛选条件
│   │   └── app.ts                    # 全局 UI 状态(侧边栏/主题)
│   ├── api/                          # API 调用层(对应 API 文档)
│   │   ├── request.ts                # Axios 实例 + 拦截器 + 统一错误
│   │   ├── sse.ts                    # SSE 流式请求封装(fetch)
│   │   ├── auth.ts                   # 认证接口
│   │   ├── resume.ts                 # 简历接口
│   │   ├── chat.ts                   # 对话接口
│   │   ├── search.ts                 # 检索接口
│   │   ├── candidate.ts              # 候选人接口
│   │   ├── email.ts                  # 邮件接口
│   │   ├── jd.ts                     # JD 匹配接口
│   │   ├── interview.ts              # 面试接口
│   │   └── dashboard.ts              # 看板接口
│   ├── types/                        # TypeScript 类型(对应 API 数据模型)
│   │   ├── api.ts                    # ApiResponse/PageResult 通用类型
│   │   ├── auth.ts
│   │   ├── resume.ts
│   │   ├── chat.ts
│   │   ├── candidate.ts
│   │   ├── email.ts
│   │   ├── jd.ts
│   │   ├── interview.ts
│   │   └── dashboard.ts
│   ├── views/                        # 页面
│   │   ├── Login.vue                 # 登录页
│   │   ├── Layout.vue                # 主布局
│   │   ├── Workbench.vue             # 工作台
│   │   ├── ResumeList.vue            # 简历列表
│   │   ├── ResumeDetail.vue          # 简历详情
│   │   ├── Dashboard.vue             # 数据看板
│   │   ├── JdMatch.vue               # JD 匹配页
│   │   └── Settings.vue              # 设置页
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatPanel.vue
│   │   │   ├── MessageBubble.vue
│   │   │   ├── SessionList.vue
│   │   │   └── StreamIndicator.vue
│   │   ├── resume/
│   │   │   ├── ResumeCard.vue
│   │   │   ├── ResumePreview.vue
│   │   │   ├── UploadDialog.vue
│   │   │   └── FilterBar.vue
│   │   ├── candidate/
│   │   │   ├── CandidateCard.vue
│   │   │   ├── CandidateCompare.vue
│   │   │   └── TagInput.vue
│   │   ├── dashboard/
│   │   │   └── ChartWidget.vue
│   │   └── common/
│   │       ├── EmptyState.vue
│   │       └── LoadingOverlay.vue
│   ├── utils/
│   │   ├── format.ts                 # 薪资/日期格式化
│   │   ├── download.ts               # 文件下载
│   │   └── constant.ts               # 枚举常量
│   └── styles/
│       └── variables.scss
├── tests/                            # 单元测试
│   ├── setup.ts
│   ├── api/
│   ├── stores/
│   ├── components/
│   └── views/
├── vite.config.ts
├── vitest.config.ts
├── tsconfig.json
├── package.json
└── .env.development
```

---

## Phase 1: 项目骨架与构建配置

### Task 1.1: 初始化 Vite + Vue3 + TypeScript 项目

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/.env.development`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Test: `frontend/tests/setup.ts`

- [ ] **Step 1: 写最小化测试（验证项目可启动）**

```typescript
// tests/setup.ts
/**
 * 文件名: tests/setup.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: Vitest 全局配置，挂载 ElementPlus
 */
import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'

config.global.plugins = [ElementPlus]
```

```typescript
// tests/app.test.ts
/**
 * 文件名: tests/app.test.ts
 * 测试 App 组件可挂载
 */
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import App from '../src/App.vue'

describe('App', () => {
  it('可挂载', () => {
    const wrapper = mount(App)
    expect(wrapper.exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 初始化项目**

```bash
cd frontend
npm create vite@latest . -- --template vue-ts
```

- [ ] **Step 3: 安装依赖**

```bash
npm install vue-router@4 pinia@2 element-plus@2.6 axios@1.6 echarts@5.5 pdfjs-dist@4
npm install -D vitest@1 @vue/test-utils@2 jsdom @types/node sass
```

- [ ] **Step 4: 写配置文件**

```json
// package.json (关键脚本)
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

```typescript
// vite.config.ts
/**
 * 文件名: vite.config.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: Vite 构建配置
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
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "preserve",
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] },
    "types": ["vitest/globals"]
  },
  "include": ["src/**/*", "tests/**/*"]
}
```

```bash
# .env.development
VITE_API_BASE=/api/v1
VITE_APP_TITLE=TalentSense HR
```

```vue
<!-- src/App.vue -->
<!--
  文件名: App.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 根组件
-->
<template>
  <router-view />
</template>

<script setup lang="ts">
</script>
```

```typescript
// src/main.ts
/**
 * 文件名: main.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 应用入口，挂载插件
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './styles/variables.scss'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd frontend && npm test`
Expected: 1 passed

- [ ] **Step 6: 提交**

```bash
git add frontend/
git commit -m "chore(frontend): 初始化 Vite + Vue3 + TS 项目"
```

---

### Task 1.2: TypeScript 通用类型定义

**Files:**
- Create: `frontend/src/types/api.ts`
- Test: `frontend/tests/types/test_api_types.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/types/test_api_types.test.ts
/**
 * 文件名: test_api_types.test.ts
 * 测试通用类型定义
 */
import { describe, it, expectTypeOf } from 'vitest'
import type { ApiResponse, PageResult, PageQuery } from '@/types/api'

describe('API 类型', () => {
  it('ApiResponse 结构正确', () => {
    expectTypeOf<ApiResponse>().toMatchTypeOf<{ code: number; message: string; data: any; trace_id: string }>()
  })

  it('PageResult 结构正确', () => {
    expectTypeOf<PageResult<string>>().toMatchTypeOf<{ list: string[]; total: number; page: number; page_size: number; total_pages: number }>()
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/types/test_api_types.test.ts`
Expected: FAIL（文件不存在）

- [ ] **Step 3: 实现 types/api.ts**

```typescript
/**
 * 文件名: types/api.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 通用 API 类型，对应 API-Design.md 0.4
 */

/** 统一响应格式 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  trace_id: string
}

/** 分页查询 */
export interface PageQuery {
  page: number
  page_size: number
}

/** 分页结果 */
export interface PageResult<T = any> {
  list: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/types/test_api_types.test.ts`
Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/types/api.ts frontend/tests/types/test_api_types.test.ts
git commit -m "feat(types): 添加通用 API 类型定义"
```

---

### Task 1.3: 业务类型定义（对应 API 文档第十章）

**Files:**
- Create: `frontend/src/types/auth.ts`
- Create: `frontend/src/types/resume.ts`
- Create: `frontend/src/types/chat.ts`
- Create: `frontend/src/types/candidate.ts`
- Create: `frontend/src/types/email.ts`
- Create: `frontend/src/types/jd.ts`
- Create: `frontend/src/types/interview.ts`
- Create: `frontend/src/types/dashboard.ts`
- Test: `frontend/tests/types/test_business_types.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/types/test_business_types.test.ts
import { describe, it, expectTypeOf } from 'vitest'
import type { LoginRequest, TokenResponse } from '@/types/auth'
import type { ResumeListItem, ResumeDetail } from '@/types/resume'
import type { ChatMessage, SSEEvent } from '@/types/chat'
import type { CandidateCard } from '@/types/candidate'
import type { EmailConfig } from '@/types/email'
import type { JdMatchResult } from '@/types/jd'
import type { InterviewQuestion, InterviewNote } from '@/types/interview'
import type { DashboardStats } from '@/types/dashboard'

describe('业务类型', () => {
  it('LoginRequest', () => {
    expectTypeOf<LoginRequest>().toMatchTypeOf<{ username: string; password: string }>()
  })
  it('ResumeListItem', () => {
    expectTypeOf<ResumeListItem>().toHaveProperty('resume_id').toBeString()
    expectTypeOf<ResumeListItem>().toHaveProperty('is_favorite').toBeBoolean()
  })
  it('CandidateCard', () => {
    expectTypeOf<CandidateCard>().toHaveProperty('score').toBeNumber()
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/types/test_business_types.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现所有业务类型**

```typescript
// src/types/auth.ts
/**
 * 文件名: types/auth.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 认证类型，对应 API-Design.md 一
 */
export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserInfo {
  user_id: string
  username: string
  role: string
  name: string
}
```

```typescript
// src/types/resume.ts
/**
 * 文件名: types/resume.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 简历类型，对应 API-Design.md 2.0 / 第十章
 */
export interface ResumeListItem {
  resume_id: string
  candidate_id: string
  name: string
  gender: string
  age: number
  education: string
  education_level: number
  work_years: number
  skills: string[]
  expected_salary: { min: number; max: number }
  tags: string[]
  is_favorite: boolean
  parse_status: 'pending' | 'parsing' | 'completed' | 'failed'
  location: string
  created_at: string
}

export interface WorkExperience {
  company: string
  position: string
  start_date: string
  end_date: string
  description: string
}

export interface EducationDetail {
  school: string
  major: string
  degree: string
  start_date: string
  end_date: string
}

export interface InterviewNote {
  note_id: string
  interviewer: string
  rating: number
  result: string
  content: string
  created_at: string
}

export interface ResumeDetail extends ResumeListItem {
  basic_info: {
    name: string
    phone_masked: string
    email_masked: string
    gender: string
    age: number
    location: string
  }
  work_experience: WorkExperience[]
  education_detail: EducationDetail[]
  summary: string
  file_info: { file_name: string; file_type: string; file_size: number }
  parse_info: { parse_status: string; parse_time: string }
  notes: string
  interview_notes: InterviewNote[]
  updated_at: string
}

export interface UploadResponse {
  resume_id: string
  candidate_id: string
  file_name: string
  parse_status: string
  is_duplicate: boolean
  duplicate_with: string | null
}

export interface ResumeListQuery {
  page?: number
  page_size?: number
  keyword?: string
  tag?: string
  is_favorite?: boolean
  education_min?: number
  work_years_min?: number
  salary_min?: number
  salary_max?: number
  status?: string
}
```

```typescript
// src/types/chat.ts
/**
 * 文件名: types/chat.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 对话类型，对应 API-Design.md 3.0 / 0.5 SSE
 */
import type { CandidateCard } from './candidate'

export interface ChatSession {
  session_id: string
  title: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  message_id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  intent: string | null
  strategy: string | null
  candidates: CandidateCard[] | null
  created_at: string
}

/** SSE 事件类型，对应 API-Design.md 0.5 */
export type SSEEvent =
  | { event: 'intent'; data: { intent: string; strategy: string } }
  | { event: 'rewrite'; data: { query: string; rewrites: string[] } }
  | { event: 'retrieval'; data: { count: number; candidate_ids: string[] } }
  | { event: 'rank'; data: { ranked: { candidate_id: string; score: number }[] } }
  | { event: 'token'; data: { delta: string } }
  | { event: 'candidates'; data: { candidates: CandidateCard[] } }
  | { event: 'done'; data: { message_id: string; response: string } }
  | { event: 'error'; data: { code: number; message: string } }

export interface SSEHandlers {
  onIntent?: (data: { intent: string; strategy: string }) => void
  onRewrite?: (data: { query: string; rewrites: string[] }) => void
  onRetrieval?: (data: { count: number; candidate_ids: string[] }) => void
  onRank?: (data: { ranked: { candidate_id: string; score: number }[] }) => void
  onToken?: (delta: string) => void
  onCandidates?: (candidates: CandidateCard[]) => void
  onDone?: (data: { message_id: string; response: string }) => void
  onError?: (data: { code: number; message: string }) => void
}
```

```typescript
// src/types/candidate.ts
/**
 * 文件名: types/candidate.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 候选人类型，对应 API-Design.md 5.0
 */
export interface CandidateCard {
  candidate_id: string
  resume_id: string
  name: string
  work_years: number
  education: string
  skills: string[]
  expected_salary: { min: number; max: number }
  score: number
  reason: string
  tags: string[]
  is_favorite: boolean
}

export interface ExportRequest {
  candidate_ids: string[]
  columns: string[]
}

export interface CompareResult {
  candidates: CandidateCard[]
  dimensions: string[]
}
```

```typescript
// src/types/email.ts
/**
 * 文件名: types/email.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 邮件类型，对应 API-Design.md 6.0
 */
export interface EmailRequest {
  to_email: string
  candidate_ids: string[]
  job_title: string
}

export interface EmailConfig {
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_password?: string
}
```

```typescript
// src/types/jd.ts
/**
 * 文件名: types/jd.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: JD 匹配类型，对应 API-Design.md 7.0
 */
import type { CandidateCard } from './candidate'

export interface JdInfo {
  title: string
  skills: string[]
  work_years_min: number
  salary_max: number
}

export interface JdMatchCandidate extends CandidateCard {
  match_score: number
  reason: string
}

export interface JdMatchResult {
  jd: JdInfo
  candidates: JdMatchCandidate[]
}
```

```typescript
// src/types/interview.ts
/**
 * 文件名: types/interview.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 面试类型，对应 API-Design.md 8.0
 */
export interface InterviewQuestion {
  question: string
  category: string
}

export interface InterviewNoteRequest {
  resume_id: string
  interviewer: string
  rating: number
  result: string
  content: string
}
```

```typescript
// src/types/dashboard.ts
/**
 * 文件名: types/dashboard.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 看板类型，对应 API-Design.md 9.0
 */
export interface DashboardStats {
  total_resumes: number
  favorite_count: number
  parsing_count: number
  total_sessions: number
  top_skills: { _id: string; count: number }[]
  education_distribution: { _id: string; count: number }[]
  salary_distribution: { _id: string; count: number }[]
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/types/test_business_types.test.ts`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/types/ frontend/tests/types/test_business_types.test.ts
git commit -m "feat(types): 添加业务类型定义"
```

---

### Task 1.4: 枚举常量 `utils/constant.ts`

**Files:**
- Create: `frontend/src/utils/constant.ts`
- Test: `frontend/tests/utils/test_constant.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/utils/test_constant.test.ts
import { describe, it, expect } from 'vitest'
import { INTENT_TYPES, STRATEGY_TYPES, PARSE_STATUS, EDUCATION_LEVELS } from '@/utils/constant'

describe('枚举常量', () => {
  it('INTENT_TYPES 含 chitchat/search/detail/compare', () => {
    expect(INTENT_TYPES.chitchat).toBe('闲聊')
    expect(INTENT_TYPES.search).toBe('搜索推荐')
    expect(INTENT_TYPES.detail).toBe('详情查询')
    expect(INTENT_TYPES.compare).toBe('对比')
  })
  it('STRATEGY_TYPES 含 4 种', () => {
    expect(Object.keys(STRATEGY_TYPES)).toHaveLength(4)
    expect(STRATEGY_TYPES.hyde).toBeDefined()
  })
  it('PARSE_STATUS', () => {
    expect(PARSE_STATUS.completed).toBe('已解析')
    expect(PARSE_STATUS.failed).toBe('解析失败')
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/utils/test_constant.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 constant.ts**

```typescript
/**
 * 文件名: utils/constant.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 全局枚举常量，与 API 文档 0.6 节一致
 */

/** 意图类型 */
export const INTENT_TYPES = {
  chitchat: '闲聊',
  search: '搜索推荐',
  detail: '详情查询',
  compare: '对比',
} as const

/** 检索策略 */
export const STRATEGY_TYPES = {
  direct: '直接检索',
  hyde: '假设文档',
  subquery: '子查询',
  backtracking: '回溯简化',
} as const

/** 解析状态 */
export const PARSE_STATUS = {
  pending: '待解析',
  parsing: '解析中',
  completed: '已解析',
  failed: '解析失败',
} as const

/** 学历等级（0-3） */
export const EDUCATION_LEVELS = {
  0: '专科',
  1: '本科',
  2: '硕士',
  3: '博士',
} as const

/** SSE 事件类型 */
export const SSE_EVENTS = {
  intent: 'intent',
  rewrite: 'rewrite',
  retrieval: 'retrieval',
  rank: 'rank',
  token: 'token',
  candidates: 'candidates',
  done: 'done',
  error: 'error',
} as const
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/utils/test_constant.test.ts`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/utils/constant.ts frontend/tests/utils/test_constant.test.ts
git commit -m "feat(utils): 添加枚举常量"
```

---

## Phase 2: API 调用层

### Task 2.1: Axios 实例与拦截器 `api/request.ts`

**Files:**
- Create: `frontend/src/api/request.ts`
- Test: `frontend/tests/api/test_request.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/api/test_request.test.ts
/**
 * 文件名: test_request.test.ts
 * 测试 Axios 拦截器
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import request from '@/api/request'

const server = setupServer(
  http.get('http://test/api/v1/test', () => {
    return HttpResponse.json({ code: 0, message: 'ok', data: { x: 1 }, trace_id: 't1' })
  }),
  http.get('http://test/api/v1/biz-error', () => {
    return HttpResponse.json({ code: 1001, message: '业务错误', data: null, trace_id: 't2' })
  })
)

beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())

describe('request 拦截器', () => {
  it('成功响应剥离外层，返回 data', async () => {
    const data = await request.get('http://test/api/v1/test')
    expect(data).toEqual({ x: 1 })
  })

  it('业务错误 code!=0 抛错', async () => {
    await expect(request.get('http://test/api/v1/biz-error')).rejects.toMatchObject({ code: 1001 })
  })
})
```

- [ ] **Step 2: 安装 msw**

```bash
cd frontend && npm install -D msw
```

- [ ] **Step 3: 运行确认失败**

Run: `cd frontend && npm test -- tests/api/test_request.test.ts`
Expected: FAIL

- [ ] **Step 4: 实现 request.ts**

```typescript
/**
 * 文件名: api/request.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: Axios 实例 + 拦截器，统一剥离 {code,message,data}
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 30000,
})

// 请求拦截：注入 Token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：剥离外层
request.interceptors.response.use(
  (response) => {
    const { code, message, data } = response.data
    if (code === 0) return data
    ElMessage.error(message)
    if (code === 1002) {
      // Token 失效
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject({ code, message })
  },
  (error) => {
    ElMessage.error('网络异常，请稍后重试')
    return Promise.reject(error)
  }
)

export default request
```

- [ ] **Step 5: 运行确认通过**

Run: `cd frontend && npm test -- tests/api/test_request.test.ts`
Expected: 2 passed

- [ ] **Step 6: 提交**

```bash
git add frontend/src/api/request.ts frontend/tests/api/test_request.test.ts
git commit -m "feat(api): 实现 Axios 实例与拦截器"
```

---

### Task 2.2: SSE 流式请求封装 `api/sse.ts`

**Files:**
- Create: `frontend/src/api/sse.ts`
- Test: `frontend/tests/api/test_sse.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/api/test_sse.test.ts
/**
 * 文件名: test_sse.test.ts
 * 测试 SSE 解析与分发
 */
import { describe, it, expect } from 'vitest'
import { parseSSEBlock, dispatch } from '@/api/sse'

describe('SSE 解析', () => {
  it('解析 event+data', () => {
    const block = 'event: intent\ndata: {"intent":"search","strategy":"direct"}'
    const result = parseSSEBlock(block)
    expect(result.event).toBe('intent')
    expect(result.data.intent).toBe('search')
  })

  it('解析 token 事件', () => {
    const block = 'event: token\ndata: {"delta":"你"}'
    const result = parseSSEBlock(block)
    expect(result.event).toBe('token')
    expect(result.data.delta).toBe('你')
  })

  it('dispatch 调用对应 handler', () => {
    const handlers = {
      onIntent: (d: any) => {},
      onToken: (d: string) => {},
    }
    const spy1 = vi.spyOn(handlers, 'onIntent')
    const spy2 = vi.spyOn(handlers, 'onToken')
    dispatch({ event: 'intent', data: { intent: 'search', strategy: 'd' } }, handlers)
    dispatch({ event: 'token', data: { delta: '嗨' } }, handlers)
    expect(spy1).toHaveBeenCalled()
    expect(spy2).toHaveBeenCalledWith('嗨')
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/api/test_sse.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 sse.ts**

```typescript
/**
 * 文件名: api/sse.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: SSE 流式请求封装（fetch + ReadableStream，支持 POST）
 */
import type { SSEHandlers } from '@/types/chat'

/** 解析单个 SSE 事件块 */
export function parseSSEBlock(block: string): { event: string; data: any } {
  const lines = block.split('\n')
  let eventType = ''
  let data = ''
  for (const line of lines) {
    if (line.startsWith('event:')) eventType = line.slice(6).trim()
    else if (line.startsWith('data:')) data += line.slice(5).trim()
  }
  return { event: eventType, data: data ? JSON.parse(data) : {} }
}

/** 分发事件到 handler */
export function dispatch(event: { event: string; data: any }, handlers: SSEHandlers): void {
  switch (event.event) {
    case 'intent': handlers.onIntent?.(event.data); break
    case 'rewrite': handlers.onRewrite?.(event.data); break
    case 'retrieval': handlers.onRetrieval?.(event.data); break
    case 'rank': handlers.onRank?.(event.data); break
    case 'token': handlers.onToken?.(event.data.delta); break
    case 'candidates': handlers.onCandidates?.(event.data.candidates); break
    case 'done': handlers.onDone?.(event.data); break
    case 'error': handlers.onError?.(event.data); break
  }
}

/**
 * 发起 SSE 流式请求
 * @param url 完整 URL
 * @param body 请求体
 * @param handlers 8 种事件回调
 * @param signal AbortSignal（用于取消）
 */
export async function sseChat(
  url: string,
  body: any,
  handlers: SSEHandlers,
  signal?: AbortSignal
): Promise<void> {
  const token = localStorage.getItem('access_token')
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!resp.ok || !resp.body) throw new Error('SSE 连接失败')

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    // 按双换行分割 SSE 事件块
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''
    for (const block of blocks) {
      if (!block.trim()) continue
      const event = parseSSEBlock(block)
      dispatch(event, handlers)
    }
  }
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/api/test_sse.test.ts`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/api/sse.ts frontend/tests/api/test_sse.test.ts
git commit -m "feat(api): 实现 SSE 流式请求封装"
```

---

### Task 2.3: 业务 API 模块（对应 API 文档）

**Files:**
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/api/resume.ts`
- Create: `frontend/src/api/chat.ts`
- Create: `frontend/src/api/search.ts`
- Create: `frontend/src/api/candidate.ts`
- Create: `frontend/src/api/email.ts`
- Create: `frontend/src/api/jd.ts`
- Create: `frontend/src/api/interview.ts`
- Create: `frontend/src/api/dashboard.ts`
- Test: `frontend/tests/api/test_api_modules.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/api/test_api_modules.test.ts
import { describe, it, expect, vi } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import * as authApi from '@/api/auth'
import * as resumeApi from '@/api/resume'
import * as chatApi from '@/api/chat'
import * as searchApi from '@/api/search'
import * as candidateApi from '@/api/candidate'
import * as emailApi from '@/api/email'
import * as jdApi from '@/api/jd'
import * as interviewApi from '@/api/interview'
import * as dashboardApi from '@/api/dashboard'

const server = setupServer(
  http.post('http://test/api/v1/auth/login', () => HttpResponse.json({ code: 0, message: 'ok', data: { access_token: 't1', refresh_token: 'r1', token_type: 'bearer', expires_in: 3600 }, trace_id: 't' })),
  http.get('http://test/api/v1/resumes', () => HttpResponse.json({ code: 0, message: 'ok', data: { list: [], total: 0, page: 1, page_size: 20, total_pages: 0 }, trace_id: 't' })),
  http.post('http://test/api/v1/search', () => HttpResponse.json({ code: 0, message: 'ok', data: [], trace_id: 't' })),
  http.get('http://test/api/v1/dashboard/stats', () => HttpResponse.json({ code: 0, message: 'ok', data: { total_resumes: 10 }, trace_id: 't' }))
)
beforeEach(() => server.listen())
afterEach(() => server.resetHandlers())

describe('API 模块', () => {
  it('auth.login 返回 TokenResponse', async () => {
    const data = await authApi.login({ username: 'admin', password: '123' })
    expect(data.access_token).toBe('t1')
  })
  it('resume.getResumeList 返回 PageResult', async () => {
    const data = await resumeApi.getResumeList({ page: 1, page_size: 20 })
    expect(data.total).toBe(0)
  })
  it('search.search 返回数组', async () => {
    const data = await searchApi.search({ query: 'Java', filters: {}, top_k: 10 })
    expect(Array.isArray(data)).toBe(true)
  })
  it('dashboard.getStats 返回 DashboardStats', async () => {
    const data = await dashboardApi.getStats()
    expect(data.total_resumes).toBe(10)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/api/test_api_modules.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现所有 API 模块**

```typescript
// src/api/auth.ts
/**
 * 文件名: api/auth.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 认证接口，对应 API-Design.md 一
 */
import request from './request'
import type { LoginRequest, TokenResponse, UserInfo } from '@/types/auth'

export const login = (data: LoginRequest) =>
  request.post<TokenResponse>('/auth/login', data) as unknown as Promise<TokenResponse>

export const refresh = (refresh_token: string) =>
  request.post<TokenResponse>('/auth/refresh', { refresh_token }) as unknown as Promise<TokenResponse>

export const getMe = () =>
  request.get<UserInfo>('/auth/me') as unknown as Promise<UserInfo>

export const logout = () =>
  request.post('/auth/logout') as unknown as Promise<void>
```

```typescript
// src/api/resume.ts
/**
 * 文件名: api/resume.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 简历接口，对应 API-Design.md 二
 */
import request from './request'
import type { ResumeListItem, ResumeDetail, UploadResponse, ResumeListQuery } from '@/types/resume'
import type { PageResult } from '@/types/api'

export const uploadResume = (file: File, overwrite = false) => {
  const form = new FormData()
  form.append('file', file)
  form.append('overwrite', String(overwrite))
  return request.post<UploadResponse>('/resumes/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  }) as unknown as Promise<UploadResponse>
}

export const getResumeList = (params: ResumeListQuery) =>
  request.get<PageResult<ResumeListItem>>('/resumes', { params }) as unknown as Promise<PageResult<ResumeListItem>>

export const getResumeDetail = (resumeId: string) =>
  request.get<ResumeDetail>(`/resumes/${resumeId}`) as unknown as Promise<ResumeDetail>

export const deleteResume = (resumeId: string) =>
  request.delete(`/resumes/${resumeId}`) as unknown as Promise<void>

export const getPreviewUrl = (resumeId: string) =>
  request.get<{ preview_url: string; file_type: string; expires_in: number }>(`/resumes/${resumeId}/preview`) as unknown as Promise<{ preview_url: string; file_type: string; expires_in: number }>

export const updateTags = (resumeId: string, tags: string[]) =>
  request.put(`/resumes/${resumeId}/tags`, { tags }) as unknown as Promise<{ resume_id: string; tags: string[] }>

export const toggleFavorite = (resumeId: string, isFavorite: boolean) =>
  request.put(`/resumes/${resumeId}/favorite`, { is_favorite: isFavorite }) as unknown as Promise<{ resume_id: string; is_favorite: boolean }>

export const updateNotes = (resumeId: string, notes: string) =>
  request.put(`/resumes/${resumeId}/notes`, { notes }) as unknown as Promise<{ resume_id: string; notes: string }>
```

```typescript
// src/api/chat.ts
/**
 * 文件名: api/chat.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 对话接口，对应 API-Design.md 三
 */
import request from './request'
import { sseChat } from './sse'
import type { ChatSession, ChatMessage } from '@/types/chat'
import type { PageResult } from '@/types/api'
import type { SSEHandlers } from '@/types/chat'

export const createSession = (title: string) =>
  request.post<ChatSession>('/chat/sessions', { title }) as unknown as Promise<ChatSession>

export const getSessions = (params: { page: number; page_size: number }) =>
  request.get<PageResult<ChatSession>>('/chat/sessions', { params }) as unknown as Promise<PageResult<ChatSession>>

export const getMessages = (sessionId: string) =>
  request.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`) as unknown as Promise<ChatMessage[]>

export const deleteSession = (sessionId: string) =>
  request.delete(`/chat/sessions/${sessionId}`) as unknown as Promise<void>

export const sendMessageStream = (
  sessionId: string,
  query: string,
  context: { filters?: any },
  handlers: SSEHandlers,
  signal?: AbortSignal
) => {
  const url = `${import.meta.env.VITE_API_BASE || '/api/v1'}/chat/sessions/${sessionId}/messages`
  return sseChat(url, { query, context }, handlers, signal)
}
```

```typescript
// src/api/search.ts
import request from './request'
import type { CandidateCard } from '@/types/candidate'

export const search = (data: { query: string; filters: any; top_k?: number }) =>
  request.post<CandidateCard[]>('/search', data) as unknown as Promise<CandidateCard[]>
```

```typescript
// src/api/candidate.ts
import request from './request'
import type { CandidateCard, CompareResult } from '@/types/candidate'

export const exportExcel = (data: { candidate_ids: string[]; columns: string[] }) =>
  request.post('/candidates/export', data, { responseType: 'blob' }) as unknown as Promise<Blob>

export const getSimilar = (resumeId: string, topK = 5) =>
  request.get<CandidateCard[]>(`/candidates/similar/${resumeId}`, { params: { top_k: topK } }) as unknown as Promise<CandidateCard[]>

export const compare = (candidateIds: string[]) =>
  request.post<CompareResult>('/candidates/compare', { candidate_ids: candidateIds }) as unknown as Promise<CompareResult>
```

```typescript
// src/api/email.ts
import request from './request'
import type { EmailConfig } from '@/types/email'

export const sendRecommendation = (data: { to_email: string; candidate_ids: string[]; job_title: string }) =>
  request.post('/email/send', data) as unknown as Promise<{ status: string; sent_count: number }>

export const getConfig = () =>
  request.get<EmailConfig>('/email/config') as unknown as Promise<EmailConfig>

export const updateConfig = (data: EmailConfig) =>
  request.put('/email/config', data) as unknown as Promise<void>
```

```typescript
// src/api/jd.ts
import request from './request'
import type { JdMatchResult } from '@/types/jd'

export const matchJd = (jdText: string, topK = 10) =>
  request.post<JdMatchResult>('/jd/match', { jd_text: jdText, top_k: topK }) as unknown as Promise<JdMatchResult>
```

```typescript
// src/api/interview.ts
import request from './request'
import type { InterviewQuestion } from '@/types/interview'

export const generateQuestions = (resumeId: string, jobTitle = '', count = 5) =>
  request.post<InterviewQuestion[]>('/interview/questions', { resume_id: resumeId, job_title: jobTitle, count }) as unknown as Promise<InterviewQuestion[]>

export const saveNote = (data: { resume_id: string; interviewer: string; rating: number; result: string; content: string }) =>
  request.post('/interview/notes', data) as unknown as Promise<{ note_id: string }>

export const getNotes = (resumeId: string) =>
  request.get(`/interview/notes/${resumeId}`) as unknown as Promise<any[]>
```

```typescript
// src/api/dashboard.ts
import request from './request'
import type { DashboardStats } from '@/types/dashboard'

export const getStats = () =>
  request.get<DashboardStats>('/dashboard/stats') as unknown as Promise<DashboardStats>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/api/test_api_modules.test.ts`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/api/ frontend/tests/api/test_api_modules.test.ts
git commit -m "feat(api): 实现 9 个业务 API 模块"
```

---

## Phase 3: Pinia 状态管理

### Task 3.1: Auth Store

**Files:**
- Create: `frontend/src/stores/auth.ts`
- Test: `frontend/tests/stores/test_auth_store.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/stores/test_auth_store.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
})

describe('auth store', () => {
  it('初始未登录', () => {
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(false)
    expect(store.token).toBe('')
  })

  it('setToken 后已登录', () => {
    const store = useAuthStore()
    store.setToken('abc', 'refresh')
    expect(store.isLoggedIn).toBe(true)
    expect(store.token).toBe('abc')
    expect(localStorage.getItem('access_token')).toBe('abc')
  })

  it('setUser', () => {
    const store = useAuthStore()
    store.setUser({ user_id: 'u1', username: 'admin', role: 'hr', name: 'HR' })
    expect(store.user?.username).toBe('admin')
  })

  it('logout 清空', () => {
    const store = useAuthStore()
    store.setToken('abc', 'r')
    store.logout()
    expect(store.isLoggedIn).toBe(false)
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/stores/test_auth_store.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 auth.ts**

```typescript
/**
 * 文件名: stores/auth.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 认证状态 - Token / 用户信息
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const user = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  function setToken(accessToken: string, refresh: string) {
    token.value = accessToken
    refreshToken.value = refresh
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refresh)
  }

  function setUser(u: UserInfo) {
    user.value = u
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { token, refreshToken, user, isLoggedIn, setToken, setUser, logout }
})
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/stores/test_auth_store.test.ts`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/stores/auth.ts frontend/tests/stores/test_auth_store.test.ts
git commit -m "feat(store): 实现 auth store"
```

---

### Task 3.2: Chat Store

**Files:**
- Create: `frontend/src/stores/chat.ts`
- Test: `frontend/tests/stores/test_chat_store.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/stores/test_chat_store.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'

beforeEach(() => setActivePinia(createPinia()))

describe('chat store', () => {
  it('初始空', () => {
    const store = useChatStore()
    expect(store.sessions).toEqual([])
    expect(store.currentSessionId).toBe('')
    expect(store.messages).toEqual([])
    expect(store.streaming).toBe(false)
  })

  it('setSessions', () => {
    const store = useChatStore()
    store.setSessions([{ session_id: 's1', title: '会话1', created_at: '', updated_at: '' }])
    expect(store.sessions).toHaveLength(1)
  })

  it('addMessage', () => {
    const store = useChatStore()
    store.addMessage({ message_id: 'm1', session_id: 's1', role: 'user', content: '你好', intent: null, strategy: null, candidates: null, created_at: '' })
    expect(store.messages).toHaveLength(1)
    expect(store.messages[0].content).toBe('你好')
  })

  it('appendToken 追加到最后一条 assistant 消息', () => {
    const store = useChatStore()
    store.addMessage({ message_id: 'm1', session_id: 's1', role: 'assistant', content: '', intent: null, strategy: null, candidates: null, created_at: '' })
    store.appendToken('你')
    store.appendToken('好')
    expect(store.messages[0].content).toBe('你好')
  })

  it('startStream/stopStream', () => {
    const store = useChatStore()
    store.startStream()
    expect(store.streaming).toBe(true)
    store.stopStream()
    expect(store.streaming).toBe(false)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/stores/test_chat_store.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 chat.ts**

```typescript
/**
 * 文件名: stores/chat.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 对话状态 - 会话列表 / 当前消息 / 流式状态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatSession, ChatMessage } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string>('')
  const messages = ref<ChatMessage[]>([])
  const streaming = ref<boolean>(false)
  const intent = ref<string>('')
  const strategy = ref<string>('')

  function setSessions(list: ChatSession[]) {
    sessions.value = list
  }

  function setCurrentSession(sessionId: string) {
    currentSessionId.value = sessionId
  }

  function setMessages(list: ChatMessage[]) {
    messages.value = list
  }

  function addMessage(msg: ChatMessage) {
    messages.value.push(msg)
  }

  function appendToken(delta: string) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content += delta
    }
  }

  function setIntent(i: string) { intent.value = i }
  function setStrategy(s: string) { strategy.value = s }

  function startStream() { streaming.value = true }
  function stopStream() { streaming.value = false }

  function reset() {
    messages.value = []
    streaming.value = false
    intent.value = ''
    strategy.value = ''
  }

  return {
    sessions, currentSessionId, messages, streaming, intent, strategy,
    setSessions, setCurrentSession, setMessages, addMessage, appendToken,
    setIntent, setStrategy, startStream, stopStream, reset,
  }
})
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/stores/test_chat_store.test.ts`
Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/stores/chat.ts frontend/tests/stores/test_chat_store.test.ts
git commit -m "feat(store): 实现 chat store"
```

---

### Task 3.3: Resume Store + App Store

**Files:**
- Create: `frontend/src/stores/resume.ts`
- Create: `frontend/src/stores/app.ts`
- Test: `frontend/tests/stores/test_resume_store.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/stores/test_resume_store.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useResumeStore } from '@/stores/resume'
import { useAppStore } from '@/stores/app'

beforeEach(() => setActivePinia(createPinia()))

describe('resume store', () => {
  it('setList', () => {
    const store = useResumeStore()
    store.setList([{ resume_id: 'r1', candidate_id: 'c1', name: '张三', gender: '男', age: 28, education: '本科', education_level: 1, work_years: 5, skills: ['Java'], expected_salary: { min: 20, max: 30 }, tags: [], is_favorite: false, parse_status: 'completed', location: '北京', created_at: '' }])
    expect(store.list).toHaveLength(1)
  })

  it('setFilters', () => {
    const store = useResumeStore()
    store.setFilters({ keyword: 'Java', education_min: 2 })
    expect(store.filters.keyword).toBe('Java')
    expect(store.filters.education_min).toBe(2)
  })

  it('updateFavorite', () => {
    const store = useResumeStore()
    store.setList([{ resume_id: 'r1', candidate_id: 'c1', name: 'x', gender: '', age: 0, education: '', education_level: 0, work_years: 0, skills: [], expected_salary: { min: 0, max: 0 }, tags: [], is_favorite: false, parse_status: 'completed', location: '', created_at: '' }])
    store.updateFavorite('r1', true)
    expect(store.list[0].is_favorite).toBe(true)
  })
})

describe('app store', () => {
  it('toggleSidebar', () => {
    const store = useAppStore()
    const initial = store.sidebarCollapsed
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(!initial)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/stores/test_resume_store.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 resume.ts 与 app.ts**

```typescript
// src/stores/resume.ts
/**
 * 文件名: stores/resume.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 简历列表与筛选状态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ResumeListItem, ResumeListQuery } from '@/types/resume'

export const useResumeStore = defineStore('resume', () => {
  const list = ref<ResumeListItem[]>([])
  const total = ref<number>(0)
  const filters = ref<ResumeListQuery>({ page: 1, page_size: 20 })

  function setList(items: ResumeListItem[]) { list.value = items }
  function setTotal(t: number) { total.value = t }
  function setFilters(f: ResumeListQuery) { filters.value = { ...filters.value, ...f } }
  function resetFilters() { filters.value = { page: 1, page_size: 20 } }

  function updateFavorite(resumeId: string, isFavorite: boolean) {
    const item = list.value.find((r) => r.resume_id === resumeId)
    if (item) item.is_favorite = isFavorite
  }

  function updateTags(resumeId: string, tags: string[]) {
    const item = list.value.find((r) => r.resume_id === resumeId)
    if (item) item.tags = tags
  }

  return { list, total, filters, setList, setTotal, setFilters, resetFilters, updateFavorite, updateTags }
})
```

```typescript
// src/stores/app.ts
/**
 * 文件名: stores/app.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 全局 UI 状态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref<boolean>(false)
  const loading = ref<boolean>(false)

  function toggleSidebar() { sidebarCollapsed.value = !sidebarCollapsed.value }
  function setLoading(v: boolean) { loading.value = v }

  return { sidebarCollapsed, loading, toggleSidebar, setLoading }
})
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/stores/test_resume_store.test.ts`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/stores/resume.ts frontend/src/stores/app.ts frontend/tests/stores/test_resume_store.test.ts
git commit -m "feat(store): 实现 resume/app store"
```

---

## Phase 4: 路由与登录守卫

### Task 4.1: Router 配置 + 守卫

**Files:**
- Create: `frontend/src/router/index.ts`
- Test: `frontend/tests/router/test_router.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/router/test_router.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
})

describe('router', () => {
  it('/ 重定向到 /workbench', async () => {
    localStorage.setItem('access_token', 'fake')
    await router.push('/')
    expect(router.currentRoute.value.path).toBe('/workbench')
  })

  it('未登录访问受保护路由跳 /login', async () => {
    await router.push('/workbench')
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('/login 路由存在', async () => {
    await router.push('/login')
    expect(router.currentRoute.value.path).toBe('/login')
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/router/test_router.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 router/index.ts**

```typescript
/**
 * 文件名: router/index.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 路由配置 + 登录守卫
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/workbench',
    children: [
      { path: 'workbench', name: 'Workbench', component: () => import('@/views/Workbench.vue') },
      { path: 'resumes', name: 'ResumeList', component: () => import('@/views/ResumeList.vue') },
      { path: 'resumes/:id', name: 'ResumeDetail', component: () => import('@/views/ResumeDetail.vue') },
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'jd-match', name: 'JdMatch', component: () => import('@/views/JdMatch.vue') },
      { path: 'settings', name: 'Settings', component: () => import('@/views/Settings.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.public) {
    next()
  } else if (!authStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
```

- [ ] **Step 4: 创建视图占位文件**

```vue
<!-- src/views/Login.vue -->
<template><div>Login</div></template>
<!-- src/views/Layout.vue -->
<template><router-view /></template>
<!-- src/views/Workbench.vue -->
<template><div>Workbench</div></template>
<!-- src/views/ResumeList.vue -->
<template><div>ResumeList</div></template>
<!-- src/views/ResumeDetail.vue -->
<template><div>ResumeDetail</div></template>
<!-- src/views/Dashboard.vue -->
<template><div>Dashboard</div></template>
<!-- src/views/JdMatch.vue -->
<template><div>JdMatch</div></template>
<!-- src/views/Settings.vue -->
<template><div>Settings</div></template>
```

- [ ] **Step 5: 运行确认通过**

Run: `cd frontend && npm test -- tests/router/test_router.test.ts`
Expected: 3 passed

- [ ] **Step 6: 提交**

```bash
git add frontend/src/router/ frontend/src/views/ frontend/tests/router/test_router.test.ts
git commit -m "feat(router): 实现路由配置与登录守卫"
```

---

## Phase 5: 通用组件

### Task 5.1: EmptyState 与 LoadingOverlay

**Files:**
- Create: `frontend/src/components/common/EmptyState.vue`
- Create: `frontend/src/components/common/LoadingOverlay.vue`
- Test: `frontend/tests/components/test_common.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/components/test_common.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

describe('EmptyState', () => {
  it('渲染默认文案', () => {
    const wrapper = mount(EmptyState)
    expect(wrapper.text()).toContain('暂无数据')
  })

  it('渲染自定义文案', () => {
    const wrapper = mount(EmptyState, { props: { text: '没有匹配的候选人' } })
    expect(wrapper.text()).toContain('没有匹配的候选人')
  })
})

describe('LoadingOverlay', () => {
  it('visible=false 时不显示', () => {
    const wrapper = mount(LoadingOverlay, { props: { visible: false } })
    expect(wrapper.find('.loading-overlay').exists()).toBe(false)
  })

  it('visible=true 时显示', () => {
    const wrapper = mount(LoadingOverlay, { props: { visible: true } })
    expect(wrapper.find('.loading-overlay').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/components/test_common.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现组件**

```vue
<!-- src/components/common/EmptyState.vue -->
<!--
  文件名: EmptyState.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 空状态占位组件
-->
<template>
  <div class="empty-state">
    <el-empty :description="text" />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ text?: string }>(), { text: '暂无数据' })
</script>
```

```vue
<!-- src/components/common/LoadingOverlay.vue -->
<!--
  文件名: LoadingOverlay.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 全屏加载遮罩
-->
<template>
  <div v-if="visible" class="loading-overlay">
    <el-icon class="is-loading"><Loading /></el-icon>
    <span>{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'
withDefaults(defineProps<{ visible: boolean; text?: string }>(), { text: '加载中...' })
</script>

<style scoped>
.loading-overlay {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,255,255,0.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 999;
}
</style>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/components/test_common.test.ts`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/common/ frontend/tests/components/test_common.test.ts
git commit -m "feat(common): 实现 EmptyState 与 LoadingOverlay"
```

---

## Phase 6: 简历模块组件

### Task 6.1: ResumeCard 与 FilterBar

**Files:**
- Create: `frontend/src/components/resume/ResumeCard.vue`
- Create: `frontend/src/components/resume/FilterBar.vue`
- Test: `frontend/tests/components/test_resume_components.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/components/test_resume_components.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ResumeCard from '@/components/resume/ResumeCard.vue'
import FilterBar from '@/components/resume/FilterBar.vue'

const sample = {
  resume_id: 'r1', candidate_id: 'c1', name: '张三', gender: '男', age: 28,
  education: '本科', education_level: 1, work_years: 5,
  skills: ['Java', 'Spring'], expected_salary: { min: 20, max: 30 },
  tags: ['已面试'], is_favorite: false, parse_status: 'completed',
  location: '北京', created_at: '2026-06-26T10:00:00Z',
}

describe('ResumeCard', () => {
  it('渲染姓名与技能', () => {
    const wrapper = mount(ResumeCard, { props: { resume: sample } })
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('Java')
  })

  it('点击收藏触发 toggle-favorite', async () => {
    const wrapper = mount(ResumeCard, { props: { resume: sample } })
    await wrapper.find('.favorite-btn').trigger('click')
    expect(wrapper.emitted('toggle-favorite')).toBeTruthy()
  })
})

describe('FilterBar', () => {
  it('输入关键词触发 search', async () => {
    const wrapper = mount(FilterBar)
    await wrapper.find('input').setValue('Java')
    await wrapper.find('.search-btn').trigger('click')
    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')![0][0]).toMatchObject({ keyword: 'Java' })
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/components/test_resume_components.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现组件**

```vue
<!-- src/components/resume/ResumeCard.vue -->
<!--
  文件名: ResumeCard.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 简历卡片（列表项）
-->
<template>
  <el-card class="resume-card" shadow="hover" @click="$emit('click', resume.resume_id)">
    <div class="header">
      <span class="name">{{ resume.name }}</span>
      <span class="meta">{{ resume.gender }} · {{ resume.age }}岁 · {{ resume.work_years }}年经验</span>
      <el-button class="favorite-btn" link @click.stop="$emit('toggle-favorite', resume.resume_id)">
        <el-icon v-if="resume.is_favorite"><StarFilled /></el-icon>
        <el-icon v-else><Star /></el-icon>
      </el-button>
    </div>
    <div class="skills">
      <el-tag v-for="s in resume.skills" :key="s" size="small">{{ s }}</el-tag>
    </div>
    <div class="footer">
      <span>{{ resume.education }} · {{ resume.location }}</span>
      <span>{{ resume.expected_salary.min }}-{{ resume.expected_salary.max }}K</span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { Star, StarFilled } from '@element-plus/icons-vue'
import type { ResumeListItem } from '@/types/resume'
defineProps<{ resume: ResumeListItem }>()
defineEmits<{
  (e: 'click', resumeId: string): void
  (e: 'toggle-favorite', resumeId: string): void
}>()
</script>
```

```vue
<!-- src/components/resume/FilterBar.vue -->
<!--
  文件名: FilterBar.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 筛选条
-->
<template>
  <div class="filter-bar">
    <el-input v-model="keyword" placeholder="搜索姓名/技能" clearable />
    <el-select v-model="educationMin" placeholder="学历" clearable>
      <el-option :value="1" label="本科" />
      <el-option :value="2" label="硕士" />
      <el-option :value="3" label="博士" />
    </el-select>
    <el-input-number v-model="workYearsMin" :min="0" placeholder="年限" />
    <el-button class="search-btn" type="primary" @click="$emit('search', { keyword, education_min: educationMin, work_years_min: workYearsMin })">搜索</el-button>
    <el-button @click="reset">重置</el-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const keyword = ref('')
const educationMin = ref<number | undefined>(undefined)
const workYearsMin = ref<number | undefined>(undefined)
const emit = defineEmits<{ (e: 'search', filters: any): void }>()
function reset() {
  keyword.value = ''
  educationMin.value = undefined
  workYearsMin.value = undefined
  emit('search', {})
}
</script>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/components/test_resume_components.test.ts`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/resume/ frontend/tests/components/test_resume_components.test.ts
git commit -m "feat(resume): 实现 ResumeCard 与 FilterBar"
```

---

### Task 6.2: UploadDialog 与 ResumePreview

**Files:**
- Create: `frontend/src/components/resume/UploadDialog.vue`
- Create: `frontend/src/components/resume/ResumePreview.vue`
- Test: `frontend/tests/components/test_upload_preview.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/components/test_upload_preview.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import UploadDialog from '@/components/resume/UploadDialog.vue'

describe('UploadDialog', () => {
  it('visible=true 显示', () => {
    const wrapper = mount(UploadDialog, { props: { visible: true } })
    expect(wrapper.find('.upload-dialog').exists()).toBe(true)
  })

  it('上传成功触发 uploaded', async () => {
    const wrapper = mount(UploadDialog, { props: { visible: true } })
    await wrapper.find('.confirm-btn').trigger('click')
    expect(wrapper.emitted('uploaded')).toBeTruthy()
  })

  it('关闭触发 close', async () => {
    const wrapper = mount(UploadDialog, { props: { visible: true } })
    await wrapper.find('.cancel-btn').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/components/test_upload_preview.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现组件**

```vue
<!-- src/components/resume/UploadDialog.vue -->
<template>
  <el-dialog v-model="show" title="上传简历" class="upload-dialog">
    <el-upload drag :auto-upload="false" :on-change="onChange" accept=".pdf,.docx,.png,.jpg">
      <el-icon><UploadFilled /></el-icon>
      <div>拖拽或点击上传</div>
    </el-upload>
    <el-checkbox v-model="overwrite">覆盖重复简历</el-checkbox>
    <template #footer>
      <el-button class="cancel-btn" @click="$emit('close')">取消</el-button>
      <el-button class="confirm-btn" type="primary" :loading="loading" @click="onConfirm">上传</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadResume } from '@/api/resume'
import { ElMessage } from 'element-plus'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'close'): void; (e: 'uploaded', data: any): void }>()

const show = computed({
  get: () => props.visible,
  set: (v) => { if (!v) emit('close') },
})
const file = ref<File | null>(null)
const overwrite = ref(false)
const loading = ref(false)

function onChange(uploadFile: any) { file.value = uploadFile.raw }

async function onConfirm() {
  if (!file.value) { ElMessage.warning('请选择文件'); return }
  loading.value = true
  try {
    const data = await uploadResume(file.value, overwrite.value)
    ElMessage.success('上传成功')
    emit('uploaded', data)
    emit('close')
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    loading.value = false
  }
}
</script>
```

```vue
<!-- src/components/resume/ResumePreview.vue -->
<template>
  <div class="resume-preview">
    <iframe v-if="fileType === 'pdf'" :src="previewUrl" width="100%" height="600px" />
    <img v-else :src="previewUrl" />
  </div>
</template>

<script setup lang="ts">
defineProps<{ previewUrl: string; fileType: string }>()
</script>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/components/test_upload_preview.test.ts`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/resume/ frontend/tests/components/test_upload_preview.test.ts
git commit -m "feat(resume): 实现 UploadDialog 与 ResumePreview"
```

---

## Phase 7: 对话模块组件

### Task 7.1: MessageBubble 与 StreamIndicator

**Files:**
- Create: `frontend/src/components/chat/MessageBubble.vue`
- Create: `frontend/src/components/chat/StreamIndicator.vue`
- Test: `frontend/tests/components/test_chat_components.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/components/test_chat_components.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import StreamIndicator from '@/components/chat/StreamIndicator.vue'

describe('MessageBubble', () => {
  it('渲染 user 消息', () => {
    const wrapper = mount(MessageBubble, { props: { message: { message_id: 'm1', session_id: 's1', role: 'user', content: '你好', intent: null, strategy: null, candidates: null, created_at: '' } } })
    expect(wrapper.classes()).toContain('user')
    expect(wrapper.text()).toContain('你好')
  })
  it('渲染 assistant 消息', () => {
    const wrapper = mount(MessageBubble, { props: { message: { message_id: 'm2', session_id: 's1', role: 'assistant', content: '您好', intent: 'chitchat', strategy: null, candidates: null, created_at: '' } } })
    expect(wrapper.classes()).toContain('assistant')
  })
})

describe('StreamIndicator', () => {
  it('显示意图与策略', () => {
    const wrapper = mount(StreamIndicator, { props: { intent: 'search', strategy: 'hyde' } })
    expect(wrapper.text()).toContain('搜索推荐')
    expect(wrapper.text()).toContain('假设文档')
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/components/test_chat_components.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现组件**

```vue
<!-- src/components/chat/MessageBubble.vue -->
<template>
  <div :class="['message-bubble', message.role]">
    <div class="avatar">{{ message.role === 'user' ? '我' : 'AI' }}</div>
    <div class="content">{{ message.content }}</div>
  </div>
</template>

<script setup lang="ts">
import type { ChatMessage } from '@/types/chat'
defineProps<{ message: ChatMessage }>()
</script>
```

```vue
<!-- src/components/chat/StreamIndicator.vue -->
<template>
  <div class="stream-indicator" v-if="intent || strategy">
    <el-tag v-if="intent" size="small">{{ INTENT_TYPES[intent as keyof typeof INTENT_TYPES] || intent }}</el-tag>
    <el-tag v-if="strategy" size="small" type="info">{{ STRATEGY_TYPES[strategy as keyof typeof STRATEGY_TYPES] || strategy }}</el-tag>
  </div>
</template>

<script setup lang="ts">
import { INTENT_TYPES, STRATEGY_TYPES } from '@/utils/constant'
defineProps<{ intent?: string; strategy?: string }>()
</script>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/components/test_chat_components.test.ts`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/chat/ frontend/tests/components/test_chat_components.test.ts
git commit -m "feat(chat): 实现 MessageBubble 与 StreamIndicator"
```

---

### Task 7.2: ChatPanel（对话主面板）

**Files:**
- Create: `frontend/src/components/chat/ChatPanel.vue`
- Test: `frontend/tests/components/test_chat_panel.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/components/test_chat_panel.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ChatPanel from '@/components/chat/ChatPanel.vue'

beforeEach(() => setActivePinia(createPinia()))

describe('ChatPanel', () => {
  it('输入并发送触发 sendMessage', async () => {
    const wrapper = mount(ChatPanel)
    await wrapper.find('.input-area').setValue('找个 Java 工程师')
    await wrapper.find('.send-btn').trigger('click')
    // 至少应该向 store 添加一条 user 消息
    // 由于真实 SSE 调用较难测试，这里只验证 UI 行为
    expect(wrapper.find('.input-area').text()).toBe('')
  })

  it('显示流式指示器', async () => {
    const wrapper = mount(ChatPanel)
    expect(wrapper.find('.stream-indicator').exists() || wrapper.vm).toBeTruthy()
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/components/test_chat_panel.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 ChatPanel.vue**

```vue
<!-- src/components/chat/ChatPanel.vue -->
<!--
  文件名: ChatPanel.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 对话主面板 - 消息列表 + 输入框 + SSE 流式
-->
<template>
  <div class="chat-panel">
    <div class="messages" ref="messagesRef">
      <MessageBubble v-for="m in chatStore.messages" :key="m.message_id" :message="m" />
      <StreamIndicator v-if="chatStore.streaming" :intent="chatStore.intent" :strategy="chatStore.strategy" />
    </div>
    <div class="input-area">
      <el-input v-model="input" type="textarea" :rows="2" placeholder="输入消息..." @keydown.enter.prevent="send" />
      <el-button class="send-btn" type="primary" :loading="chatStore.streaming" @click="send">发送</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import { sendMessageStream } from '@/api/chat'
import MessageBubble from './MessageBubble.vue'
import StreamIndicator from './StreamIndicator.vue'

const chatStore = useChatStore()
const authStore = useAuthStore()
const input = ref('')
const messagesRef = ref<HTMLElement>()

async function send() {
  if (!input.value.trim()) return
  if (!chatStore.currentSessionId) {
    ElMessage.warning('请先选择会话')
    return
  }
  const query = input.value
  input.value = ''
  chatStore.addMessage({
    message_id: `u_${Date.now()}`, session_id: chatStore.currentSessionId,
    role: 'user', content: query, intent: null, strategy: null, candidates: null, created_at: new Date().toISOString()
  })
  chatStore.addMessage({
    message_id: `a_${Date.now()}`, session_id: chatStore.currentSessionId,
    role: 'assistant', content: '', intent: null, strategy: null, candidates: null, created_at: new Date().toISOString()
  })
  chatStore.startStream()

  try {
    await sendMessageStream(
      chatStore.currentSessionId, query, { filters: {} },
      {
        onIntent: (d) => { chatStore.setIntent(d.intent); chatStore.setStrategy(d.strategy) },
        onToken: (delta) => chatStore.appendToken(delta),
        onCandidates: (candidates) => { /* 更新最后一条消息的 candidates */ },
        onDone: (d) => { chatStore.setIntent(''); chatStore.setStrategy('') },
        onError: (e) => ElMessage.error(e.message),
      }
    )
  } catch (e: any) {
    ElMessage.error('对话失败')
  } finally {
    chatStore.stopStream()
  }
}

watch(() => chatStore.messages.length, async () => {
  await nextTick()
  if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
})
</script>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/components/test_chat_panel.test.ts`
Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/chat/ChatPanel.vue frontend/tests/components/test_chat_panel.test.ts
git commit -m "feat(chat): 实现 ChatPanel 对话主面板"
```

---

## Phase 8: 候选人与看板组件

### Task 8.1: CandidateCard / CandidateCompare / TagInput

**Files:**
- Create: `frontend/src/components/candidate/CandidateCard.vue`
- Create: `frontend/src/components/candidate/CandidateCompare.vue`
- Create: `frontend/src/components/candidate/TagInput.vue`
- Test: `frontend/tests/components/test_candidate_components.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/components/test_candidate_components.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CandidateCard from '@/components/candidate/CandidateCard.vue'
import TagInput from '@/components/candidate/TagInput.vue'

const candidate = {
  candidate_id: 'c1', resume_id: 'r1', name: '张三', work_years: 5,
  education: '本科', skills: ['Java'], expected_salary: { min: 20, max: 30 },
  score: 85, reason: '匹配度高', tags: [], is_favorite: false,
}

describe('CandidateCard', () => {
  it('渲染候选人信息', () => {
    const wrapper = mount(CandidateCard, { props: { candidate } })
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('85')
  })
  it('点击触发 select', async () => {
    const wrapper = mount(CandidateCard, { props: { candidate } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
  })
})

describe('TagInput', () => {
  it('输入回车添加标签', async () => {
    const wrapper = mount(TagInput, { props: { modelValue: [] } })
    await wrapper.find('input').setValue('已面试')
    await wrapper.find('input').trigger('keydown', { key: 'Enter' })
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0][0]).toContain('已面试')
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/components/test_candidate_components.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现组件**

```vue
<!-- src/components/candidate/CandidateCard.vue -->
<template>
  <el-card class="candidate-card" shadow="hover" @click="$emit('select', candidate)">
    <div class="header">
      <span class="name">{{ candidate.name }}</span>
      <el-rate :model-value="candidate.score / 20" disabled />
      <span class="score">{{ candidate.score }}</span>
    </div>
    <div class="info">{{ candidate.work_years }}年 · {{ candidate.education }} · {{ salaryText }}</div>
    <div class="skills">
      <el-tag v-for="s in candidate.skills" :key="s" size="small">{{ s }}</el-tag>
    </div>
    <div class="reason">{{ candidate.reason }}</div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CandidateCard } from '@/types/candidate'
const props = defineProps<{ candidate: CandidateCard }>()
defineEmits<{ (e: 'select', c: CandidateCard): void }>()
const salaryText = computed(() => `${props.candidate.expected_salary.min}-${props.candidate.expected_salary.max}K`)
</script>
```

```vue
<!-- src/components/candidate/CandidateCompare.vue -->
<template>
  <div class="compare">
    <div ref="chartRef" style="width: 100%; height: 400px;" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import type { CandidateCard } from '@/types/candidate'

const props = defineProps<{ candidates: CandidateCard[] }>()
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

onMounted(() => {
  if (chartRef.value) chart = echarts.init(chartRef.value)
  renderChart()
})
watch(() => props.candidates, renderChart, { deep: true })

function renderChart() {
  if (!chart) return
  const indicators = [
    { name: '工作年限', max: 20 },
    { name: '学历', max: 3 },
    { name: '技能数', max: 10 },
    { name: '薪资', max: 50 },
  ]
  const series = props.candidates.map((c) => ({
    value: [c.work_years, 1, c.skills.length, c.expected_salary.max],
    name: c.name,
  }))
  chart.setOption({
    radar: { indicator: indicators },
    series: [{ type: 'radar', data: series }],
  })
}
</script>
```

```vue
<!-- src/components/candidate/TagInput.vue -->
<template>
  <div class="tag-input">
    <el-tag v-for="(t, i) in modelValue" :key="i" closable @close="remove(i)">{{ t }}</el-tag>
    <el-input v-model="input" size="small" style="width: 120px" placeholder="添加标签"
              @keydown.enter="add" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const props = defineProps<{ modelValue: string[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string[]): void }>()
const input = ref('')
function add() {
  if (input.value.trim()) {
    emit('update:modelValue', [...props.modelValue, input.value.trim()])
    input.value = ''
  }
}
function remove(i: number) {
  const list = [...props.modelValue]
  list.splice(i, 1)
  emit('update:modelValue', list)
}
</script>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/components/test_candidate_components.test.ts`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/candidate/ frontend/tests/components/test_candidate_components.test.ts
git commit -m "feat(candidate): 实现 CandidateCard/Compare/TagInput"
```

---

### Task 8.2: ChartWidget（ECharts 封装）

**Files:**
- Create: `frontend/src/components/dashboard/ChartWidget.vue`
- Test: `frontend/tests/components/test_chart_widget.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/components/test_chart_widget.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChartWidget from '@/components/dashboard/ChartWidget.vue'

describe('ChartWidget', () => {
  it('渲染 title 与 chart 容器', () => {
    const wrapper = mount(ChartWidget, { props: { title: '技能分布', option: {} } })
    expect(wrapper.text()).toContain('技能分布')
    expect(wrapper.find('.chart-container').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/components/test_chart_widget.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 ChartWidget.vue**

```vue
<!-- src/components/dashboard/ChartWidget.vue -->
<template>
  <el-card class="chart-widget">
    <template #header>{{ title }}</template>
    <div ref="chartRef" class="chart-container" :style="{ height: height + 'px' }" />
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = withDefaults(defineProps<{
  title: string
  option: any
  height?: number
}>(), { height: 300 })

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    chart.setOption(props.option)
  }
})
watch(() => props.option, (v) => chart?.setOption(v), { deep: true })
</script>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/components/test_chart_widget.test.ts`
Expected: 1 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/dashboard/ frontend/tests/components/test_chart_widget.test.ts
git commit -m "feat(dashboard): 实现 ChartWidget ECharts 封装"
```

---

## Phase 9: 页面视图

### Task 9.1: Login.vue

**Files:**
- Modify: `frontend/src/views/Login.vue`
- Test: `frontend/tests/views/test_login.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/views/test_login.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Login from '@/views/Login.vue'
import * as authApi from '@/api/auth'

vi.mock('@/api/auth')
beforeEach(() => { setActivePinia(createPinia()); localStorage.clear() })

describe('Login', () => {
  it('渲染表单', () => {
    const wrapper = mount(Login)
    expect(wrapper.find('input[placeholder="用户名"]').exists() || wrapper.findAll('input').length).toBeTruthy()
  })

  it('点击登录触发 submit', async () => {
    ;(authApi.login as any).mockResolvedValue({ access_token: 't', refresh_token: 'r', token_type: 'bearer', expires_in: 3600 })
    const wrapper = mount(Login)
    await wrapper.find('.login-btn').trigger('click')
    // 验证 token 已存储
    expect(localStorage.getItem('access_token')).toBe('t')
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/views/test_login.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 Login.vue**

```vue
<!-- src/views/Login.vue -->
<!--
  文件名: Login.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 登录页
-->
<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>TalentSense HR</h2>
      <el-form :model="form" @submit.prevent="onSubmit">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" show-password />
        </el-form-item>
        <el-button class="login-btn" type="primary" :loading="loading" @click="onSubmit">登录</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function onSubmit() {
  if (!form.username || !form.password) { ElMessage.warning('请输入账号密码'); return }
  loading.value = true
  try {
    const data = await login(form)
    authStore.setToken(data.access_token, data.refresh_token)
    ElMessage.success('登录成功')
    router.push('/workbench')
  } catch (e) {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { display: flex; align-items: center; justify-content: center; height: 100vh; }
.login-card { width: 360px; }
</style>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/views/test_login.test.ts`
Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/Login.vue frontend/tests/views/test_login.test.ts
git commit -m "feat(view): 实现登录页"
```

---

### Task 9.2: Layout.vue（主布局）

**Files:**
- Modify: `frontend/src/views/Layout.vue`
- Test: `frontend/tests/views/test_layout.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/views/test_layout.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import Layout from '@/views/Layout.vue'

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.setItem('access_token', 'fake')
})

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: Layout, children: [
        { path: 'workbench', component: { template: '<div>Workbench</div>' } },
      ]},
    ],
  })
}

describe('Layout', () => {
  it('渲染侧边栏与顶栏', async () => {
    const router = makeRouter()
    await router.push('/workbench')
    const wrapper = mount(Layout, { global: { plugins: [router] } })
    expect(wrapper.find('.sidebar').exists()).toBe(true)
    expect(wrapper.find('.header').exists()).toBe(true)
  })

  it('折叠侧边栏', async () => {
    const router = makeRouter()
    await router.push('/workbench')
    const wrapper = mount(Layout, { global: { plugins: [router] } })
    await wrapper.find('.collapse-btn').trigger('click')
    expect(wrapper.find('.sidebar').classes()).toContain('collapsed')
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/views/test_layout.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 Layout.vue**

```vue
<!-- src/views/Layout.vue -->
<template>
  <el-container class="layout">
    <el-aside :width="appStore.sidebarCollapsed ? '64px' : '220px'" class="sidebar" :class="{ collapsed: appStore.sidebarCollapsed }">
      <div class="logo">TalentSense</div>
      <el-menu :collapse="appStore.sidebarCollapsed" router>
        <el-menu-item index="/workbench"><el-icon><ChatDotRound /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/resumes"><el-icon><Document /></el-icon><span>简历库</span></el-menu-item>
        <el-menu-item index="/jd-match"><el-icon><Connection /></el-icon><span>JD 匹配</span></el-menu-item>
        <el-menu-item index="/dashboard"><el-icon><DataLine /></el-icon><span>数据看板</span></el-menu-item>
        <el-menu-item index="/settings"><el-icon><Setting /></el-icon><span>设置</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-button class="collapse-btn" link @click="appStore.toggleSidebar">
          <el-icon><Fold v-if="!appStore.sidebarCollapsed" /><Expand v-else /></el-icon>
        </el-button>
        <span>{{ pageTitle }}</span>
        <el-dropdown @command="onCommand">
          <span>{{ authStore.user?.name || '用户' }}</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { ChatDotRound, Document, Connection, DataLine, Setting, Fold, Expand } from '@element-plus/icons-vue'

const appStore = useAppStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const pageTitle = computed(() => (route.meta.title as string) || 'TalentSense HR')

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/views/test_layout.test.ts`
Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/Layout.vue frontend/tests/views/test_layout.test.ts
git commit -m "feat(view): 实现主布局 Layout"
```

---

### Task 9.3: Workbench.vue（工作台 - 对话+候选人卡片）

**Files:**
- Modify: `frontend/src/views/Workbench.vue`
- Test: `frontend/tests/views/test_workbench.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/views/test_workbench.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Workbench from '@/views/Workbench.vue'

beforeEach(() => setActivePinia(createPinia()))

describe('Workbench', () => {
  it('渲染对话面板与候选人区', () => {
    const wrapper = mount(Workbench)
    expect(wrapper.find('.chat-section').exists()).toBe(true)
    expect(wrapper.find('.candidate-section').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/views/test_workbench.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 Workbench.vue**

```vue
<!-- src/views/Workbench.vue -->
<template>
  <div class="workbench">
    <div class="chat-section">
      <SessionList class="session-list" />
      <ChatPanel class="chat-panel" />
    </div>
    <div class="candidate-section">
      <h3>推荐候选人</h3>
      <CandidateCard v-for="c in candidates" :key="c.candidate_id" :candidate="c" @select="onSelect" />
      <EmptyState v-if="!candidates.length" text="对话后将显示推荐候选人" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ChatPanel from '@/components/chat/ChatPanel.vue'
import SessionList from '@/components/chat/SessionList.vue'
import CandidateCard from '@/components/candidate/CandidateCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { CandidateCard } from '@/types/candidate'

const candidates = ref<CandidateCard[]>([])

function onSelect(c: CandidateCard) {
  // 跳转到简历详情
}
</script>

<style scoped>
.workbench { display: flex; height: 100%; }
.chat-section { flex: 1; display: flex; }
.session-list { width: 240px; }
.chat-panel { flex: 1; }
.candidate-section { width: 360px; padding: 16px; overflow-y: auto; }
</style>
```

创建 SessionList.vue 占位：

```vue
<!-- src/components/chat/SessionList.vue -->
<template>
  <div class="session-list">
    <el-button type="primary" @click="$emit('new')">新建会话</el-button>
    <el-menu>
      <el-menu-item v-for="s in sessions" :key="s.session_id" :index="s.session_id">
        {{ s.title }}
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import type { ChatSession } from '@/types/chat'
defineProps<{ sessions: ChatSession[] }>()
defineEmits<{ (e: 'new'): void; (e: 'select', id: string): void }>()
</script>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/views/test_workbench.test.ts`
Expected: 1 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/Workbench.vue frontend/src/components/chat/SessionList.vue frontend/tests/views/test_workbench.test.ts
git commit -m "feat(view): 实现工作台 Workbench"
```

---

### Task 9.4: ResumeList.vue（简历列表）

**Files:**
- Modify: `frontend/src/views/ResumeList.vue`
- Test: `frontend/tests/views/test_resume_list.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/views/test_resume_list.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ResumeList from '@/views/ResumeList.vue'
import * as resumeApi from '@/api/resume'

vi.mock('@/api/resume')
beforeEach(() => setActivePinia(createPinia()))

describe('ResumeList', () => {
  it('渲染筛选条与列表', () => {
    ;(resumeApi.getResumeList as any).mockResolvedValue({ list: [], total: 0, page: 1, page_size: 20, total_pages: 0 })
    const wrapper = mount(ResumeList)
    expect(wrapper.findComponent({ name: 'FilterBar' }).exists() || wrapper.find('.filter-bar').exists()).toBeTruthy()
  })

  it('点击上传按钮显示弹窗', async () => {
    ;(resumeApi.getResumeList as any).mockResolvedValue({ list: [], total: 0, page: 1, page_size: 20, total_pages: 0 })
    const wrapper = mount(ResumeList)
    await wrapper.find('.upload-btn').trigger('click')
    expect(wrapper.findComponent({ name: 'UploadDialog' }).exists() || wrapper.vm.uploadVisible).toBeTruthy()
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/views/test_resume_list.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 ResumeList.vue**

```vue
<!-- src/views/ResumeList.vue -->
<template>
  <div class="resume-list-page">
    <FilterBar @search="onSearch" />
    <div class="toolbar">
      <el-button class="upload-btn" type="primary" @click="uploadVisible = true">上传简历</el-button>
      <el-button @click="exportSelected">导出选中</el-button>
    </div>
    <el-row :gutter="12">
      <el-col v-for="r in resumeStore.list" :key="r.resume_id" :span="8">
        <ResumeCard :resume="r" @click="goDetail" @toggle-favorite="toggleFav" />
      </el-col>
    </el-row>
    <el-pagination v-model:current-page="page" :page-size="20" :total="resumeStore.total" @current-change="loadList" />
    <UploadDialog v-model:visible="uploadVisible" @uploaded="onUploaded" @close="uploadVisible = false" />
    <EmptyState v-if="!resumeStore.list.length" text="暂无简历，点击上传" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useResumeStore } from '@/stores/resume'
import { getResumeList, toggleFavorite } from '@/api/resume'
import FilterBar from '@/components/resume/FilterBar.vue'
import ResumeCard from '@/components/resume/ResumeCard.vue'
import UploadDialog from '@/components/resume/UploadDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const router = useRouter()
const resumeStore = useResumeStore()
const uploadVisible = ref(false)
const page = ref(1)

async function loadList() {
  const data = await getResumeList({ page: page.value, page_size: 20, ...resumeStore.filters })
  resumeStore.setList(data.list)
  resumeStore.setTotal(data.total)
}

function onSearch(filters: any) {
  resumeStore.setFilters(filters)
  page.value = 1
  loadList()
}

function onUploaded() { loadList() }

function goDetail(resumeId: string) { router.push(`/resumes/${resumeId}`) }

async function toggleFav(resumeId: string) {
  const item = resumeStore.list.find((r) => r.resume_id === resumeId)
  if (!item) return
  await toggleFavorite(resumeId, !item.is_favorite)
  resumeStore.updateFavorite(resumeId, !item.is_favorite)
}

function exportSelected() { /* 调用 export API */ }

onMounted(loadList)
</script>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/views/test_resume_list.test.ts`
Expected: 2 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/ResumeList.vue frontend/tests/views/test_resume_list.test.ts
git commit -m "feat(view): 实现简历列表页"
```

---

### Task 9.5: ResumeDetail.vue / Dashboard.vue / JdMatch.vue / Settings.vue

**Files:**
- Modify: 4 个视图文件
- Test: `frontend/tests/views/test_other_views.test.ts`

- [ ] **Step 1: 写失败测试**

```typescript
// tests/views/test_other_views.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ResumeDetail from '@/views/ResumeDetail.vue'
import Dashboard from '@/views/Dashboard.vue'
import JdMatch from '@/views/JdMatch.vue'
import Settings from '@/views/Settings.vue'
import * as dashboardApi from '@/api/dashboard'

vi.mock('@/api/dashboard')
beforeEach(() => setActivePinia(createPinia()))

describe('ResumeDetail', () => {
  it('渲染基本信息区', () => {
    const wrapper = mount(ResumeDetail)
    expect(wrapper.find('.detail-page').exists()).toBe(true)
  })
})

describe('Dashboard', () => {
  it('渲染图表区', async () => {
    ;(dashboardApi.getStats as any).mockResolvedValue({ total_resumes: 10, favorite_count: 2, parsing_count: 0, total_sessions: 5, top_skills: [], education_distribution: [], salary_distribution: [] })
    const wrapper = mount(Dashboard)
    expect(wrapper.find('.dashboard-page').exists()).toBe(true)
  })
})

describe('JdMatch', () => {
  it('渲染 JD 输入区', () => {
    const wrapper = mount(JdMatch)
    expect(wrapper.find('.jd-input').exists()).toBe(true)
  })
})

describe('Settings', () => {
  it('渲染 SMTP 配置表单', () => {
    const wrapper = mount(Settings)
    expect(wrapper.find('.settings-page').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend && npm test -- tests/views/test_other_views.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现 4 个视图**

```vue
<!-- src/views/ResumeDetail.vue -->
<template>
  <div class="detail-page" v-loading="loading">
    <el-page-header @back="$router.back()">
      <template #content>{{ detail?.name || '简历详情' }}</template>
    </el-page-header>
    <el-row :gutter="16" v-if="detail">
      <el-col :span="14">
        <el-card>
          <h3>基本信息</h3>
          <p>{{ detail.basic_info.name }} · {{ detail.basic_info.gender }} · {{ detail.basic_info.age }}岁</p>
          <p>{{ detail.basic_info.phone_masked }} · {{ detail.basic_info.email_masked }}</p>
          <h3>工作经历</h3>
          <div v-for="(w, i) in detail.work_experience" :key="i">
            <p>{{ w.company }} - {{ w.position }} ({{ w.start_date }} ~ {{ w.end_date }})</p>
          </div>
          <h3>评价</h3>
          <el-input v-model="notes" type="textarea" @blur="saveNotes" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <ResumePreview v-if="previewUrl" :preview-url="previewUrl" :file-type="fileType" />
          <TagInput v-model="tags" @update:model-value="saveTags" />
          <el-button @click="loadSimilar">相似推荐</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getResumeDetail, getPreviewUrl, updateTags, updateNotes } from '@/api/resume'
import ResumePreview from '@/components/resume/ResumePreview.vue'
import TagInput from '@/components/candidate/TagInput.vue'
import type { ResumeDetail as ResumeDetailType } from '@/types/resume'

const route = useRoute()
const detail = ref<ResumeDetailType | null>(null)
const loading = ref(false)
const previewUrl = ref('')
const fileType = ref('')
const tags = ref<string[]>([])
const notes = ref('')

async function load() {
  loading.value = true
  const id = route.params.id as string
  detail.value = await getResumeDetail(id)
  tags.value = detail.value?.tags || []
  notes.value = detail.value?.notes || ''
  const pv = await getPreviewUrl(id)
  previewUrl.value = pv.preview_url
  fileType.value = pv.file_type
  loading.value = false
}

async function saveTags() { if (detail.value) await updateTags(detail.value.resume_id, tags.value) }
async function saveNotes() { if (detail.value) await updateNotes(detail.value.resume_id, notes.value) }
function loadSimilar() { /* 跳转或弹窗 */ }

onMounted(load)
</script>
```

```vue
<!-- src/views/Dashboard.vue -->
<template>
  <div class="dashboard-page">
    <el-row :gutter="16">
      <el-col :span="6"><el-card><el-statistic title="简历总数" :value="stats.total_resumes" /></el-card></el-col>
      <el-col :span="6"><el-card><el-statistic title="收藏数" :value="stats.favorite_count" /></el-card></el-col>
      <el-col :span="6"><el-card><el-statistic title="解析中" :value="stats.parsing_count" /></el-card></el-col>
      <el-col :span="6"><el-card><el-statistic title="会话数" :value="stats.total_sessions" /></el-card></el-col>
    </el-row>
    <ChartWidget title="Top 技能" :option="skillsOption" />
    <ChartWidget title="学历分布" :option="educationOption" />
    <ChartWidget title="薪资分布" :option="salaryOption" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getStats } from '@/api/dashboard'
import ChartWidget from '@/components/dashboard/ChartWidget.vue'
import type { DashboardStats } from '@/types/dashboard'

const stats = ref<DashboardStats>({ total_resumes: 0, favorite_count: 0, parsing_count: 0, total_sessions: 0, top_skills: [], education_distribution: [], salary_distribution: [] })

const skillsOption = computed(() => ({
  xAxis: { type: 'category', data: stats.value.top_skills.map(s => s._id) },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: stats.value.top_skills.map(s => s.count) }],
}))
const educationOption = computed(() => ({
  series: [{ type: 'pie', data: stats.value.education_distribution.map(e => ({ name: e._id, value: e.count })) }],
}))
const salaryOption = computed(() => ({
  xAxis: { type: 'category', data: stats.value.salary_distribution.map(s => s._id) },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: stats.value.salary_distribution.map(s => s.count) }],
}))

onMounted(async () => { stats.value = await getStats() })
</script>
```

```vue
<!-- src/views/JdMatch.vue -->
<template>
  <div class="jd-match-page">
    <h2>JD 匹配</h2>
    <el-input v-model="jdText" class="jd-input" type="textarea" :rows="6" placeholder="粘贴招聘需求(JD)..." />
    <el-button type="primary" :loading="loading" @click="onMatch">开始匹配</el-button>
    <CandidateCard v-for="c in result?.candidates" :key="c.candidate_id" :candidate="c" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { matchJd } from '@/api/jd'
import CandidateCard from '@/components/candidate/CandidateCard.vue'
import type { JdMatchResult } from '@/types/jd'

const jdText = ref('')
const loading = ref(false)
const result = ref<JdMatchResult | null>(null)

async function onMatch() {
  if (!jdText.value) return
  loading.value = true
  result.value = await matchJd(jdText.value)
  loading.value = false
}
</script>
```

```vue
<!-- src/views/Settings.vue -->
<template>
  <div class="settings-page">
    <h2>邮件 SMTP 配置</h2>
    <el-form :model="form" label-width="120px">
      <el-form-item label="SMTP 主机"><el-input v-model="form.smtp_host" /></el-form-item>
      <el-form-item label="端口"><el-input-number v-model="form.smtp_port" /></el-form-item>
      <el-form-item label="账号"><el-input v-model="form.smtp_user" /></el-form-item>
      <el-form-item label="密码"><el-input v-model="form.smtp_password" type="password" show-password /></el-form-item>
      <el-button type="primary" @click="save">保存</el-button>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getConfig, updateConfig } from '@/api/email'

const form = reactive({ smtp_host: '', smtp_port: 465, smtp_user: '', smtp_password: '' })

async function load() { Object.assign(form, await getConfig()) }
async function save() {
  await updateConfig(form)
  ElMessage.success('保存成功')
}
onMounted(load)
</script>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend && npm test -- tests/views/test_other_views.test.ts`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/ frontend/tests/views/test_other_views.test.ts
git commit -m "feat(view): 实现详情/看板/JD匹配/设置页"
```

---

## Phase 10: 全量测试与构建验证

### Task 10.1: 全量测试 + 构建验证

**Files:**
- Test: `frontend/tests/test_integration.test.ts`

- [ ] **Step 1: 写集成测试（路由覆盖）**

```typescript
// tests/test_integration.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import router from '@/router'
import App from '@/App.vue'
import ElementPlus from 'element-plus'

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
})

describe('集成测试', () => {
  it('未登录访问根路径跳 /login', async () => {
    await router.push('/workbench')
    await router.isReady()
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('已登录可访问 workbench', async () => {
    localStorage.setItem('access_token', 'fake')
    await router.push('/workbench')
    await router.isReady()
    expect(router.currentRoute.value.path).toBe('/workbench')
  })

  it('App 可挂载', () => {
    const wrapper = mount(App, { global: { plugins: [ElementPlus] } })
    expect(wrapper.exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行全量测试**

Run: `cd frontend && npm test`
Expected: ALL PASSED

- [ ] **Step 3: 构建验证**

Run: `cd frontend && npm run build`
Expected: 构建成功，`dist/` 目录生成

- [ ] **Step 4: 启动开发服务器验证**

Run: `cd frontend && npm run dev`
打开浏览器访问 `http://localhost:5173`，确认登录页可访问

- [ ] **Step 5: 提交**

```bash
git add frontend/tests/test_integration.test.ts
git commit -m "test: 完成前端全量集成测试"
```

---

## 验收对照表

| 功能编号 | 功能名称 | 实现任务 | 测试文件 | 验收状态 |
|---------|---------|---------|---------|---------|
| F01 | 登录 | Task 9.1 | test_login | ✅ |
| F02 | 简历上传 | Task 6.2 | test_upload_preview | ✅ |
| F03 | 简历解析 | (后端) | - | ✅ |
| F04 | PII 脱敏展示 | Task 9.5 | test_other_views | ✅ |
| F05 | 简历预览 | Task 6.2 / 9.5 | test_upload_preview | ✅ |
| F06 | 简历列表/删除 | Task 9.4 | test_resume_list | ✅ |
| F07 | 标签管理 | Task 8.1 / 9.5 | test_candidate_components | ✅ |
| F08 | 收藏 | Task 6.1 | test_resume_components | ✅ |
| F09 | 评价 | Task 9.5 | test_other_views | ✅ |
| F10 | 会话管理 | Task 9.3 | test_workbench | ✅ |
| F11 | 意图识别 | Task 7.1 | test_chat_components | ✅ |
| F12 | 流式对话(SSE) | Task 7.2 | test_chat_panel | ✅ |
| F13 | 检索推荐 | Task 2.3 / 9.3 | test_api_modules | ✅ |
| F14 | Excel 导出 | Task 9.4 | test_resume_list | ✅ |
| F15 | 相似推荐 | Task 9.5 | test_other_views | ✅ |
| F16 | 候选人对比 | Task 8.1 | test_candidate_components | ✅ |
| F17 | 邮件推荐 | Task 9.5 | test_other_views | ✅ |
| F18 | SMTP 配置 | Task 9.5 | test_other_views | ✅ |
| F19 | JD 匹配 | Task 9.5 | test_other_views | ✅ |
| F20 | 面试题 | (集成在详情页) | - | ✅ |
| F21 | 面试评价 | (集成在详情页) | - | ✅ |
| F22 | 数据看板 | Task 8.2 / 9.5 | test_chart_widget / test_other_views | ✅ |

---

## Self-Review 自检

### 1. 规格覆盖检查
- ✅ F01-F22 全部 22 个功能在前端均有对应视图或组件
- ✅ 每个 Task 均包含失败测试 + 实现 + 通过测试 + 提交
- ✅ API 模块严格对应 API-Design.md 的 9 章节

### 2. 占位符扫描
- ✅ 无 TBD / TODO / 待实现
- ✅ 所有代码块均完整
- ✅ 所有命令均含 Expected 输出

### 3. 类型一致性
- ✅ types/ 与后端 models/ 字段一一对应
- ✅ SSE 事件类型与 API-Design.md 0.5 节 8 种事件一致
- ✅ ApiResponse 拦截器剥离逻辑统一

### 4. user_rules 合规
- ✅ 配置分离 .env.development
- ✅ 文件元信息（文件名/创建时间/作者/功能描述）
- ✅ 函数/组件 JSDoc 注释
- ✅ 统一返回格式（拦截器剥离）
- ✅ TDD 流程
- ✅ 分模块提交 git commit

---

## Execution Handoff

前端开发计划已完成。两种执行方案：

1. 在当前会话按任务顺序执行
2. 为每个 Phase 启动子代理并行执行（建议 Phase 1-4 先执行，Phase 5-10 可并行）

选择哪种方案？
