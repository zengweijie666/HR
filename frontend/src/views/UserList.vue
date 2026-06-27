<!--
  文件名: views/UserList.vue
  创建时间: 2026-06-27
  作者: TalentSense Team
  功能描述: 用户管理页（仅 admin 可见）
    - 顶部页头：eyebrow + 大标题
    - 工具栏：状态/角色/关键词筛选 + 创建账号按钮
    - 表格：用户名/姓名/邮箱/角色/状态/创建时间/操作
    - 操作：审批通过/拒绝、启用/禁用、重置密码、删除
    - 分页：底部右侧
-->
<template>
  <div class="page-users">
    <!-- 页头 -->
    <header class="page-users__head">
      <span class="eyebrow">USER MANAGEMENT</span>
      <h1 class="page-users__title decor-line">用户管理</h1>
      <p class="page-users__subtitle">
        管理系统用户账号，审批注册申请，启用/禁用或重置密码
      </p>
    </header>

    <!-- 工具栏 -->
    <div class="page-users__toolbar">
      <div class="page-users__filters">
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px" @change="loadList">
          <el-option label="待审批" value="pending" />
          <el-option label="正常" value="approved" />
          <el-option label="禁用" value="disabled" />
        </el-select>
        <el-select v-model="filters.role" placeholder="角色" clearable style="width: 120px" @change="loadList">
          <el-option label="管理员" value="admin" />
          <el-option label="HR" value="hr" />
        </el-select>
        <el-input
          v-model="filters.keyword"
          placeholder="用户名/姓名"
          clearable
          style="width: 200px"
          @keyup.enter="loadList"
          @clear="loadList"
        />
        <el-button @click="loadList">查询</el-button>
      </div>
      <el-button type="primary" @click="openCreate">创建账号</el-button>
    </div>

    <!-- 表格 -->
    <div class="page-users__table-wrap">
      <LoadingOverlay :visible="loading" />
      <el-table :data="list" class="page-users__table">
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : 'HR' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button size="small" type="success" @click="handleApprove(row)">通过</el-button>
              <el-button size="small" type="danger" @click="handleReject(row)">拒绝</el-button>
            </template>
            <template v-else>
              <el-button v-if="row.status === 'approved'" size="small" @click="handleToggleStatus(row, 'disabled')">禁用</el-button>
              <el-button v-else size="small" type="success" @click="handleToggleStatus(row, 'approved')">启用</el-button>
              <el-button size="small" @click="openReset(row)">重置密码</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="page-users__pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        background
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadList"
        @size-change="loadList"
      />
    </div>

    <!-- 创建账号对话框 -->
    <el-dialog v-model="createVisible" title="创建账号" width="440px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="createForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="createForm.name" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="createForm.role">
            <el-radio value="hr">HR</el-radio>
            <el-radio value="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetVisible" title="重置密码" width="400px">
      <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-position="top">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetForm.new_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleReset">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * UserList 用户管理页
 * 加载用户列表，支持筛选/创建/审批/启禁用/重置密码/删除
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import {
  listUsers, createUser, approveUser, rejectUser,
  updateUserStatus, resetUserPassword, deleteUser,
} from '@/api/user'
import type { UserListItem, UserStatus, UserRole } from '@/types/user'

const list = ref<UserListItem[]>([])
const loading = ref<boolean>(false)
const submitLoading = ref<boolean>(false)

const filters = reactive({
  status: '' as UserStatus | '',
  role: '' as UserRole | '',
  keyword: '',
})

const pagination = reactive({ page: 1, page_size: 20, total: 0 })

// 创建账号表单
const createVisible = ref<boolean>(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  username: '', password: '', email: '', name: '', role: 'hr' as UserRole,
})
const createRules: FormRules = {
  username: [{ required: true, min: 3, max: 20, message: '3-20 字符', trigger: 'blur' }],
  password: [{ required: true, min: 8, max: 32, message: '8-32 字符', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

// 重置密码表单
const resetVisible = ref<boolean>(false)
const resetFormRef = ref<FormInstance>()
const resetForm = reactive({ new_password: '' })
const resetTargetId = ref<string>('')
const resetRules: FormRules = {
  new_password: [{ required: true, min: 8, max: 32, message: '8-32 字符', trigger: 'blur' }],
}

/** 状态标签类型 */
function statusType(s: UserStatus): 'warning' | 'success' | 'info' {
  return s === 'pending' ? 'warning' : s === 'approved' ? 'success' : 'info'
}

/** 状态标签文本 */
function statusText(s: UserStatus): string {
  return s === 'pending' ? '待审批' : s === 'approved' ? '正常' : '禁用'
}

/** 加载用户列表 */
async function loadList(): Promise<void> {
  loading.value = true
  try {
    const data = await listUsers({
      page: pagination.page,
      page_size: pagination.page_size,
      status: filters.status || undefined,
      role: filters.role || undefined,
      keyword: filters.keyword || undefined,
    })
    list.value = data.list ?? []
    pagination.total = data.total ?? 0
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载失败')
  } finally {
    loading.value = false
  }
}

/** 打开创建账号对话框 */
function openCreate(): void {
  createForm.username = ''
  createForm.password = ''
  createForm.email = ''
  createForm.name = ''
  createForm.role = 'hr'
  createVisible.value = true
}

/** 提交创建账号 */
async function handleCreate(): Promise<void> {
  if (!createFormRef.value) return
  try { await createFormRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    await createUser({
      username: createForm.username.trim(),
      password: createForm.password,
      role: createForm.role,
      email: createForm.email.trim(),
      name: createForm.name.trim(),
    })
    ElMessage.success('创建成功')
    createVisible.value = false
    await loadList()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '创建失败')
  } finally {
    submitLoading.value = false
  }
}

/** 审批通过 */
async function handleApprove(row: UserListItem): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认通过 ${row.username} 的申请？`, '审批', { type: 'warning' })
    await approveUser(row.user_id)
    ElMessage.success('已通过')
    await loadList()
  } catch { /* cancel */ }
}

/** 拒绝申请 */
async function handleReject(row: UserListItem): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认拒绝 ${row.username} 的申请？此操作不可恢复`, '拒绝', { type: 'warning' })
    await rejectUser(row.user_id)
    ElMessage.success('已拒绝')
    await loadList()
  } catch { /* cancel */ }
}

/** 启用/禁用 */
async function handleToggleStatus(row: UserListItem, status: UserStatus): Promise<void> {
  const action = status === 'disabled' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确认${action} ${row.username}？`, action, { type: 'warning' })
    await updateUserStatus(row.user_id, status)
    ElMessage.success(`已${action}`)
    await loadList()
  } catch { /* cancel */ }
}

/** 打开重置密码对话框 */
function openReset(row: UserListItem): void {
  resetTargetId.value = row.user_id
  resetForm.new_password = ''
  resetVisible.value = true
}

/** 提交重置密码 */
async function handleReset(): Promise<void> {
  if (!resetFormRef.value) return
  try { await resetFormRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    await resetUserPassword(resetTargetId.value, resetForm.new_password)
    ElMessage.success('密码已重置')
    resetVisible.value = false
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '重置失败')
  } finally {
    submitLoading.value = false
  }
}

/** 删除账号 */
async function handleDelete(row: UserListItem): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认删除 ${row.username}？此操作不可恢复`, '删除', { type: 'error' })
    await deleteUser(row.user_id)
    ElMessage.success('已删除')
    await loadList()
  } catch { /* cancel */ }
}

onMounted(() => { void loadList() })
</script>

<style scoped lang="scss">
.page-users {
  position: relative;
  min-height: 100%;

  &__head {
    margin-bottom: var(--space-6);
    animation: fadeInUp var(--duration-slow) var(--ease-out) both;
  }

  &__title {
    margin-top: var(--space-3);
    font-family: var(--font-display);
    font-size: 32px;
    font-weight: 500;
    color: var(--color-primary);
    padding-bottom: 10px;
    letter-spacing: -0.02em;
  }

  &__subtitle {
    margin-top: var(--space-3);
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
  }

  &__toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-4);
    padding: var(--space-4) var(--space-6);
    background-color: var(--color-bg-card);
    border: 1px solid var(--color-line);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
  }

  &__filters {
    display: flex;
    gap: var(--space-3);
    align-items: center;
  }

  &__table-wrap {
    position: relative;
    padding: var(--space-4) var(--space-6);
    background-color: var(--color-bg-card);
    border: 1px solid var(--color-line);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
  }

  &__table {
    width: 100%;
  }

  &__pagination {
    margin-top: var(--space-4);
    display: flex;
    justify-content: flex-end;
  }
}
</style>
