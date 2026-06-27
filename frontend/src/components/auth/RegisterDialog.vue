<!--
  文件名: components/auth/RegisterDialog.vue
  创建时间: 2026-06-27
  作者: TalentSense Team
  功能描述: 注册申请对话框（HR 自助申请，提交后 status=pending）
    - 用户名/密码/邮箱/姓名表单
    - 提交后提示待管理员审批
-->
<template>
  <el-dialog v-model="visible" title="申请账号" width="420px" :close-on-click-modal="false" align-center>
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="register-form">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="3-20 字符" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" show-password placeholder="8-32 字符" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="可选" />
      </el-form-item>
      <el-form-item label="姓名" prop="name">
        <el-input v-model="form.name" placeholder="可选" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">提交申请</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * RegisterDialog 注册申请对话框
 * 通过 open() 方法打开，提交后调用 register API
 */
import { ref, reactive } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { register } from '@/api/auth'

const visible = ref<boolean>(false)
const loading = ref<boolean>(false)
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  password: '',
  email: '',
  name: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '3-20 字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 32, message: '8-32 字符', trigger: 'blur' },
  ],
}

/** 打开对话框并重置表单 */
function open(): void {
  form.username = ''
  form.password = ''
  form.email = ''
  form.name = ''
  visible.value = true
}

/** 提交注册申请 */
async function handleSubmit(): Promise<void> {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    await register({
      username: form.username.trim(),
      password: form.password,
      email: form.email || undefined,
      name: form.name || undefined,
    })
    ElMessage.success('申请已提交，待管理员审批')
    visible.value = false
  } catch (err) {
    const msg = err instanceof Error ? err.message : '申请失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

defineExpose({ open })
</script>

<style scoped lang="scss">
.register-form {
  :deep(.el-form-item__label) {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--color-ink-soft);
    padding-bottom: 4px;
  }
  :deep(.el-input__wrapper) {
    border-radius: var(--radius-md);
  }
}
</style>
