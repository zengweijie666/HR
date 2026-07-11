# 认证与权限控制设计

- 文件名: docs/specs/2026-06-27-auth-rbac-design.md
- 创建时间: 2026-06-27
- 作者: TalentSense Team
- 功能描述: 注册功能 + 角色权限控制（RBAC）+ 用户管理的设计规范

## 1. 背景与目标

### 1.1 现状
- 仅有 `/auth/login`、`/auth/refresh`、`/auth/me`、`/auth/logout` 接口
- users 表无 status / role 强约束（role 默认 "hr"）
- 无注册功能，账号靠手动插入 MongoDB
- 所有业务接口对已登录用户一视同仁，无角色区分

### 1.2 目标
1. 后端启动时自动初始化管理员账号（.env 配置）
2. 支持双路径注册：
   - 管理员在用户管理页直接开号（approved）
   - HR 在登录页自助申请（pending），管理员审批后才能登录
3. RBAC 权限控制：admin / hr 两角色
   - hr：招聘业务功能全开放（上传/检索/收藏/标签/备注/JD 匹配/对话/导出/看板/面试评价写入）
   - admin：hr 所有权限 + 删除类操作 + 用户管理 + SMTP 配置
4. 用户管理页（仅 admin 可见）：创建/审批/启用禁用/重置密码/删除

## 2. 数据模型

### 2.1 MongoDB users 表（扩展）

```js
{
  user_id: "u_xxxxxxxxxxxx",         // 主键，uuid
  username: "admin",                  // 唯一
  password_hash: "$2b$12$...",        // bcrypt
  email: "admin@test.com",            // 可选
  name: "管理员",                     // 显示名（可选，默认用 username）
  role: "admin" | "hr",               // 角色，默认 "hr"
  status: "approved" | "pending" | "disabled",  // 账号状态
  created_at: "2026-06-27T...",
  updated_at: "2026-06-27T...",
}
```

索引：
- `username` unique
- `role` + `status` 复合索引（列表筛选）

### 2.2 状态流转

```
自助申请 ─┐
          ├──> pending ──approve──> approved ──disable──> disabled
管理员开号 ──────────────────────> approved ──enable───> approved
                                    │
                                    └──reject/delete──> (记录删除)
```

- pending：仅 admin 可见，HR 无法登录
- approved：正常使用
- disabled：保留数据但禁止登录

## 3. API 设计

所有路由遵循 `/api/v1/[module]` 前缀，统一响应 `{code, message, data, trace_id}`。

### 3.1 认证扩展（/api/v1/auth）

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/auth/register` | 公开 | HR 自助申请，status=pending，role=hr |
| POST | `/auth/login` | 公开 | 增加 status 校验：pending/disabled 拒绝登录 |
| POST | `/auth/refresh` | 公开 | 不变 |
| GET | `/auth/me` | 已登录 | 不变 |
| POST | `/auth/logout` | 已登录 | 不变 |
| PUT | `/auth/password` | 已登录 | 修改自己密码（需 old_password） |

#### 3.1.1 注册请求/响应

```json
// POST /auth/register
// 请求
{
  "username": "zhangsan",
  "password": "Pass@1234",
  "email": "zhangsan@test.com",  // 可选
  "name": "张三"                  // 可选
}
// 响应
{
  "code": 0, "message": "success",
  "data": {"user_id": "u_xxx", "username": "zhangsan", "status": "pending"}
}
```

校验：
- username 3-20 字符，唯一
- password 8-32 字符
- email 格式校验（若提供）

#### 3.1.2 登录状态校验

```python
# login 流程增加 status 校验
if user_doc.get("status") != "approved":
    if user_doc.get("status") == "pending":
        raise AuthError("账号待审批，请联系管理员")
    elif user_doc.get("status") == "disabled":
        raise AuthError("账号已禁用，请联系管理员")
```

### 3.2 用户管理（/api/v1/users，全部 admin only）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/users` | 分页列表，支持 status/role/keyword 筛选 |
| POST | `/users` | 管理员直接开号（status=approved） |
| GET | `/users/{user_id}` | 详情 |
| PUT | `/users/{user_id}/approve` | 审批通过（pending → approved） |
| PUT | `/users/{user_id}/reject` | 拒绝申请（直接删除记录） |
| PUT | `/users/{user_id}/status` | 启用/禁用（body: {"status": "approved"\|"disabled"}） |
| PUT | `/users/{user_id}/password` | 重置密码（body: {"new_password": "..."}） |
| DELETE | `/users/{user_id}` | 删除账号（硬删除，不可恢复） |

#### 3.2.1 列表响应

```json
// GET /users?page=1&page_size=20&status=pending&role=hr&keyword=zhang
{
  "code": 0, "message": "success",
  "data": {
    "list": [
      {
        "user_id": "u_xxx",
        "username": "zhangsan",
        "email": "zhangsan@test.com",
        "name": "张三",
        "role": "hr",
        "status": "pending",
        "created_at": "...",
        "updated_at": "..."
      }
    ],
    "total": 1, "page": 1, "page_size": 20, "total_pages": 1
  }
}
```

### 3.3 管理员自动初始化

在 `app/main.py` 的 `lifespan` 启动事件中：

```python
async def _ensure_admin():
    """启动时检查并创建管理员账号"""
    from app.core.database import MongoDB
    from app.services.auth_service import AuthService
    admin_username = settings.ADMIN_USERNAME
    admin_password = settings.ADMIN_PASSWORD
    admin_email = settings.ADMIN_EMAIL
    
    exists = await MongoDB.db.users.find_one({"username": admin_username})
    if exists:
        logger.info(f"管理员账号 {admin_username} 已存在")
        return
    
    user_id = f"u_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    await MongoDB.db.users.insert_one({
        "user_id": user_id,
        "username": admin_username,
        "password_hash": AuthService.hash_password(admin_password),
        "email": admin_email,
        "name": "管理员",
        "role": "admin",
        "status": "approved",
        "created_at": now,
        "updated_at": now,
    })
    logger.info(f"管理员账号 {admin_username} 已自动创建")
```

### 3.4 .env 配置项扩展

```bash
# 管理员初始化
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password-here
ADMIN_EMAIL=admin@test.com
```

更新 `.env.example` 与 `app/core/config.py`。

## 4. 权限控制实现

### 4.1 依赖注入

```python
# app/api/deps.py
async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """校验 token，返回 user payload（已有）"""
    ...

async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """要求 admin 角色"""
    if user.get("role") != "admin":
        raise AuthError("需要管理员权限")
    return user
```

### 4.2 接口权限矩阵

| 接口 | hr | admin |
|---|---|---|
| 简历上传/列表/详情/预览/标签/收藏/备注 | ✅ | ✅ |
| 简历删除 | ❌ | ✅ |
| 检索/JD 匹配/对话/候选人推荐 | ✅ | ✅ |
| 面试题生成/评价保存/评价列表 | ✅ | ✅ |
| Excel 导出 | ✅ | ✅ |
| 看板统计 | ✅ | ✅ |
| 邮件发送 | ✅ | ✅ |
| SMTP 配置 GET/PUT | ❌ | ✅ |
| 用户管理全部接口 | ❌ | ✅ |
| 修改自己密码 | ✅ | ✅ |

需要加 `Depends(require_admin)` 的接口：
- `DELETE /api/v1/resumes/{resume_id}`
- `GET /api/v1/email/config`、`PUT /api/v1/email/config`
- `/api/v1/users/*` 全部

## 5. 前端设计

### 5.1 新增页面

#### 5.1.1 用户管理页 `/users`（仅 admin）

- 路由：`/users`，meta 加 `requireAdmin: true`
- 路由守卫：非 admin 访问跳 `/workbench`
- 组件：`UserList.vue` + `UserFormDialog.vue`

功能：
- 分页表格：用户名/邮箱/姓名/角色/状态/创建时间/操作
- 筛选：状态（全部/待审批/正常/禁用）、角色（全部/admin/hr）、关键词
- 操作按钮（按状态显示）：
  - pending：审批通过 / 拒绝
  - approved：禁用 / 重置密码 / 删除
  - disabled：启用 / 重置密码 / 删除
- 顶部"创建账号"按钮：弹出表单（用户名/密码/邮箱/姓名/角色）

#### 5.1.2 登录页扩展

- "登 录" 按钮下方加"申请账号"链接
- 点击弹出 `RegisterDialog.vue`：用户名/密码/邮箱/姓名
- 提交成功提示"申请已提交，待管理员审批"
- 登录失败时若 message 含"待审批"/"已禁用"，红色错误提示

### 5.2 侧边栏菜单

`Layout.vue` 中根据 `authStore.user.role` 动态显示：

```vue
<el-menu-item v-if="authStore.user?.role === 'admin'" index="/users">
  <el-icon><UserFilled /></el-icon>
  <template #title>用户管理</template>
</el-menu-item>
```

### 5.3 顶栏标识

admin 用户头像旁加 "管理员" 标签：

```vue
<el-tag v-if="authStore.user?.role === 'admin'" type="danger" size="small">管理员</el-tag>
```

### 5.4 类型与 API 扩展

```typescript
// types/auth.ts
export interface UserInfo {
  user_id: string
  username: string
  role: 'admin' | 'hr'
  status?: 'approved' | 'pending' | 'disabled'
  email?: string
  name?: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
  name?: string
}

export interface UserListItem {
  user_id: string
  username: string
  email: string
  name: string
  role: 'admin' | 'hr'
  status: 'approved' | 'pending' | 'disabled'
  created_at: string
  updated_at: string
}
```

```typescript
// api/auth.ts 新增
export function register(data: RegisterRequest): Promise<{ user_id: string; username: string; status: string }>
export function changePassword(oldPassword: string, newPassword: string): Promise<void>

// api/user.ts 新增（新文件）
export function listUsers(params): Promise<PageResult<UserListItem>>
export function createUser(data): Promise<UserListItem>
export function approveUser(userId: string): Promise<void>
export function rejectUser(userId: string): Promise<void>
export function updateUserStatus(userId: string, status: string): Promise<void>
export function resetUserPassword(userId: string, newPassword: string): Promise<void>
export function deleteUser(userId: string): Promise<void>
```

### 5.5 路由守卫扩展

```typescript
router.beforeEach(async (to) => {
  if (to.meta.public === true) return true
  const auth = useAuthStore()
  if (!auth.isLoggedIn) return { path: '/login' }
  if (!auth.user) {
    try {
      const me = await getMe()
      auth.setUser(me)
    } catch {
      auth.logout()
      return { path: '/login' }
    }
  }
  // admin 路由权限校验
  if (to.meta.requireAdmin === true && auth.user?.role !== 'admin') {
    return { path: '/workbench' }
  }
  return true
})
```

## 6. 错误处理

### 6.1 业务错误码扩展

```python
# app/core/response.py 新增
CODE.AUTH_PENDING = 1003    # 账号待审批
CODE.AUTH_DISABLED = 1004   # 账号已禁用
CODE.USER_NOT_FOUND = 2001  # 用户不存在
CODE.USERNAME_EXISTS = 2002 # 用户名已存在
CODE.FORBIDDEN = 1005       # 权限不足
```

### 6.2 前端错误处理

- HTTP 401 或业务码 1002/1003/1004 → 跳登录页
- 业务码 1005（权限不足）→ ElMessage.error 提示"需要管理员权限"
- 注册时用户名已存在（2002）→ 表单校验错误提示

## 7. 测试要求

### 7.1 后端单元测试

- `test_auth_service.py`：register / login status 校验 / change_password
- `test_user_service.py`（新）：list/create/approve/reject/status/reset_password/delete
- `test_auth_api.py`：注册接口 / 登录 pending/disabled 拒绝
- `test_users_api.py`（新）：admin 权限校验 / 各操作
- `test_deps.py`（新）：require_admin 拒绝 hr / 通过 admin

### 7.2 前端测试

- `test_user_list.test.ts`：表格渲染 / 筛选 / 操作按钮
- `test_register_dialog.test.ts`：表单校验 / 提交
- `test_router.test.ts`：admin 路由守卫

## 8. 改动范围清单

### 8.1 后端

新增：
- `app/services/user_service.py`
- `app/api/users.py`
- `app/models/user.py`
- `tests/services/test_user_service.py`
- `tests/api/test_users_api.py`

修改：
- `app/services/auth_service.py`：register / login status 校验 / change_password
- `app/api/auth.py`：新增 register / password 路由
- `app/api/deps.py`：新增 require_admin
- `app/core/config.py`：新增 ADMIN_USERNAME/PASSWORD/EMAIL
- `app/core/database.py`：users 表索引
- `app/main.py`：lifespan 加 _ensure_admin
- `app/api/resumes.py`：delete 加 require_admin
- `app/api/email.py`：config 接口加 require_admin
- `app/core/response.py`：新增错误码
- `.env.example`：新增配置项

### 8.2 前端

新增：
- `src/views/UserList.vue`
- `src/components/auth/RegisterDialog.vue`
- `src/components/user/UserFormDialog.vue`
- `src/api/user.ts`
- `src/types/user.ts`

修改：
- `src/views/Login.vue`：加"申请账号"链接
- `src/views/Layout.vue`：admin 菜单项 + 标识
- `src/router/index.ts`：/users 路由 + 守卫
- `src/api/auth.ts`：register / changePassword
- `src/types/auth.ts`：status / role 类型
- `src/stores/auth.ts`：role 持久化

## 9. 实施顺序

1. 后端：config + database + response 扩展
2. 后端：auth_service register + login status 校验 + change_password
3. 后端：deps require_admin + 接口权限加固
4. 后端：user_service + users 路由
5. 后端：main.py 管理员初始化
6. 后端：单元测试
7. 前端：types + api
8. 前端：RegisterDialog + Login 集成
9. 前端：UserList 页面
10. 前端：Layout 菜单 + 路由守卫
11. 前端：测试
12. 联调验证 + git 提交
