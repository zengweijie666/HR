# TalentSense HR 简历推荐系统 - API 接口文档

**版本**：v2.5
**日期**：2026-06-26
**Base URL**：`http://localhost:8000/api/v1`
**认证方式**：JWT Bearer Token（除登录接口外均需认证）
**Content-Type**：`application/json`（上传文件为 `multipart/form-data`）

> 本文档为前后端对接的统一契约，前端请求与后端响应必须严格遵循本文档定义。

---

## 〇、统一约定

### 0.1 统一响应格式

所有非流式接口统一返回如下结构：

```json
{
  "code": 0,
  "message": "success",
  "data": { },
  "trace_id": "trace_xxx"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 业务状态码，`0` 表示成功，非 `0` 表示业务错误 |
| message | string | 提示信息，成功为 `success`，失败为错误描述 |
| data | object/array/null | 业务数据，无数据返回 `null` |
| trace_id | string | 链路追踪 ID（loguru 日志关联） |

### 0.2 业务状态码

| code | HTTP Status | 说明 |
|------|-------------|------|
| 0 | 200 | 成功 |
| 1001 | 400 | 参数校验失败 |
| 1002 | 401 | 未认证 / Token 失效 |
| 1003 | 403 | 无权限 |
| 1004 | 404 | 资源不存在 |
| 1005 | 409 | 资源冲突（如重复简历） |
| 2001 | 422 | 简历解析失败 |
| 2002 | 422 | LLM 调用失败 |
| 2003 | 422 | 向量检索失败 |
| 2004 | 422 | 邮件发送失败 |
| 5000 | 500 | 服务器内部错误 |

### 0.3 分页约定

列表类接口统一使用分页查询参数与响应：

**请求参数（Query）**：
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| page | int | 1 | 页码，从 1 开始 |
| page_size | int | 20 | 每页条数，最大 100 |

**响应 data 结构**：
```json
{
  "list": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "total_pages": 0
}
```

### 0.4 认证方式

除 `POST /auth/login` 外，所有接口需在请求头携带：
```
Authorization: Bearer <access_token>
```

Token 过期后使用 `refresh_token` 刷新（见 1.2）。

### 0.5 SSE 流式响应约定

对话接口 `POST /chat/sessions/{session_id}/messages` 使用 SSE 流式输出，响应头：
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

**SSE 事件类型**（`event:` 字段）：

| event | data 结构 | 说明 |
|-------|-----------|------|
| `intent` | `{"intent": "search", "strategy": "hyde"}` | 意图识别结果 |
| `rewrite` | `{"query": "改写后的query", "rewrites": ["..."]}` | Query 改写结果 |
| `retrieval` | `{"count": 10, "candidate_ids": ["cand_xxx"]}` | 检索召回 |
| `rank` | `{"ranked": [{"candidate_id": "cand_xxx", "score": 95}]}` | Reranker+LLM 评分 |
| `token` | `{"delta": "推荐"}` | 流式输出 token |
| `candidates` | `{"candidates": [CandidateCard]}` | 推荐候选人卡片列表 |
| `done` | `{"message_id": "msg_xxx", "response": "完整响应文本"}` | 流结束 |
| `error` | `{"code": 2002, "message": "LLM 调用失败"}` | 错误 |

### 0.6 通用枚举

**意图类型 intent**：`chitchat` | `search` | `detail` | `compare`

**Query 改写策略 strategy**：`direct` | `hyde` | `subquery` | `backtracking`

**学历 education_level**：`0` 专科 | `1` 本科 | `2` 硕士 | `3` 博士

**简历解析状态 parse_status**：`pending` | `parsing` | `completed` | `failed`

---

## 一、认证接口（Auth）

### 1.1 用户登录

`POST /auth/login`

**请求体**：
```json
{
  "username": "admin",
  "password": "hashed_password"
}
```

**响应 data**：
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "u_001",
    "username": "admin",
    "role": "hr",
    "email": "hr@company.com"
  }
}
```

### 1.2 刷新 Token

`POST /auth/refresh`

**请求体**：
```json
{ "refresh_token": "eyJhbGci..." }
```

**响应 data**：同 1.1 的 `user` + 新的 `access_token` / `refresh_token`。

### 1.3 获取当前用户

`GET /auth/me`

**响应 data**：
```json
{
  "user_id": "u_001",
  "username": "admin",
  "role": "hr",
  "email": "hr@company.com"
}
```

### 1.4 登出

`POST /auth/logout`

**响应 data**：`null`（后端使当前 token 失效）

---

## 二、简历管理接口（Resumes）

### 2.1 上传简历

`POST /resumes/upload`

**请求**：`multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 简历文件，支持 `.pdf` `.docx` `.png` `.jpg` |
| overwrite | boolean | 否 | 重复时是否覆盖，默认 `false` |

**响应 data**：
```json
{
  "resume_id": "res_xxx",
  "candidate_id": "cand_xxx",
  "file_name": "张三_简历.pdf",
  "parse_status": "parsing",
  "is_duplicate": false,
  "duplicate_with": null
}
```

> 解析异步进行，前端通过 `GET /resumes/{resume_id}` 轮询 `parse_status`，或通过 2.2 的 `status` 筛选。重复简历时 `is_duplicate=true`，返回 `duplicate_with` 指向已存在简历 ID。

### 2.2 简历列表

`GET /resumes`

**查询参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页条数，默认 20 |
| keyword | string | 否 | 姓名/技能关键词模糊搜索 |
| tag | string | 否 | 按标签精确筛选 |
| is_favorite | boolean | 否 | 仅看收藏 |
| education_min | int | 否 | 最低学历（education_level） |
| work_years_min | int | 否 | 最低工作年限 |
| salary_min | int | 否 | 最低期望薪资（K） |
| salary_max | int | 否 | 最高期望薪资（K） |
| status | string | 否 | 解析状态筛选（completed/failed） |

**响应 data**（分页结构，`list` 元素为 [ResumeListItem](#41-resumelistitem)）：
```json
{
  "list": [ { "resume_id": "res_xxx", "name": "张三", "..." : "..." } ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

### 2.3 简历详情

`GET /resumes/{resume_id}`

**响应 data**：见 [ResumeDetail](#42-resumedetail)

### 2.4 删除简历

`DELETE /resumes/{resume_id}`

**响应 data**：`null`（同时删除 MinIO 文件、MongoDB 记录、Milvus 向量）

### 2.5 获取简历预览 URL

`GET /resumes/{resume_id}/preview`

**响应 data**：
```json
{
  "preview_url": "http://minio:9000/resumes/res_xxx?presigned=...",
  "file_type": "pdf",
  "expires_in": 3600
}
```

> 返回 MinIO 预签名 URL，前端用 PDF.js 渲染（不做 bbox 高亮）。

### 2.6 更新标签

`PUT /resumes/{resume_id}/tags`

**请求体**：
```json
{ "tags": ["已面试", "重点关注"] }
```

**响应 data**：`{ "resume_id": "res_xxx", "tags": ["已面试", "重点关注"] }`

### 2.7 收藏 / 取消收藏

`PUT /resumes/{resume_id}/favorite`

**请求体**：
```json
{ "is_favorite": true }
```

**响应 data**：`{ "resume_id": "res_xxx", "is_favorite": true }`

### 2.8 更新评价备注

`PUT /resumes/{resume_id}/notes`

**请求体**：
```json
{ "notes": "面试表现良好，技术扎实" }
```

**响应 data**：`{ "resume_id": "res_xxx", "notes": "面试表现良好，技术扎实" }`

---

## 三、对话/Agent 接口（Chat，SSE 流式）

### 3.1 创建会话

`POST /chat/sessions`

**请求体**：
```json
{ "title": "5年Java后端招聘" }
```

**响应 data**：
```json
{
  "session_id": "sess_xxx",
  "title": "5年Java后端招聘",
  "created_at": "2026-06-26T10:00:00Z"
}
```

### 3.2 会话列表

`GET /chat/sessions`

**查询参数**：`page`、`page_size`

**响应 data**（分页结构，元素为）：
```json
{
  "session_id": "sess_xxx",
  "title": "5年Java后端招聘",
  "last_message": "推荐张三，5年Java...",
  "message_count": 8,
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T10:30:00Z"
}
```

### 3.3 获取消息历史

`GET /chat/sessions/{session_id}/messages`

**查询参数**：`page`、`page_size`（默认最近 5 轮，即 10 条）

**响应 data**（分页结构，元素为 [ChatMessage](#43-chatmessage)）：
```json
{
  "list": [
    { "role": "user", "content": "找个5年Java", "..." : "..." },
    { "role": "assistant", "content": "推荐以下候选人", "candidates": [], "..." : "..." }
  ],
  "total": 10,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

### 3.4 发送消息（SSE 流式）

`POST /chat/sessions/{session_id}/messages`

**请求头**：
```
Accept: text/event-stream
Authorization: Bearer <token>
```

**请求体**：
```json
{
  "query": "帮我找一个5年经验的Java后端，本科以上，期望30K以内",
  "context": {
    "filters": {
      "education_min": 1,
      "salary_max": 30,
      "work_years_min": 5
    }
  }
}
```

**响应**：SSE 流，事件类型见 [0.5 SSE 事件约定](#05-sse-流式响应约定)。

**完整 SSE 流示例**：
```
event: intent
data: {"intent":"search","strategy":"hyde"}

event: rewrite
data: {"query":"5年Java后端开发经验，熟悉Spring生态，本科及以上，期望薪资30K以内","rewrites":["..."]}

event: retrieval
data: {"count":20,"candidate_ids":["cand_001","cand_002"]}

event: rank
data: {"ranked":[{"candidate_id":"cand_001","score":95},{"candidate_id":"cand_002","score":88}]}

event: token
data: {"delta":"根据"}

event: token
data: {"delta":"您的需求"}

event: candidates
data: {"candidates":[{"candidate_id":"cand_001","name":"张三","score":95,"reason":"5年Java后端..."}]}

event: done
data: {"message_id":"msg_xxx","response":"根据您的需求，推荐以下候选人：..."}
```

### 3.5 删除会话

`DELETE /chat/sessions/{session_id}`

**响应 data**：`null`（同时删除 MongoDB 中的对话历史）

---

## 四、检索接口（Search）

### 4.1 直接检索

`POST /search`

> 与对话不同，本接口为非流式直接检索，用于前端"快速搜索"功能。

**请求体**：
```json
{
  "query": "Java后端开发",
  "strategy": "auto",
  "filters": {
    "education_min": 1,
    "work_years_min": 3,
    "salary_min": 15,
    "salary_max": 30,
    "skills": ["Java", "Spring Boot"]
  },
  "top_k": 10
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 检索 query |
| strategy | string | 否 | 改写策略：`auto`(LLM选)/`direct`/`hyde`/`subquery`/`backtracking`，默认 `auto` |
| filters | object | 否 | 硬条件过滤 |
| top_k | int | 否 | 返回条数，默认 10，最大 50 |

**响应 data**：
```json
{
  "query_rewrite": "5年Java后端开发经验...",
  "strategy": "hyde",
  "candidates": [ { "candidate_id": "cand_001", "name": "张三", "score": 95, "reason": "..." } ],
  "total": 10
}
```

---

## 五、候选人接口（Candidates）

### 5.1 Excel 导出

`POST /candidates/export`

**请求体**：
```json
{
  "candidate_ids": ["res_xxx", "res_yyy"],
  "fields": ["name", "work_years", "education", "skills", "expected_salary", "phone_masked", "email_masked"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| candidate_ids | string[] | 是 | 要导出的 resume_id 列表（空则导出当前筛选结果，需配合 `filters`） |
| filters | object | 否 | 当 `candidate_ids` 为空时使用列表筛选条件 |
| fields | string[] | 否 | 导出字段，默认全部 |

**响应**：文件流下载
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="candidates_20260626.xlsx"
```

### 5.2 相似候选人推荐

`GET /candidates/{resume_id}/similar`

**查询参数**：
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| top_k | int | 5 | 返回条数，最大 20 |

**响应 data**：
```json
{
  "source": { "resume_id": "res_xxx", "name": "张三" },
  "similar": [
    { "resume_id": "res_yyy", "name": "李四", "similarity": 0.92, "shared_skills": ["Java", "Spring Boot"] }
  ]
}
```

### 5.3 候选人对比

`POST /candidates/compare`

**请求体**：
```json
{ "candidate_ids": ["res_xxx", "res_yyy", "res_zzz"] }
```

**响应 data**：
```json
{
  "dimensions": ["工作年限", "学历", "技能匹配度", "期望薪资", "项目经验"],
  "candidates": [
    {
      "resume_id": "res_xxx",
      "name": "张三",
      "values": { "工作年限": 5, "学历": "本科", "技能匹配度": 95, "期望薪资": "20-30K", "项目经验": "3个" }
    }
  ]
}
```

---

## 六、邮件接口（Email）

### 6.1 发送推荐邮件

`POST /email/send-recommendation`

**请求体**：
```json
{
  "to_email": "HR@company.com",
  "cc": ["leader@company.com"],
  "subject": "Java后端候选人推荐 - 5人",
  "query": "5年Java后端开发",
  "candidate_ids": ["res_xxx", "res_yyy"],
  "include_excel": true,
  "remark": "请优先关注张三"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| to_email | string | 是 | 收件人邮箱 |
| cc | string[] | 否 | 抄送 |
| subject | string | 否 | 邮件主题，默认 LLM 生成 |
| query | string | 否 | 招聘需求描述（用于 LLM 生成报告） |
| candidate_ids | string[] | 是 | 推荐候选人 resume_id 列表 |
| include_excel | boolean | 否 | 是否附加 Excel，默认 `true` |
| remark | string | 否 | 附加备注 |

**响应 data**：
```json
{
  "message_id": "email_xxx",
  "status": "sent",
  "sent_at": "2026-06-26T10:00:00Z",
  "recipient": "HR@company.com"
}
```

### 6.2 获取邮件配置

`GET /email/config`

**响应 data**：
```json
{
  "smtp_host": "smtp.company.com",
  "smtp_port": 465,
  "smtp_user": "hr@company.com",
  "use_ssl": true,
  "sender_name": "TalentSense HR",
  "signature": "—— TalentSense HR 推荐系统"
}
```

> `smtp_password` 不返回明文，仅返回是否已配置：`"password_configured": true`。

### 6.3 更新邮件配置

`PUT /email/config`

**请求体**：
```json
{
  "smtp_host": "smtp.company.com",
  "smtp_port": 465,
  "smtp_user": "hr@company.com",
  "smtp_password": "new_password",
  "use_ssl": true,
  "sender_name": "TalentSense HR",
  "signature": "—— TalentSense HR 推荐系统"
}
```

**响应 data**：同 6.2（不返回密码明文）

---

## 七、JD 匹配接口（JD Match）

### 7.1 JD 岗位匹配

`POST /jd/match`

**请求体**：
```json
{
  "jd_text": "岗位：高级Java开发工程师\n要求：5年以上Java后端开发经验，熟悉Spring Boot、MySQL，本科及以上学历...",
  "top_k": 10,
  "filters": {
    "education_min": 1,
    "work_years_min": 5
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| jd_text | string | 是 | JD 原文 |
| top_k | int | 否 | 返回条数，默认 10 |
| filters | object | 否 | 额外硬条件过滤 |

**响应 data**：
```json
{
  "parsed_requirements": {
    "skills": ["Java", "Spring Boot", "MySQL"],
    "work_years_min": 5,
    "education_min": 1,
    "responsibilities": ["后端服务开发", "数据库设计"]
  },
  "candidates": [
    {
      "candidate_id": "cand_001",
      "resume_id": "res_xxx",
      "name": "张三",
      "score": 95,
      "match_analysis": {
        "matched_skills": ["Java", "Spring Boot", "MySQL"],
        "missing_skills": [],
        "experience_match": true,
        "education_match": true,
        "reason": "5年Java后端经验，技能完全匹配..."
      }
    }
  ],
  "total": 10
}
```

---

## 八、面试接口（Interview）

### 8.1 生成面试问题

`POST /candidates/{resume_id}/interview-questions`

**请求体**：
```json
{
  "dimensions": ["technical", "project", "system_design", "behavioral"],
  "count_per_dimension": 3,
  "focus_skills": ["Java", "MySQL"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dimensions | string[] | 否 | 生成维度，默认全部。可选：`technical`/`project`/`system_design`/`behavioral` |
| count_per_dimension | int | 否 | 每维度题数，默认 3 |
| focus_skills | string[] | 否 | 重点考察技能 |

**响应 data**：
```json
{
  "resume_id": "res_xxx",
  "candidate_name": "张三",
  "questions": [
    {
      "dimension": "technical",
      "question": "请讲讲 HashMap 在 JDK1.8 中的底层实现，以及为什么引入红黑树？",
      "skill": "Java",
      "difficulty": "medium",
      "reference_answer": "JDK1.8 HashMap 采用数组+链表+红黑树..."
    },
    {
      "dimension": "project",
      "question": "你在XX项目中提到使用了微服务架构，请描述服务拆分粒度如何决定？",
      "skill": null,
      "difficulty": "hard",
      "reference_answer": null
    }
  ]
}
```

### 8.2 保存面试评价

`POST /candidates/{resume_id}/interview-notes`

**请求体**：
```json
{
  "interviewer": "李HR",
  "rating": 4,
  "result": "pass",
  "notes": "技术基础扎实，项目经验丰富，沟通良好"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| interviewer | string | 是 | 面试官 |
| rating | int | 是 | 评分 1-5 |
| result | string | 是 | 结果：`pass`/`fail`/`pending` |
| notes | string | 否 | 评价内容 |

**响应 data**：
```json
{
  "note_id": "note_xxx",
  "resume_id": "res_xxx",
  "interviewer": "李HR",
  "rating": 4,
  "result": "pass",
  "notes": "技术基础扎实...",
  "created_at": "2026-06-26T11:00:00Z"
}
```

### 8.3 获取面试评价列表

`GET /candidates/{resume_id}/interview-notes`

**响应 data**：
```json
{
  "list": [ { "note_id": "note_xxx", "interviewer": "李HR", "rating": 4, "..." : "..." } ]
}
```

---

## 九、数据看板接口（Dashboard）

### 9.1 看板统计

`GET /dashboard/stats`

**查询参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| range | string | 否 | 统计范围：`week`/`month`/`all`，默认 `all` |

**响应 data**：
```json
{
  "summary": {
    "total_resumes": 1256,
    "new_this_week": 32,
    "new_this_month": 128,
    "favorite_count": 45,
    "interviewed_count": 78
  },
  "skill_distribution": [
    { "skill": "Java", "count": 320 },
    { "skill": "Python", "count": 280 },
    { "skill": "Spring Boot", "count": 210 }
  ],
  "work_years_distribution": [
    { "range": "0-3年", "count": 280 },
    { "range": "3-5年", "count": 350 },
    { "range": "5-10年", "count": 420 },
    { "range": "10年以上", "count": 206 }
  ],
  "education_distribution": [
    { "level": "专科", "count": 150 },
    { "level": "本科", "count": 680 },
    { "level": "硕士", "count": 360 },
    { "level": "博士", "count": 66 }
  ],
  "salary_distribution": [
    { "range": "0-15K", "count": 220 },
    { "range": "15-25K", "count": 380 },
    { "range": "25-40K", "count": 420 },
    { "range": "40K+", "count": 236 }
  ],
  "tag_distribution": [
    { "tag": "已面试", "count": 78 },
    { "tag": "重点关注", "count": 45 },
    { "tag": "淘汰", "count": 23 }
  ]
}
```

---

## 十、数据模型定义

### 10.1 ResumeListItem

```json
{
  "resume_id": "res_xxx",
  "candidate_id": "cand_xxx",
  "name": "张三",
  "gender": "男",
  "age": 30,
  "education": "本科",
  "education_level": 1,
  "work_years": 5,
  "skills": ["Java", "Spring Boot", "MySQL"],
  "expected_salary": { "min": 20, "max": 30 },
  "tags": ["已面试"],
  "is_favorite": false,
  "parse_status": "completed",
  "location": "北京",
  "created_at": "2026-06-26T10:00:00Z"
}
```

### 10.2 ResumeDetail

```json
{
  "resume_id": "res_xxx",
  "candidate_id": "cand_xxx",
  "basic_info": {
    "name": "张三",
    "phone_masked": "138****1234",
    "email_masked": "zhang***@xx.com",
    "gender": "男",
    "age": 30,
    "location": "北京"
  },
  "education": "本科",
  "education_level": 1,
  "work_years": 5,
  "skills": ["Java", "Spring Boot", "MySQL", "Redis"],
  "work_experience": [
    {
      "company": "XX科技",
      "position": "高级Java开发",
      "start_date": "2021-06",
      "end_date": "至今",
      "description": "负责后端微服务架构设计..."
    }
  ],
  "education_detail": [
    {
      "school": "XX大学",
      "major": "计算机科学",
      "degree": "本科",
      "start_date": "2016-09",
      "end_date": "2020-06"
    }
  ],
  "summary": "5年Java后端开发经验...",
  "expected_salary": { "min": 20, "max": 30 },
  "file_info": {
    "file_name": "张三_简历.pdf",
    "file_type": "pdf",
    "file_size": 1024000
  },
  "parse_info": {
    "parse_status": "completed",
    "parse_time": "2026-06-26T10:00:00Z"
  },
  "tags": ["已面试"],
  "is_favorite": true,
  "notes": "面试表现良好",
  "interview_notes": [
    {
      "note_id": "note_xxx",
      "interviewer": "李HR",
      "rating": 4,
      "result": "pass",
      "notes": "...",
      "created_at": "2026-06-26T11:00:00Z"
    }
  ],
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T11:00:00Z"
}
```

### 10.3 CandidateCard（推荐卡片）

```json
{
  "candidate_id": "cand_xxx",
  "resume_id": "res_xxx",
  "name": "张三",
  "work_years": 5,
  "education": "本科",
  "skills": ["Java", "Spring Boot", "MySQL"],
  "expected_salary": { "min": 20, "max": 30 },
  "score": 95,
  "reason": "5年Java后端开发经验，技能完全匹配需求，薪资在预期范围内...",
  "tags": ["已面试"],
  "is_favorite": false
}
```

### 10.4 ChatMessage

```json
{
  "message_id": "msg_xxx",
  "session_id": "sess_xxx",
  "role": "assistant",
  "content": "根据您的需求，推荐以下候选人：...",
  "intent": "search",
  "strategy": "hyde",
  "candidates": [ { "candidate_id": "cand_xxx", "name": "张三", "score": 95 } ],
  "created_at": "2026-06-26T10:05:00Z"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| role | string | `user` / `assistant` |
| intent | string | assistant 消息的意图（user 消息为 null） |
| strategy | string | assistant 消息使用的改写策略 |
| candidates | array | assistant 推荐的候选人卡片（user 消息为 null） |

---

## 十一、错误响应示例

### 参数校验失败
```json
{
  "code": 1001,
  "message": "字段 'query' 不能为空",
  "data": null,
  "trace_id": "trace_xxx"
}
```

### 未认证
```json
{
  "code": 1002,
  "message": "Token 已过期，请重新登录",
  "data": null,
  "trace_id": "trace_xxx"
}
```

### 简历解析失败
```json
{
  "code": 2001,
  "message": "PDF 解析失败：文件已损坏",
  "data": { "resume_id": "res_xxx", "file_name": "张三_简历.pdf" },
  "trace_id": "trace_xxx"
}
```

---

## 附录：接口清单速查表

| 模块 | 方法 | 端点 | 说明 |
|------|------|------|------|
| Auth | POST | /auth/login | 登录 |
| Auth | POST | /auth/refresh | 刷新 Token |
| Auth | GET | /auth/me | 当前用户 |
| Auth | POST | /auth/logout | 登出 |
| Resume | POST | /resumes/upload | 上传简历 |
| Resume | GET | /resumes | 简历列表 |
| Resume | GET | /resumes/{id} | 简历详情 |
| Resume | DELETE | /resumes/{id} | 删除简历 |
| Resume | GET | /resumes/{id}/preview | 预览 URL |
| Resume | PUT | /resumes/{id}/tags | 更新标签 |
| Resume | PUT | /resumes/{id}/favorite | 收藏 |
| Resume | PUT | /resumes/{id}/notes | 评价备注 |
| Chat | POST | /chat/sessions | 创建会话 |
| Chat | GET | /chat/sessions | 会话列表 |
| Chat | GET | /chat/sessions/{id}/messages | 消息历史 |
| Chat | POST | /chat/sessions/{id}/messages | 发送消息(SSE) |
| Chat | DELETE | /chat/sessions/{id} | 删除会话 |
| Search | POST | /search | 直接检索 |
| Candidate | POST | /candidates/export | Excel 导出 |
| Candidate | GET | /candidates/{id}/similar | 相似推荐 |
| Candidate | POST | /candidates/compare | 对比 |
| Email | POST | /email/send-recommendation | 发推荐邮件 |
| Email | GET | /email/config | 邮件配置 |
| Email | PUT | /email/config | 更新配置 |
| JD | POST | /jd/match | JD 匹配 |
| Interview | POST | /candidates/{id}/interview-questions | 面试题 |
| Interview | POST | /candidates/{id}/interview-notes | 保存评价 |
| Interview | GET | /candidates/{id}/interview-notes | 评价列表 |
| Dashboard | GET | /dashboard/stats | 看板统计 |
