# 简历库筛选增强与脱敏改造设计

- **创建时间**: 2026-06-27
- **作者**: TalentSense Team
- **状态**: 待评审
- **关联计划**: docs/plans/2026-06-27-resume-filters-and-unmask.md（待 writing-plans 生成）

## 一、背景与目标

用户在使用简历库过程中提出以下优化诉求：

1. **邮件和电话不要脱敏** —— HR 录用流程需要真实联系方式
2. **在简历页面发送邮件可自动填写邮件** —— 从列表/详情触发发邮件时自动预填收件人
3. **收藏筛选缺失** —— 有收藏功能但无法按收藏状态筛选
4. **按入库时间筛选 + 优先展示新简历** —— HR 关注新入库候选人
5. **其他体验优化** —— 扫描代码后补充：卡片显示入库时间、分页大小可切换、排序选项、列表总数统计

## 二、需求清单

| # | 需求 | 类型 | 涉及层 |
|---|------|------|--------|
| R1 | 脱敏改造（admin 看原始，普通用户看脱敏） | 功能变更 | 后端 + 前端 |
| R2 | 发邮件自动预填收件人邮箱 | 新增 | 前端 |
| R3 | 收藏筛选下拉 | 新增 | 前端 + 后端（已支持） |
| R4 | 卡片显示入库相对时间 | 新增 | 前端 |
| R5 | 入库日期范围筛选 | 新增 | 前端 + 后端 |
| R6 | 分页大小可切换 | 新增 | 前端 |
| R7 | 排序选项（入库时间/工作经验/学历） | 新增 | 前端 + 后端 |
| R8 | 列表总数统计文案 | 新增 | 前端 |

## 三、详细设计

### R1. 脱敏改造（RBAC 角色区分）

#### 现状
- `resume_service.py` 第 207-208 行存储 `phone_masked`/`email_masked`，不存原始值
- `pii.py` 提供 `mask_phone`/`mask_email`/`hash_phone`/`hash_email`
- 列表和详情接口都只返回 masked 字段

#### 设计
**存储层**（`resume_service.py` 第 205-212 行 `basic_info`）：
```python
"basic_info": {
    "name": structured.get("name", ""),
    "phone": structured.get("phone", ""),           # 新增：原始值
    "email": structured.get("email", ""),           # 新增：原始值
    "phone_masked": mask_phone(structured.get("phone", "")),  # 保留：兜底
    "email_masked": mask_email(structured.get("email", "")),  # 保留：兜底
    "phone_hash": phone_h, "email_hash": email_h,   # 保留：去重
    "gender": ..., "age": ..., "location": ...,
}
```

**查询层**（`list()` 和 `get_detail()`）：
- 方法签名增加 `current_user: Optional[dict] = None` 参数
- 扁平化时判断角色：
  ```python
  is_admin = current_user and current_user.get("role") == "admin"
  for key in ("name", "gender", "age", "location"):
      item[key] = basic.get(key)
  if is_admin:
      item["phone"] = basic.get("phone", "")
      item["email"] = basic.get("email", "")
  else:
      item["phone_masked"] = basic.get("phone_masked", "")
      item["email_masked"] = basic.get("email_masked", "")
  ```

**API 路由层**（`api/resumes.py`）：
- 所有路由通过 `Depends(get_current_user)` 注入当前用户
- 调用 service 方法时传入 `current_user=user`

**前端类型**（`types/resume.ts`）：
```typescript
export interface ResumeListItem {
  // ... 现有字段
  phone?: string        // admin 可见
  email?: string        // admin 可见
  phone_masked?: string // 普通用户可见
  email_masked?: string // 普通用户可见
}
```

**前端展示**：
- `ResumeDetail.vue` 第 43-46 行：优先显示 `phone`/`email`，回退到 masked
- `SendEmailDialog` 预填 `to_email` 时优先用 `email` 字段

#### 向后兼容
- MongoDB 旧文档没有 `phone`/`email` 字段，admin 用户会看到空字符串 → 需要在 `_flatten_doc` 中兜底：`basic.get("phone") or basic.get("phone_masked", "")`

### R2. 发邮件自动预填收件人

#### 现状
- `ResumeList.handleSendEmail` 只预填 `candidate_name` 变量
- `ResumeDetail.handleSendEmail` 只预填变量，未预填 `to_email`

#### 设计
**列表页**（`ResumeList.vue` 第 249-256 行）：
```typescript
function handleSendEmail(resumeId: string): void {
  const item = resumeStore.list.find((r) => r.resume_id === resumeId)
  sendEmailDialogRef.value?.open({
    to_email: item?.email || item?.email_masked || '',  // 优先原始值
    variables: {
      candidate_name: item?.name ?? '',
    },
  })
}
```

**详情页**（`ResumeDetail.vue` 第 323-334 行）：
```typescript
function handleSendEmail(): void {
  if (!detail.value) return
  sendEmailDialogRef.value?.open({
    to_email: detail.value.email || detail.value.email_masked || '',
    variables: {
      candidate_name: detail.value.basic_info?.name ?? detail.value.name ?? '',
      // ... 其他变量保持不变
    },
  })
}
```

**前提**：R1 让 list 接口也返回 email 字段（admin 原始/普通用户 masked）

### R3. 收藏筛选下拉

#### 现状
- 后端 `list()` 已支持 `is_favorite` 查询（第 410-413 行附近）
- 前端 `ResumeListQuery` 已有 `is_favorite?: boolean` 字段
- FilterBar 没有收藏筛选 UI

#### 设计
**FilterBar.vue** 加下拉：
```vue
<el-select v-model="favoriteFilter" placeholder="收藏" clearable style="width: 120px">
  <el-option label="已收藏" :value="true" />
  <el-option label="未收藏" :value="false" />
</el-select>
```

**ResumeFilters 接口** 增加字段：
```typescript
export interface ResumeFilters {
  keyword?: string
  education_min?: number
  work_years_min?: number
  is_favorite?: boolean  // 新增
}
```

### R4. 卡片显示入库相对时间

#### 设计
**工具函数**（`utils/format.ts` 新增）：
```typescript
/** 计算相对时间，如「今天」「3 天前」「2 周前」「1 个月前」 */
export function formatRelativeTime(isoDate: string): string {
  if (!isoDate) return ''
  const date = new Date(isoDate)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays} 天前`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} 周前`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} 个月前`
  return `${Math.floor(diffDays / 365)} 年前`
}
```

**ResumeCard.vue** 底部学历旁加：
```vue
<span v-if="resume.created_at" class="resume-card__dot">·</span>
<span v-if="resume.created_at" class="resume-card__time">
  {{ formatRelativeTime(resume.created_at) }}
</span>
```

### R5. 入库日期范围筛选

#### 后端设计
**`resume_service.py` `list()` 方法** 增加参数：
```python
async def list(
    self,
    page: int = 1, page_size: int = 20,
    keyword: str = "", tag: str = "",
    is_favorite: Optional[bool] = None,
    education_min: Optional[int] = None,
    work_years_min: Optional[int] = None,
    salary_min: Optional[int] = None, salary_max: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,  # 新增：ISO 日期
    date_to: Optional[str] = None,    # 新增：ISO 日期
    sort_by: str = "created_at",      # 新增：R7
    sort_order: str = "desc",         # 新增：R7
    current_user: Optional[dict] = None,  # 新增：R1
) -> dict:
```

**查询构建**：
```python
if date_from:
    query["created_at"] = {"$gte": date_from}
if date_to:
    query.setdefault("created_at", {})["$lte"] = date_to + "T23:59:59"
```

**API 入参**（`api/resumes.py`）：路由参数增加 `date_from`/`date_to`/`sort_by`/`sort_order`

#### 前端设计
**FilterBar.vue** 加日期范围选择器：
```vue
<el-date-picker
  v-model="dateRange"
  type="daterange"
  range-separator="至"
  start-placeholder="开始日期"
  end-placeholder="结束日期"
  value-format="YYYY-MM-DD"
  style="width: 260px"
/>
```

**handleSearch** 提交时转换：
```typescript
function handleSearch(): void {
  emit('search', {
    keyword: keyword.value || undefined,
    education_min: educationMin.value,
    work_years_min: workYearsMin.value,
    is_favorite: favoriteFilter.value,
    date_from: dateRange.value?.[0],
    date_to: dateRange.value?.[1],
    sort_by: sortBy.value,
    sort_order: sortOrder.value,
  })
}
```

### R6. 分页大小可切换

**ResumeList.vue** 第 70-78 行：
```vue
<el-pagination
  background
  layout="total, sizes, prev, pager, next"
  :total="resumeStore.total"
  :page-size="pageSize"
  :page-sizes="[10, 20, 50, 100]"
  :current-page="page"
  @current-change="handlePageChange"
  @size-change="handleSizeChange"
/>
```

**新增 handleSizeChange**：
```typescript
function handleSizeChange(size: number): void {
  pageSize.value = size
  page.value = 1
  void loadList()
}
```

**分页显示条件**改为 `resumeStore.total > 0`（原来是 `> pageSize`，切换大小时会闪烁）

### R7. 排序选项

**FilterBar.vue** 加排序下拉：
```vue
<el-select v-model="sortBy" style="width: 140px" @change="handleSearch">
  <el-option label="入库时间" value="created_at" />
  <el-option label="工作经验" value="work_years" />
  <el-option label="学历" value="education_level" />
</el-select>
<el-select v-model="sortOrder" style="width: 100px" @change="handleSearch">
  <el-option label="降序" value="desc" />
  <el-option label="升序" value="asc" />
</el-select>
```

**后端** `list()` 第 434 行：
```python
cursor = self.resumes_coll.find(query, {"_id": 0}).skip(skip).limit(page_size).sort(sort_by, 1 if sort_order == "asc" else -1)
```

### R8. 列表总数统计

**ResumeList.vue** 工具栏右侧加文案：
```vue
<div class="page-resume-list__stats">
  共 <strong>{{ resumeStore.total }}</strong> 份简历
</div>
```

## 四、数据流

### 列表查询流程（改造后）
```
用户操作 FilterBar → handleSearch 组装查询参数
  ↓
ResumeList.loadList() 调用 getResumeList(query)
  ↓
API: GET /api/v1/resumes?keyword=...&is_favorite=...&date_from=...&sort_by=...
  ↓
路由层: Depends(get_current_user) → 注入 current_user
  ↓
resume_service.list(..., current_user=user)
  ↓
MongoDB: db.resumes.find(query).sort(sort_by, sort_order)
  ↓
扁平化: 根据 current_user.role 决定返回 phone/email 还是 phone_masked/email_masked
  ↓
返回 {list, total, page, page_size, total_pages}
  ↓
前端: resumeStore.setList(res.list) + setTotal(res.total)
  ↓
ResumeCard 渲染: 姓名/技能/入库时间/手机/邮箱
```

### 发邮件流程（改造后）
```
用户点击卡片邮件按钮 → handleSendEmail(resumeId)
  ↓
从 resumeStore.list 找到 item（已含 email/email_masked 字段）
  ↓
SendEmailDialog.open({ to_email: item.email || item.email_masked, variables: {...} })
  ↓
用户确认 → sendMail API
```

## 五、错误处理

| 场景 | 处理方式 |
|------|----------|
| current_user 为 None（未登录） | 返回 masked 字段（保守默认） |
| 旧简历文档无 phone/email 字段 | admin 看到 masked 值作为兜底 |
| 日期格式错误 | 后端 try/except 返回空结果，不崩溃 |
| sort_by 字段非法 | 后端白名单校验，默认 created_at |
| 日期范围 date_from > date_to | 后端交换两个值 |

## 六、测试策略

### 后端测试（`test_resume_service.py`）
- `test_list_returns_raw_phone_for_admin`：admin 用户看到原始 phone/email
- `test_list_returns_masked_for_normal_user`：普通用户看到 masked
- `test_list_returns_masked_when_no_user`：current_user=None 返回 masked
- `test_list_falls_back_to_masked_for_old_resumes`：旧文档无 phone 字段时 admin 兜底
- `test_list_filter_by_date_range`：date_from/date_to 筛选生效
- `test_list_sort_by_work_years`：sort_by=work_years 排序正确
- `test_list_invalid_sort_by_defaults_to_created_at`：非法 sort_by 兜底
- `test_list_invalid_date_range_swapped`：date_from > date_to 自动交换

### 前端测试
- `test_format_relative_time`：相对时间函数各分支
- `test_filter_bar_emits_favorite_filter`：收藏筛选触发 search
- `test_filter_bar_emits_date_range`：日期范围触发 search
- `test_filter_bar_emits_sort_options`：排序选项触发 search
- `test_resume_card_shows_relative_time`：卡片显示入库时间
- `test_resume_list_pagination_size_change`：分页大小切换
- `test_resume_list_shows_total_count`：总数统计文案
- `test_send_email_prefills_to_email`：发邮件预填收件人

## 七、影响范围

### 后端
- `app/services/resume_service.py`：存储增加 phone/email、list/get_detail 改造
- `app/api/resumes.py`：路由注入 current_user、增加查询参数
- `app/utils/pii.py`：无需改动（mask/hash 函数保留）

### 前端
- `src/types/resume.ts`：增加 phone/email/created_at 等字段
- `src/utils/format.ts`：新增 formatRelativeTime
- `src/components/resume/FilterBar.vue`：收藏下拉 + 日期范围 + 排序
- `src/components/resume/ResumeCard.vue`：显示入库时间
- `src/views/ResumeList.vue`：分页大小 + 总数统计 + 发邮件预填
- `src/views/ResumeDetail.vue`：显示原始手机/邮箱、发邮件预填

### 数据库
- 无需迁移：旧文档保留 masked 字段，新文档同时存 phone/email/masked
- 可选：编写一次性脚本回填旧文档的 phone/email 字段（从 masked 反推不可行，需重新解析）

## 八、不实现的内容（YAGNI）

- 不做邮箱验证（发送时由 SMTP 校验）
- 不做手机号格式校验（解析时已处理）
- 不做多角色权限细分（只区分 admin/非 admin）
- 不做收藏计数统计
- 不做时间筛选快捷选项（用户已选日期范围）
