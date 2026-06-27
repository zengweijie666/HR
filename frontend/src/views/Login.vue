<!--
  文件名: views/Login.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 登录页（杂志封面级 Editorial Tech 风格）
    - 左右分栏：左 60% 品牌展示（深墨绿背景），右 40% 表单区（奶白背景）
    - 左侧：eyebrow + Fraunces 大标题 + 副文案 + 3 条特性 bullet + 几何装饰
    - 右侧：SIGN IN 小标 + 标题 + 用户名/密码输入 + 全宽登录按钮
    - 移动端（<992px）隐藏品牌区，表单全屏
    - 登录成功：setToken + setUser + 跳转 /workbench
-->
<template>
  <div class="page-login">
    <!-- 左侧品牌展示区 -->
    <aside class="page-login__brand">
      <div class="page-login__brand-inner">
        <span class="page-login__eyebrow eyebrow page-login__eyebrow--light">
          TALENTSENSE · 2026
        </span>

        <h1 class="page-login__title">
          智能招聘的<br />编辑学
        </h1>

        <p class="page-login__subtitle">
          基于 AI 的简历推荐与招聘辅助系统，让每一次人才决策都有据可依。
        </p>

        <ul class="page-login__features">
          <li v-for="feat in features" :key="feat" class="page-login__feature">
            <span class="page-login__feature-line" />
            <span class="page-login__feature-text">{{ feat }}</span>
          </li>
        </ul>
      </div>

      <!-- 几何装饰 -->
      <div class="page-login__decor" aria-hidden="true">
        <span class="page-login__decor-ring" />
        <span class="page-login__decor-dot" />
      </div>
    </aside>

    <!-- 右侧表单区 -->
    <main class="page-login__main">
      <div class="page-login__form-wrap">
        <span class="page-login__eyebrow eyebrow">SIGN IN</span>
        <h2 class="page-login__form-title">欢迎回来</h2>
        <p class="page-login__form-sub">使用你的账号登录 TalentSense HR</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          class="page-login__form"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              size="large"
              placeholder="请输入用户名"
              :prefix-icon="User"
              autocomplete="username"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              size="large"
              type="password"
              show-password
              placeholder="请输入密码"
              :prefix-icon="Lock"
              autocomplete="current-password"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-button
            type="primary"
            class="page-login__submit"
            :loading="loading"
            native-type="submit"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form>

        <p class="page-login__register">
          还没有账号？<a href="javascript:void(0)" @click="registerDialogRef?.open()">申请账号</a>
        </p>
        <RegisterDialog ref="registerDialogRef" />

        <p class="page-login__footnote">
          © 2026 TalentSense · 让招聘更智能
        </p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
/**
 * Login 登录页
 * 表单校验通过后调用 login API，成功写入 token / user 并跳转工作台
 */
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import RegisterDialog from '@/components/auth/RegisterDialog.vue'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref<boolean>(false)
const registerDialogRef = ref<InstanceType<typeof RegisterDialog>>()

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const features: string[] = ['语义检索', '智能匹配', '对话式推荐']

/**
 * 处理登录提交
 * 校验通过后调用 login，写入 token 与用户信息，跳转 /workbench
 */
async function handleLogin(): Promise<void> {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    const data = await login({
      username: form.username.trim(),
      password: form.password,
    })
    authStore.setToken(data.access_token, data.refresh_token)
    if (data.user) {
      authStore.setUser(data.user)
    }
    ElMessage.success('登录成功')
    router.push('/workbench')
  } catch (err) {
    const msg = err instanceof Error ? err.message : '登录失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.page-login {
  display: flex;
  width: 100%;
  min-height: 100vh;
  background-color: var(--color-bg);

  /* ============ 左侧品牌区 ============ */
  &__brand {
    position: relative;
    flex: 0 0 60%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-16) var(--space-16);
    background-color: var(--color-bg-deep);
    overflow: hidden;
  }

  &__brand-inner {
    position: relative;
    z-index: 2;
    max-width: 540px;
    color: #fff;
    animation: fadeInUp var(--duration-slow) var(--ease-out) both;
  }

  &__eyebrow {
    &--light {
      color: var(--color-accent-soft);
      &::before {
        background: var(--color-accent-soft);
      }
    }
  }

  &__title {
    margin-top: var(--space-6);
    font-family: var(--font-display);
    font-size: 64px;
    font-weight: 300;
    line-height: 1.08;
    letter-spacing: -0.02em;
    color: #fff;
    font-optical-sizing: auto;
  }

  &__subtitle {
    margin-top: var(--space-5);
    max-width: 440px;
    font-size: var(--text-md);
    line-height: 1.7;
    color: rgba(255, 255, 255, 0.6);
  }

  &__features {
    list-style: none;
    margin-top: var(--space-10);
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  &__feature {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    color: rgba(255, 255, 255, 0.86);
    font-size: var(--text-base);
    letter-spacing: 0.02em;
  }

  &__feature-line {
    flex-shrink: 0;
    width: 24px;
    height: 2px;
    background: var(--color-accent);
  }

  &__feature-text {
    font-family: var(--font-display);
    font-size: var(--text-md);
  }

  /* 几何装饰 */
  &__decor {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 1;
  }

  &__decor-ring {
    position: absolute;
    right: -120px;
    bottom: -120px;
    width: 420px;
    height: 420px;
    border: 1.5px solid var(--color-accent);
    border-radius: 50%;
    opacity: 0.15;
  }

  &__decor-dot {
    position: absolute;
    right: 80px;
    bottom: 120px;
    width: 12px;
    height: 12px;
    background: var(--color-accent);
    border-radius: 50%;
    opacity: 0.7;
  }

  /* ============ 右侧表单区 ============ */
  &__main {
    flex: 0 0 40%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-12) var(--space-10);
    background-color: var(--color-bg);
  }

  &__form-wrap {
    width: 100%;
    max-width: 380px;
    animation: fadeInUp var(--duration-slow) var(--ease-out) both;
  }

  &__form-title {
    margin-top: var(--space-4);
    font-family: var(--font-display);
    font-size: 28px;
    font-weight: 500;
    color: var(--color-primary);
    letter-spacing: -0.01em;
  }

  &__form-sub {
    margin-top: var(--space-2);
    font-size: var(--text-sm);
    color: var(--color-ink-mute);
  }

  &__form {
    margin-top: var(--space-8);

    :deep(.el-form-item__label) {
      font-size: var(--text-sm);
      font-weight: 500;
      color: var(--color-ink-soft);
      padding-bottom: 4px;
    }

    :deep(.el-input__wrapper) {
      border-radius: var(--radius-md);
      padding: 4px 12px;
    }
  }

  &__submit {
    width: 100%;
    height: 48px;
    margin-top: var(--space-4);
    border-radius: var(--radius-md);
    font-size: var(--text-md);
    letter-spacing: 0.16em;
    font-weight: 500;
    transition: box-shadow var(--duration-base) var(--ease-out),
      transform var(--duration-fast) var(--ease-out);

    &:hover {
      box-shadow: var(--shadow-md);
      transform: translateY(-1px);
    }
  }

  &__footnote {
    margin-top: var(--space-10);
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
    letter-spacing: 0.06em;
    text-align: center;
  }

  &__register {
    margin-top: var(--space-5);
    text-align: center;
    font-size: var(--text-sm);
    color: var(--color-ink-mute);

    a {
      color: var(--color-accent);
      text-decoration: none;
      margin-left: 4px;
      &:hover {
        text-decoration: underline;
      }
    }
  }
}

/* ============ 响应式 ============ */
@media (max-width: 991px) {
  .page-login {
    &__brand {
      display: none;
    }
    &__main {
      flex: 1 1 100%;
      padding: var(--space-10) var(--space-6);
    }
  }
}
</style>
