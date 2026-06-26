# TalentSense HR 简历推荐系统 - 前端开发文档

**版本**：v2.5
**日期**：2026-06-26
**对接文档**：[API-Design.md](./API-Design.md)（接口契约）、[MVP-Design.md](./MVP-Design.md)（需求设计）

> 前端实现严格遵循 [API-Design.md](./API-Design.md) 中定义的端点、请求/响应结构与枚举值。本文档描述页面结构、组件设计、状态管理、API 调用层与 SSE 流式处理实现。

---

## 一、技术栈

| 组件 | 选型 | 版本 | 用途 |
|------|------|------|------|
| 框架 | Vue 3 | 3.4+ | Composition API |
| 语言 | TypeScript | 5.0+ | 类型安全 |
| 构建 | Vite | 5.0+ | 开发/构建 |
| UI 库 | Element Plus | 2.6+ | 企业级组件 |
| 状态管理 | Pinia | 2.1+ | 全局状态 |
| 路由 | Vue Router | 4.2+ | SPA 路由 |
| HTTP | Axios | 1.6+ | API 请求 |
| SSE | fetch + ReadableStream | 原生 | 对话流式（不用 EventSource，支持 POST） |
| 图表 | ECharts | 5.5+ | 数据看板 |
| PDF 预览 | PDF.js | 4.0+ | 简历预览（不做 bbox 高亮） |
| 富文本 | 无 | - | 评价用 textarea |
| 样式 | SCSS | - | 主题变量 |

---

## 二、目录结构

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
│   │   ├── resume.ts                 # ResumeListItem/ResumeDetail
│   │   ├── chat.ts                   # ChatMessage/SSEEvent
│   │   ├── candidate.ts             # CandidateCard
│   │   ├── email.ts
│   │   ├── jd.ts
│   │   ├── interview.ts
│   │   └── dashboard.ts
│   ├── views/                        # 页面
│   │   ├── Login.vue                 # 登录页
│   │   ├── Layout.vue                # 主布局(侧边栏+顶栏+内容区)
│   │   ├── Workbench.vue             # 工作台(对话+候选人卡片联动)
│   │   ├── ResumeList.vue            # 简历列表管理
│   │   ├── ResumeDetail.vue          # 简历详情+PDF预览+相似推荐
│   │   ├── Dashboard.vue             # 数据看板(ECharts)
│   │   ├── JdMatch.vue               # JD 匹配页
│   │   └── Settings.vue              # 邮件配置/系统设置
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatPanel.vue         # 对话面板(消息列表+输入框)
│   │   │   ├── MessageBubble.vue     # 消息气泡(user/assistant)
│   │   │   ├── SessionList.vue       # 会话列表侧边栏
│   │   │   └── StreamIndicator.vue   # 流式状态指示(意图/检索/排序)
│   │   ├── resume/
│   │   │   ├── ResumeCard.vue        # 简历卡片(列表项)
│   │   │   ├── ResumePreview.vue     # PDF.js 预览(不做高亮)
│   │   │   ├── UploadDialog.vue      # 上传弹窗
│   │   │   └── FilterBar.vue         # 筛选条
│   │   ├── candidate/
│   │   │   ├── CandidateCard.vue     # 候选人推荐卡片(带评分/理由)
│   │   │   ├── CandidateCompare.vue  # 候选人对比(雷达图)
│   │   │   └── TagInput.vue          # 标签输入组件
│   │   ├── dashboard/
│   │   │   └── ChartWidget.vue       # ECharts 图表封装
│   │   └── common/
│   │       ├── EmptyState.vue
│   │       └── LoadingOverlay.vue
│   ├── utils/
│   │   ├── format.ts                 # 薪资/日期格式化
│   │   ├── download.ts               # 文件下载
│   │   └── constant.ts               # 枚举常量(与 API 文档一致)
│   └── styles/
│       └── variables.scss            # 主题变量
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## 三、API 调用层实现

### 3.1 Axios 实例与拦截器 `api/request.ts`

```typescript
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 30000,
})

// 请求拦截：注入 Token
request.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

// 响应拦截：统一处理 code/message
request.interceptors.response.use(
  (response) => {
    const { code, message, data, trace_id } = response.data
    if (code === 0) return data  // 成功直接返回 data
    // 业务错误
    ElMessage.error(message)
    if (code === 1002) {  // Token 失效
      useAuthStore().logout()
      router.push('/login')
    }
    return Promise.reject({ code, message, trace_id })
  },
  (error) => {
    ElMessage.error('网络异常，请稍后重试')
    return Promise.reject(error)
  }
)

export default request
```

**对接要点**：响应拦截器直接返回 `data` 字段（剥离外层 `code/message/data` 封装），业务代码只需处理实际数据。错误统一由拦截器 `ElMessage` 提示，业务代码可选 catch 做额外处理。

### 3.2 SSE 流式请求封装 `api/sse.ts`

> 对话接口使用 `POST` + SSE，原生 `EventSource` 只支持 GET，故用 `fetch` + `ReadableStream` 实现。

```typescript
import { useAuthStore } from '@/stores/auth'

interface SSEHandlers {
  onIntent?: (data: { intent: string; strategy: string }) => void
  onRewrite?: (data: { query: string; rewrites: string[] }) => void
  onRetrieval?: (data: { count: number; candidate_ids: string[] }) => void
  onRank?: (data: { ranked: { candidate_id: string; score: number }[] }) => void
  onToken?: (delta: string) => void
  onCandidates?: (candidates: any[]) => void
  onDone?: (data: { message_id: string; response: string }) => void
  onError?: (data: { code: number; message: string }) => void
}

export async function sseChat(
  url: string,
  body: any,
  handlers: SSEHandlers,
  signal?: AbortSignal
) {
  const authStore = useAuthStore()
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'Authorization': `Bearer ${authStore.token}`,
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
    buffer = blocks.pop() || ''  // 保留未完成的块
    for (const block of blocks) {
      const event = parseSSEBlock(block)
      if (!event) continue
      dispatch(event, handlers)
    }
  }
}

function parseSSEBlock(block: string) {
  // 解析 "event: xxx\ndata: {...}"
  const lines = block.split('\n')
  let eventType = ''
  let data = ''
  for (const line of lines) {
    if (line.startsWith('event:')) eventType = line.slice(6).trim()
    else if (line.startsWith('data:')) data += line.slice(5).trim()
  }
  if (!eventType) return null
  return { event: eventType, data: data ? JSON.parse(data) : {} }
}

function dispatch(event: any, handlers: SSEHandlers) {
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
```

**对接要点**：SSE 事件类型与 [API-Design.md 0.5](./API-Design.md#05-sse-流式响应约定) 完全一致，8 种事件分别对应回调。

### 3.3 API 模块定义（对应 API 文档）

每个 API 模块严格对应 [API-Design.md](./API-Design.md) 的章节：

```typescript
// api/resume.ts
import request from './request'
import type { ResumeListItem, ResumeDetail, PageResult } from '@/types/resume'

// 对应 API 2.1 上传简历
export const uploadResume = (file: File, overwrite = false) => {
  const form = new FormData()
  form.append('file', file)
  form.append('overwrite', String(overwrite))
  return request.post('/resumes/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,  // 上传解析超时放宽
  })
}

// 对应 API 2.2 简历列表
export const getResumeList = (params: ResumeListQuery) =>
  request.get<PageResult<ResumeListItem>>('/resumes', { params })

// 对应 API 2.3 简历详情
export const getResumeDetail = (resumeId: string) =>
  request.get<ResumeDetail>(`/resumes/${resumeId}`)

// 对应 API 2.4 删除
export const deleteResume = (resumeId: string) =>
  request.delete(`/resumes/${resumeId}`)

// 对应 API 2.5 预览 URL
export const getPreviewUrl = (resumeId: string) =>
  request.get<{ preview_url: string; file_type: string }>(`/resumes/${resumeId}/preview`)

// 对应 API 2.6-2.8 标签/收藏/评价
export const updateTags = (resumeId: string, tags: string[]) =>
  request.put(`/resumes/${resumeId}/tags`, { tags })
export const toggleFavorite = (resumeId: string, isFavorite: boolean) =>
  request.put(`/resumes/${resumeId}/favorite`, { is_favorite: isFavorite })
export const updateNotes = (resumeId: string, notes: string) =>
  request.put(`/resumes/${resumeId}/notes`, { notes })
```

```typescript
// api/chat.ts
import { sseChat } from './sse'
import request from './request'

// 对应 API 3.1-3.3, 3.5（非流式）
export const createSession = (title: string) =>
  request.post('/chat/sessions', { title })
export const getSessions = (params: { page: number; page_size: number }) =>
  request.get('/chat/sessions', { params })
export const getMessages = (sessionId: string) =>
  request.get(`/chat/sessions/${sessionId}/messages`)
export const deleteSession = (sessionId: string) =>
  request.delete(`/chat/sessions/${sessionId}`)

// 对应 API 3.4 发送消息（SSE 流式）
export const sendMessageStream = (
  sessionId: string,
  query: string,
  context: { filters?: any },
  handlers: any,
  signal?: AbortSignal
) => {
  return sseChat(
    `/api/v1/chat/sessions/${sessionId}/messages`,
    { query, context },
    handlers,
    signal
  )
}
```

**所有 API 模块与 API 文档对照表**：

| API 文档章节 | 前端模块 | 函数 |
|-------------|---------|------|
| 一、Auth | `api/auth.ts` | login/refresh/getMe/logout |
| 二、Resumes | `api/resume.ts` | upload/getList/getDetail/delete/getPreviewUrl/updateTags/toggleFavorite/updateNotes |
| 三、Chat | `api/chat.ts` | createSession/getSessions/getMessages/deleteSession/sendMessageStream |
| 四、Search | `api/search.ts` | search |
| 五、Candidates | `api/candidate.ts` | exportExcel/getSimilar/compare |
| 六、Email | `api/email.ts` | sendRecommendation/getConfig/updateConfig |
| 七、JD Match | `api/jd.ts` | matchJd |
| 八、Interview | `api/interview.ts` | generateQuestions/saveNote/getNotes |
| 九、Dashboard | `api/dashboard.ts` | getStats |

### 3.4 TypeScript 类型定义 `types/`

严格对应 [API-Design.md 第十章](./API-Design.md#十数据模型定义)：

```typescript
// types/api.ts
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  trace_id: string
}
export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// types/resume.ts
export interface ResumeListItem {
  resume_id: string
  candidate_id: string
  name: string
  gender: string
  age: number
  education: string
  education_level: number  // 0-3
  work_years: number
  skills: string[]
  expected_salary: { min: number; max: number }
  tags: string[]
  is_favorite: boolean
  parse_status: 'pending' | 'parsing' | 'completed' | 'failed'
  location: string
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

// types/chat.ts
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

// types/candidate.ts
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
```

### 3.5 枚举常量 `utils/constant.ts`

```typescript
// 与 API 文档 0.6 节枚举完全一致
export const INTENT_TYPES = {
  chitchat: '闲聊',
  search: '搜索推荐',
  detail: '详情查询',
  compare: '对比',
} as const

export const STRATEGY_TYPES = {
  direct: '直接检索',
  hyde: 'HyDE假设检索',
  subquery: '子查询分解',
  backtracking: '回溯检索',
} as const

export const EDUCATION_LEVELS = {
  0: '专科',
  1: '本科',
  2: '硕士',
  3: '博士',
} as const

export const PARSE_STATUS = {
  pending: { label: '等待中', type: 'info' },
  parsing: { label: '解析中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
} as const
```

---

## 四、路由设计

```typescript
// router/index.ts
const routes = [
  { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/workbench',
    children: [
      { path: 'workbench', component: () => import('@/views/Workbench.vue'), meta: { title: '工作台' } },
      { path: 'resumes', component: () => import('@/views/ResumeList.vue'), meta: { title: '简历管理' } },
      { path: 'resumes/:id', component: () => import('@/views/ResumeDetail.vue'), meta: { title: '简历详情' } },
      { path: 'dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '数据看板' } },
      { path: 'jd-match', component: () => import('@/views/JdMatch.vue'), meta: { title: 'JD匹配' } },
      { path: 'settings', component: () => import('@/views/Settings.vue'), meta: { title: '系统设置' } },
    ],
  },
]

// 登录守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (!to.meta.public && !authStore.token) {
    next('/login')
  } else {
    next()
  }
})
```

---

## 五、状态管理（Pinia）

### 5.1 认证状态 `stores/auth.ts`

```typescript
export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    refreshToken: localStorage.getItem('refreshToken') || '',
    user: null as UserInfo | null,
  }),
  actions: {
    async login(username: string, password: string) {
      const data = await authApi.login(username, password)
      this.token = data.access_token
      this.refreshToken = data.refresh_token
      this.user = data.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('refreshToken', this.refreshToken)
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
    },
  },
})
```

### 5.2 对话状态 `stores/chat.ts`

```typescript
export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [] as Session[],
    currentSessionId: '',
    messages: [] as ChatMessage[],
    streaming: false,           // 是否正在流式输出
    streamPhase: '',            // 当前阶段：intent/rewrite/retrieval/rank/respond
    abortController: null as AbortController | null,
  }),
  actions: {
    async sendMessage(query: string, filters: any) {
      this.streaming = true
      this.streamPhase = 'thinking'
      // 先插入用户消息
      this.messages.push({ role: 'user', content: query, ... })

      this.abortController = new AbortController()
      await sendMessageStream(
        this.currentSessionId, query, { filters },
        {
          onIntent: (d) => { this.streamPhase = `意图: ${INTENT_TYPES[d.intent]}` },
          onRewrite: (d) => { this.streamPhase = 'Query 改写中...' },
          onRetrieval: (d) => { this.streamPhase = `已召回 ${d.count} 条` },
          onRank: (d) => { this.streamPhase = '精排评分中...' },
          onToken: (delta) => {
            // 追加到最后一条 assistant 消息
            const last = this.messages[this.messages.length - 1]
            if (last.role === 'assistant') last.content += delta
            else this.messages.push({ role: 'assistant', content: delta, candidates: [] })
          },
          onCandidates: (candidates) => {
            const last = this.messages[this.messages.length - 1]
            if (last.role === 'assistant') last.candidates = candidates
          },
          onDone: () => { this.streaming = false; this.streamPhase = '' },
          onError: (e) => { ElMessage.error(e.message); this.streaming = false },
        },
        this.abortController.signal
      )
    },
    stopStreaming() {
      this.abortController?.abort()
      this.streaming = false
    },
  },
})
```

### 5.3 简历状态 `stores/resume.ts`

```typescript
export const useResumeStore = defineStore('resume', {
  state: () => ({
    list: [] as ResumeListItem[],
    total: 0,
    loading: false,
    filters: {
      keyword: '', tag: '', is_favorite: false,
      education_min: null, work_years_min: null,
      salary_min: null, salary_max: null,
    },
    page: 1,
    pageSize: 20,
  }),
  actions: {
    async fetchList() {
      this.loading = true
      const data = await getResumeList({ ...this.filters, page: this.page, page_size: this.pageSize })
      this.list = data.list
      this.total = data.total
      this.loading = false
    },
    async toggleFavorite(resumeId: string, value: boolean) {
      await toggleFavoriteApi(resumeId, value)
      // 本地更新
      const item = this.list.find(i => i.resume_id === resumeId)
      if (item) item.is_favorite = value
    },
  },
})
```

---

## 六、页面实现

### 6.1 工作台 `views/Workbench.vue`（核心页面）

三栏布局：左侧会话列表 + 中间对话面板 + 右侧候选人卡片联动。

```vue
<template>
  <div class="workbench">
    <!-- 左：会话列表 -->
    <SessionList class="left-panel" @select="onSelectSession" />

    <!-- 中：对话面板 -->
    <div class="center-panel">
      <StreamIndicator v-if="chatStore.streaming" :phase="chatStore.streamPhase" />
      <ChatPanel
        :messages="chatStore.messages"
        :streaming="chatStore.streaming"
        @send="onSend"
        @stop="chatStore.stopStreaming"
        @candidate-click="onCandidateClick"
      />
    </div>

    <!-- 右：候选人详情抽屉（点击候选人卡片时展开） -->
    <el-drawer v-model="drawerVisible" size="40%" :title="selectedName">
      <ResumeDetail v-if="selectedResumeId" :resume-id="selectedResumeId" embedded />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from '@/stores/chat'
const chatStore = useChatStore()

function onSend(query: string) {
  chatStore.sendMessage(query, {})  // 可附加筛选条件
}

function onCandidateClick(resumeId: string) {
  selectedResumeId.value = resumeId
  drawerVisible.value = true
}
</script>
```

### 6.2 对话面板 `components/chat/ChatPanel.vue`

```vue
<template>
  <div class="chat-panel">
    <!-- 消息列表 -->
    <div class="messages" ref="messagesRef">
      <template v-for="msg in messages" :key="msg.message_id">
        <MessageBubble :role="msg.role">
          <div v-html="renderMarkdown(msg.content)" />
          <!-- assistant 消息附带候选人卡片 -->
          <div v-if="msg.candidates?.length" class="candidates">
            <CandidateCard
              v-for="c in msg.candidates"
              :key="c.candidate_id"
              :candidate="c"
              @click="$emit('candidate-click', c.resume_id)"
            />
          </div>
        </MessageBubble>
      </template>
      <!-- 流式打字光标 -->
      <span v-if="streaming" class="cursor">|</span>
    </div>

    <!-- 输入框 -->
    <div class="input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="输入招聘需求，如：5年Java后端，本科以上，30K以内"
        @keydown.enter.exact.prevent="onSend"
      />
      <el-button v-if="!streaming" type="primary" @click="onSend">发送</el-button>
      <el-button v-else type="danger" @click="$emit('stop')">停止</el-button>
    </div>
  </div>
</template>
```

### 6.3 候选人卡片 `components/candidate/CandidateCard.vue`

```vue
<template>
  <el-card class="candidate-card" shadow="hover" @click="$emit('click')">
    <div class="header">
      <span class="name">{{ candidate.name }}</span>
      <el-tag type="success" size="small">匹配度 {{ candidate.score }}</el-tag>
      <el-icon v-if="candidate.is_favorite" class="favorite"><StarFilled /></el-icon>
    </div>
    <div class="meta">
      <span>{{ candidate.work_years }}年经验</span>
      <el-divider direction="vertical" />
      <span>{{ candidate.education }}</span>
      <el-divider direction="vertical" />
      <span>{{ candidate.expected_salary.min }}-{{ candidate.expected_salary.max }}K</span>
    </div>
    <div class="skills">
      <el-tag v-for="s in candidate.skills.slice(0,5)" :key="s" size="small">{{ s }}</el-tag>
    </div>
    <div class="reason">{{ candidate.reason }}</div>
    <div class="actions">
      <el-button size="small" @click.stop="onExport">导出</el-button>
      <el-button size="small" @click.stop="onEmail">邮件</el-button>
      <el-button size="small" @click.stop="onInterview">面试题</el-button>
    </div>
  </el-card>
</template>
```

### 6.4 简历列表 `views/ResumeList.vue`

```vue
<template>
  <div class="resume-list">
    <!-- 筛选条 -->
    <FilterBar v-model="resumeStore.filters" @search="resumeStore.fetchList" />

    <!-- 操作栏 -->
    <div class="toolbar">
      <el-upload :show-file-list="false" :http-request="onUpload" accept=".pdf,.docx,.png,.jpg">
        <el-button type="primary">上传简历</el-button>
      </el-upload>
      <el-button @click="onBatchExport">批量导出 Excel</el-button>
    </div>

    <!-- 列表 -->
    <el-table :data="resumeStore.list" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="40" />
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="work_years" label="工作年限" />
      <el-table-column prop="education" label="学历" />
      <el-table-column label="技能">
        <template #default="{ row }">
          <el-tag v-for="s in row.skills.slice(0,3)" :key="s" size="small">{{ s }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="期望薪资">
        <template #default="{ row }">{{ row.expected_salary.min }}-{{ row.expected_salary.max }}K</template>
      </el-table-column>
      <el-table-column label="标签">
        <template #default="{ row }">
          <el-tag v-for="t in row.tags" :key="t" size="small" type="warning">{{ t }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="解析状态">
        <template #default="{ row }">
          <el-tag :type="PARSE_STATUS[row.parse_status].type">
            {{ PARSE_STATUS[row.parse_status].label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/resumes/${row.resume_id}`)">详情</el-button>
          <el-button size="small" @click="onDelete(row.resume_id)" type="danger">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="resumeStore.page"
      :page-size="resumeStore.pageSize"
      :total="resumeStore.total"
      @current-change="resumeStore.fetchList"
    />
  </div>
</template>
```

### 6.5 简历详情 `views/ResumeDetail.vue`

```vue
<template>
  <div class="resume-detail">
    <el-row :gutter="20">
      <!-- 左：简历信息 -->
      <el-col :span="14">
        <el-card>
          <h2>{{ detail.basic_info.name }} <el-tag>{{ detail.education }}</el-tag></h2>
          <p>{{ detail.basic_info.phone_masked }} | {{ detail.basic_info.email_masked }}</p>
          <p>{{ detail.work_years }}年经验 | {{ detail.expected_salary.min }}-{{ detail.expected_salary.max }}K</p>
          <el-divider>技能</el-divider>
          <el-tag v-for="s in detail.skills" :key="s">{{ s }}</el-tag>
          <el-divider>工作经历</el-divider>
          <div v-for="exp in detail.work_experience" :key="exp.company">
            <h4>{{ exp.company }} - {{ exp.position }}</h4>
            <p>{{ exp.start_date }} ~ {{ exp.end_date }}</p>
            <p>{{ exp.description }}</p>
          </div>
          <!-- 标签/收藏/评价 -->
          <el-divider>标注</el-divider>
          <TagInput v-model="detail.tags" @change="onTagsChange" />
          <el-input v-model="detail.notes" type="textarea" @blur="onNotesChange" placeholder="面试评价..." />
          <!-- 面试评价历史 -->
          <InterviewNoteList :notes="detail.interview_notes" />
        </el-card>
      </el-col>

      <!-- 右：PDF预览 + 相似推荐 + 面试题 -->
      <el-col :span="10">
        <el-tabs>
          <el-tab-pane label="简历预览">
            <ResumePreview :url="previewUrl" />
          </el-tab-pane>
          <el-tab-pane label="相似候选人">
            <SimilarCandidates :resume-id="resumeId" />
          </el-tab-pane>
          <el-tab-pane label="面试题">
            <InterviewQuestions :resume-id="resumeId" />
          </el-tab-pane>
        </el-tabs>
      </el-col>
    </el-row>
  </div>
</template>
```

### 6.6 PDF 预览 `components/resume/ResumePreview.vue`

```vue
<template>
  <div class="pdf-preview">
    <canvas ref="canvasRef" />
  </div>
</template>

<script setup lang="ts">
import * as pdfjsLib from 'pdfjs-dist'
import { onMounted, ref, watch } from 'vue'

const props = defineProps<{ url: string }>()
const canvasRef = ref<HTMLCanvasElement>()

// PDF.js 渲染（不做 bbox 高亮，仅预览）
async function renderPdf(url: string) {
  const pdf = await pdfjsLib.getDocument(url).promise
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i)
    const viewport = page.getViewport({ scale: 1.2 })
    const canvas = canvasRef.value!
    canvas.width = viewport.width
    canvas.height = viewport.height
    await page.render({ canvasContext: canvas.getContext('2d')!, viewport }).promise
  }
}

watch(() => props.url, (url) => url && renderPdf(url))
</script>
```

### 6.7 数据看板 `views/Dashboard.vue`

```vue
<template>
  <div class="dashboard">
    <!-- 概览卡片 -->
    <el-row :gutter="20">
      <el-col :span="4"><ChartWidget title="简历总数" :value="stats.summary.total_resumes" /></el-col>
      <el-col :span="4"><ChartWidget title="本周新增" :value="stats.summary.new_this_week" /></el-col>
      <el-col :span="4"><ChartWidget title="本月新增" :value="stats.summary.new_this_month" /></el-col>
      <el-col :span="4"><ChartWidget title="收藏" :value="stats.summary.favorite_count" /></el-col>
      <el-col :span="4"><ChartWidget title="已面试" :value="stats.summary.interviewed_count" /></el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <ChartWidget title="技能分布 Top-20" type="bar"
          :data="stats.skill_distribution.map(s => ({ name: s.skill, value: s.count }))" />
      </el-col>
      <el-col :span="6">
        <ChartWidget title="学历分布" type="pie"
          :data="stats.education_distribution.map(e => ({ name: e.level, value: e.count }))" />
      </el-col>
      <el-col :span="6">
        <ChartWidget title="工作年限分布" type="pie"
          :data="stats.work_years_distribution.map(w => ({ name: w.range, value: w.count }))" />
      </el-col>
    </el-row>
    <el-row :gutter="20">
      <el-col :span="12">
        <ChartWidget title="薪资分布" type="bar"
          :data="stats.salary_distribution.map(s => ({ name: s.range, value: s.count }))" />
      </el-col>
      <el-col :span="12">
        <ChartWidget title="标签分布" type="pie"
          :data="stats.tag_distribution.map(t => ({ name: t.tag, value: t.count }))" />
      </el-col>
    </el-row>
  </div>
</template>
```

### 6.8 JD 匹配 `views/JdMatch.vue`

```vue
<template>
  <div class="jd-match">
    <el-row :gutter="20">
      <el-col :span="10">
        <el-input v-model="jdText" type="textarea" :rows="15" placeholder="粘贴 JD 岗位描述..." />
        <el-button type="primary" :loading="matching" @click="onMatch">开始匹配</el-button>
      </el-col>
      <el-col :span="14">
        <div v-if="parsedRequirements">
          <h3>JD 解析结果</h3>
          <p>技能要求：{{ parsedRequirements.skills.join(', ') }}</p>
          <p>最低年限：{{ parsedRequirements.work_years_min }}年</p>
        </div>
        <CandidateCard
          v-for="c in matchedCandidates"
          :key="c.candidate_id"
          :candidate="c"
          @click="$router.push(`/resumes/${c.resume_id}`)"
        />
      </el-col>
    </el-row>
  </div>
</template>
```

---

## 七、与 API 文档的对接说明

前端实现严格遵循 [API-Design.md](./API-Design.md)：

### 7.1 请求对接

| 前端动作 | 调用 API | API 文档章节 |
|---------|---------|-------------|
| 登录 | `POST /auth/login` | 1.1 |
| 上传简历 | `POST /resumes/upload`（multipart） | 2.1 |
| 简历列表筛选 | `GET /resumes`（query 参数） | 2.2 |
| 发送对话消息 | `POST /chat/sessions/{id}/messages`（SSE） | 3.4 |
| 直接检索 | `POST /search` | 4.1 |
| Excel 导出 | `POST /candidates/export`（文件流） | 5.1 |
| 发推荐邮件 | `POST /email/send-recommendation` | 6.1 |
| JD 匹配 | `POST /jd/match` | 7.1 |
| 生成面试题 | `POST /candidates/{id}/interview-questions` | 8.1 |
| 看板统计 | `GET /dashboard/stats` | 9.1 |

### 7.2 响应对接

- **统一响应**：Axios 拦截器剥离外层 `code/message/data`，业务代码直接拿 `data`
- **分页**：列表接口返回 `{list, total, page, page_size, total_pages}`，`el-pagination` 绑定 `total`
- **SSE**：8 种事件类型对应 `sse.ts` 的 8 个回调（`onIntent/onRewrite/onRetrieval/onRank/onToken/onCandidates/onDone/onError`）
- **错误**：拦截器统一 `ElMessage` 提示 `message` 字段；`code=1002` 跳登录页

### 7.3 字段对接

前端 TypeScript 类型定义（`types/`）与 [API-Design.md 第十章数据模型](./API-Design.md#十数据模型定义) 一一对应：

| API 数据模型 | 前端类型 | 用途 |
|-------------|---------|------|
| ResumeListItem | `types/resume.ts#ResumeListItem` | 列表渲染 |
| ResumeDetail | `types/resume.ts#ResumeDetail` | 详情页 |
| CandidateCard | `types/candidate.ts#CandidateCard` | 推荐卡片 |
| ChatMessage | `types/chat.ts#ChatMessage` | 消息渲染 |

### 7.4 枚举对接

`utils/constant.ts` 中的枚举与 [API-Design.md 0.6 节](./API-Design.md#06-通用枚举) 完全一致：
- `intent`: chitchat/search/detail/compare
- `strategy`: direct/hyde/subquery/backtracking
- `education_level`: 0/1/2/3
- `parse_status`: pending/parsing/completed/failed

### 7.5 对接要点

1. **Token 注入**：所有请求经 `request.ts` 拦截器自动注入 `Authorization: Bearer <token>`
2. **SSE 鉴权**：`sse.ts` 中手动注入 `Authorization` 头（fetch 不走 Axios 拦截器）
3. **文件上传**：`Content-Type` 设为 `multipart/form-data`，超时放宽至 120s
4. **文件下载**：Excel 导出接口返回文件流，用 `Blob` + `URL.createObjectURL` 下载
5. **脱敏展示**：`phone_masked`/`email_masked` 直接展示（后端已脱敏），前端不处理明文
6. **PDF 预览**：调用 `GET /resumes/{id}/preview` 获取预签名 URL，传给 PDF.js 渲染（不做 bbox 高亮）

---

## 八、关键交互实现

### 8.1 对话流式输出

```
用户输入 → chatStore.sendMessage()
    → sendMessageStream() 发起 fetch SSE
    → onIntent: StreamIndicator 显示"意图: 搜索推荐"
    → onRewrite: StreamIndicator 显示"Query 改写中..."
    → onRetrieval: StreamIndicator 显示"已召回 20 条"
    → onRank: StreamIndicator 显示"精排评分中..."
    → onToken: 逐字追加到 assistant 消息（打字机效果）
    → onCandidates: 渲染候选人卡片到消息下方
    → onDone: 结束流式状态
```

### 8.2 候选人卡片联动

工作台中点击候选人卡片 → 打开右侧抽屉 → 调用 `GET /resumes/{id}` 加载详情 → 同时加载 PDF 预览、相似推荐、面试题（Tab 切换懒加载）。

### 8.3 简历上传与解析轮询

```typescript
async function onUpload({ file }) {
  const { resume_id, parse_status } = await uploadResume(file)
  ElMessage.success('上传成功，解析中...')
  // 轮询解析状态
  const timer = setInterval(async () => {
    const detail = await getResumeDetail(resume_id)
    if (detail.parse_info.parse_status === 'completed') {
      clearInterval(timer)
      ElMessage.success('解析完成')
      resumeStore.fetchList()  // 刷新列表
    } else if (detail.parse_info.parse_status === 'failed') {
      clearInterval(timer)
      ElMessage.error('解析失败')
    }
  }, 2000)
}
```

### 8.4 Excel 导出下载

```typescript
async function onBatchExport() {
  const resp = await request.post('/candidates/export', {
    candidate_ids: selectedIds.value,
  }, { responseType: 'blob' })  // 关键：blob 接收文件流
  const url = URL.createObjectURL(resp)
  const a = document.createElement('a')
  a.href = url
  a.download = `candidates_${Date.now()}.xlsx`
  a.click()
  URL.revokeObjectURL(url)
}
```

---

## 九、开发约定

### 9.1 组件命名
- 页面：`PascalCase.vue`（如 `ResumeList.vue`）
- 组件：按功能分组到 `components/{module}/`
- API 函数：`动词+名词`（如 `getResumeList`、`uploadResume`）

### 9.2 状态管理边界
- 全局共享状态（登录、会话、简历列表筛选）放 Pinia
- 组件局部状态（弹窗开关、表单）用 `ref`/`reactive`
- 不把请求响应数据全塞 Pinia，只在跨页面共享时入 store

### 9.3 错误处理
- 网络错误、业务错误由 `request.ts` 拦截器统一 `ElMessage` 提示
- 表单校验错误由 Element Plus `el-form` 校验
- SSE 错误通过 `onError` 回调单独处理（不阻断页面）

### 9.4 性能优化
- 路由懒加载（`() => import()`）
- 简历列表虚拟滚动（数据量大时）
- ECharts 按需引入（`echarts/core` + 具体图表）
- PDF.js 分页渲染（避免一次性渲染大 PDF）
