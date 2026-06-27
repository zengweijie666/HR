<!--
  文件名: views/Settings.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 设置页
    - 顶部页头：eyebrow + 大标题
    - 邮件 SMTP 配置卡片：主机/端口/账号/密码 + 保存
    - 测试邮件卡片：收件人邮箱 + 发送测试邮件按钮（验证 SMTP 配置是否正确）
    - onMounted：调 getConfig 加载
    - 保存：调 updateConfig API + ElMessage.success
-->
<template>
  <div class="page-settings">
    <!-- 页头 -->
    <header class="page-settings__head">
      <span class="eyebrow">CONFIGURATION</span>
      <h1 class="page-settings__title decor-line">设置</h1>
    </header>

    <!-- 邮件配置卡片 -->
    <section class="settings-card">
      <LoadingOverlay :visible="loading" />

      <div class="settings-card__head">
        <h3 class="settings-card__title decor-line">邮件服务器</h3>
        <p class="settings-card__desc">配置 SMTP 服务器用于候选人推荐邮件发送</p>
      </div>

      <el-form
        :model="form"
        label-width="120px"
        class="settings-card__form"
        label-position="right"
      >
        <el-form-item label="SMTP 主机">
          <el-input v-model="form.smtp_host" placeholder="如 smtp.example.com" />
        </el-form-item>

        <el-form-item label="端口">
          <el-input-number v-model="form.smtp_port" :min="1" :max="65535" controls-position="right" />
        </el-form-item>

        <el-form-item label="账号">
          <el-input v-model="form.smtp_user" placeholder="发件邮箱账号" />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="form.smtp_password"
            type="password"
            show-password
            placeholder="留空表示不修改密码"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">
            保存配置
          </el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- 发送测试邮件卡片 -->
    <section class="settings-card">
      <div class="settings-card__head">
        <h3 class="settings-card__title decor-line">发送测试邮件</h3>
        <p class="settings-card__desc">向指定邮箱发送一封测试邮件，用于验证 SMTP 配置是否正确</p>
      </div>

      <el-form
        :model="testForm"
        :rules="testRules"
        ref="testFormRef"
        label-width="120px"
        class="settings-card__form"
        label-position="right"
      >
        <el-form-item label="收件人邮箱" prop="to_email">
          <el-input v-model="testForm.to_email" placeholder="example@domain.com" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="testing" @click="handleSendTest">
            发送测试邮件
          </el-button>
        </el-form-item>
      </el-form>
    </section>
  </div>
</template>

<script setup lang="ts">
/**
 * Settings 设置页
 * 加载并保存邮件 SMTP 配置，发送测试邮件验证配置
 */
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import { getConfig, updateConfig, sendTestMail } from '@/api/email'
import type { EmailConfig } from '@/types/email'

const loading = ref<boolean>(false)
const saving = ref<boolean>(false)
const testing = ref<boolean>(false)

const form = reactive<EmailConfig>({
  smtp_host: '',
  smtp_port: 465,
  smtp_user: '',
  smtp_password: '',
})

// 测试邮件表单
const testFormRef = ref<FormInstance>()
const testForm = reactive({ to_email: '' })
const testRules: FormRules = {
  to_email: [
    { required: true, message: '请输入收件人邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
}

/**
 * 加载邮件配置
 */
async function loadConfig(): Promise<void> {
  loading.value = true
  try {
    const data = await getConfig()
    form.smtp_host = data.smtp_host || ''
    form.smtp_port = data.smtp_port || 465
    form.smtp_user = data.smtp_user || ''
    form.smtp_password = ''
  } catch (err) {
    const msg = err instanceof Error ? err.message : '加载配置失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

/**
 * 保存邮件配置
 */
async function handleSave(): Promise<void> {
  saving.value = true
  try {
    const payload: Partial<EmailConfig> = {
      smtp_host: form.smtp_host,
      smtp_port: form.smtp_port,
      smtp_user: form.smtp_user,
    }
    if (form.smtp_password) {
      payload.smtp_password = form.smtp_password
    }
    await updateConfig(payload)
    ElMessage.success('配置已保存')
    form.smtp_password = ''
  } catch (err) {
    const msg = err instanceof Error ? err.message : '保存配置失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

/**
 * 发送测试邮件
 */
async function handleSendTest(): Promise<void> {
  if (!testFormRef.value) return
  try { await testFormRef.value.validate() } catch { return }
  testing.value = true
  try {
    await sendTestMail({ to_email: testForm.to_email.trim() })
    ElMessage.success('测试邮件发送成功，请查收')
  } catch (err) {
    const msg = err instanceof Error ? err.message : '发送失败'
    ElMessage.error(msg)
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  void loadConfig()
})
</script>

<style scoped lang="scss">
.page-settings {
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
}

/* ============ 配置卡片 ============ */
.settings-card {
  position: relative;
  max-width: 720px;
  padding: var(--space-6) var(--space-8);
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);

  &__head {
    margin-bottom: var(--space-6);
  }

  &__title {
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-weight: 500;
    color: var(--color-primary);
    margin: 0;
    padding-bottom: 6px;
  }

  &__desc {
    margin-top: var(--space-3);
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
  }

  &__form {
    max-width: 560px;

    :deep(.el-form-item__label) {
      font-size: var(--text-sm);
      color: var(--color-ink-soft);
      font-weight: 500;
    }

    :deep(.el-input__wrapper) {
      border-radius: var(--radius-md);
    }
  }
}
</style>
