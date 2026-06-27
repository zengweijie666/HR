<!--
  文件名: components/email/SendEmailDialog.vue
  创建时间: 2026-06-27
  作者: TalentSense Team
  功能描述: 发送邮件对话框（从简历详情等场景触发）
    - 通过 open(payload) 方法打开，payload 可预填变量
    - 支持模板模式（变量提取+预览）/ 自定义模式
    - 提交后调 sendMail API
-->
<template>
  <el-dialog
    v-model="visible"
    title="发送邮件"
    width="720px"
    :close-on-click-modal="false"
    align-center
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      class="send-dialog__form"
    >
      <el-form-item label="收件人邮箱" prop="to_email">
        <el-input
          v-model="form.to_email"
          placeholder="example@domain.com"
          :prefix-icon="Message"
        />
      </el-form-item>

      <el-form-item label="发送方式" prop="mode">
        <el-radio-group v-model="form.mode">
          <el-radio value="template">使用模板</el-radio>
          <el-radio value="custom">自定义内容</el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- 模板模式 -->
      <template v-if="form.mode === 'template'">
        <el-form-item label="选择模板" prop="template_id">
          <el-select
            v-model="form.template_id"
            placeholder="请选择模板"
            style="width: 100%"
            @change="handleTemplateChange"
          >
            <el-option
              v-for="t in templates"
              :key="t.template_id"
              :label="`${t.name}（${categoryLabel(t.category)}）`"
              :value="t.template_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item v-if="selectedTemplate" label="主题预览">
          <el-input :model-value="renderedSubject" readonly />
        </el-form-item>

        <el-form-item v-if="selectedTemplate && templateVariables.length" label="变量填写">
          <div class="send-dialog__vars">
            <div v-for="v in templateVariables" :key="v" class="send-dialog__var-item">
              <span class="send-dialog__var-label mono">{{ formatVarLabel(v) }}</span>
              <el-input v-model="form.variables[v]" placeholder="变量值" />
            </div>
          </div>
        </el-form-item>

        <el-form-item v-if="selectedTemplate" label="正文预览">
          <div class="send-dialog__preview" v-html="renderedBody" />
        </el-form-item>
      </template>

      <!-- 自定义模式 -->
      <template v-else>
        <el-form-item label="主题" prop="custom_subject">
          <el-input v-model="form.custom_subject" placeholder="邮件主题" />
        </el-form-item>
        <el-form-item label="正文（HTML）" prop="custom_body">
          <el-input
            v-model="form.custom_body"
            type="textarea"
            :rows="8"
            placeholder="<html><body><p>邮件正文...</p></body></html>"
          />
        </el-form-item>
      </template>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        type="primary"
        :loading="sending"
        :disabled="!canSend"
        @click="handleSubmit"
      >
        发送
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * SendEmailDialog 发送邮件对话框
 * 通过 open(prefill) 方法打开，prefill 可预填变量（如 candidate_name）
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Message } from '@element-plus/icons-vue'
import { listTemplates, sendMail } from '@/api/email'
import type { TemplateItem, TemplateCategory } from '@/types/email'
import { TEMPLATE_CATEGORY_LABEL } from '@/types/email'

interface OpenPayload {
  /** 预填的模板变量，例如 { candidate_name: '张三', position: 'Java 工程师' } */
  variables?: Record<string, string>
  /** 预填收件人邮箱 */
  to_email?: string
  /** 默认选中的模板 ID */
  template_id?: string
}

const visible = ref<boolean>(false)
const sending = ref<boolean>(false)
const formRef = ref<FormInstance>()

const templates = ref<TemplateItem[]>([])

const form = reactive({
  to_email: '',
  mode: 'template' as 'template' | 'custom',
  template_id: '',
  custom_subject: '',
  custom_body: '',
  variables: {} as Record<string, string>,
})

const rules: FormRules = {
  to_email: [
    { required: true, message: '请输入收件人邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  template_id: [
    {
      validator: (_rule, value, callback) => {
        if (form.mode === 'template' && !value) {
          callback(new Error('请选择模板'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
  custom_subject: [
    {
      validator: (_rule, value, callback) => {
        if (form.mode === 'custom' && !value?.trim()) {
          callback(new Error('请输入邮件主题'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  custom_body: [
    {
      validator: (_rule, value, callback) => {
        if (form.mode === 'custom' && !value?.trim()) {
          callback(new Error('请输入邮件正文'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

/** 当前选中的模板 */
const selectedTemplate = computed<TemplateItem | undefined>(() => {
  return templates.value.find(t => t.template_id === form.template_id)
})

/** 模板变量提取 */
const templateVariables = computed<string[]>(() => {
  const tpl = selectedTemplate.value
  if (!tpl) return []
  const re = /\{\{\s*([\w]+)\s*\}\}/g
  const set = new Set<string>()
  let m: RegExpExecArray | null
  while ((m = re.exec(tpl.subject + tpl.body)) !== null) {
    set.add(m[1])
  }
  return Array.from(set)
})

function renderText(text: string): string {
  return text.replace(/\{\{\s*([\w]+)\s*\}\}/g, (_, k: string) => form.variables[k] ?? `{{ ${k} }}`)
}

const renderedSubject = computed(() => {
  return selectedTemplate.value ? renderText(selectedTemplate.value.subject) : ''
})

const renderedBody = computed(() => {
  return selectedTemplate.value ? renderText(selectedTemplate.value.body) : ''
})

const canSend = computed(() => {
  if (!form.to_email.trim()) return false
  if (form.mode === 'template') return !!form.template_id
  return !!(form.custom_subject.trim() && form.custom_body.trim())
})

/** 分类标签 */
function categoryLabel(c: string): string {
  return TEMPLATE_CATEGORY_LABEL[c as TemplateCategory] ?? c
}

/** 格式化变量标签 */
function formatVarLabel(v: string): string {
  return `{{ ${v} }}`
}

/** 模板切换：保留已填写的变量值 */
function handleTemplateChange(): void {
  // 不清空已填写的 variables，让用户切换模板时已填的值可复用
}

/**
 * 打开对话框
 * @param payload 预填项（变量、收件人、默认模板）
 */
function open(payload?: OpenPayload): void {
  form.to_email = payload?.to_email ?? ''
  form.mode = 'template'
  form.template_id = payload?.template_id ?? ''
  form.custom_subject = ''
  form.custom_body = ''
  form.variables = { ...(payload?.variables ?? {}) }
  visible.value = true
  void loadTemplates()
}

/** 加载模板列表 */
async function loadTemplates(): Promise<void> {
  try {
    templates.value = await listTemplates()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载模板失败')
  }
}

/** 提交发送 */
async function handleSubmit(): Promise<void> {
  if (!formRef.value) return
  try { await formRef.value.validate() } catch { return }
  sending.value = true
  try {
    const payload = {
      to_email: form.to_email.trim(),
      ...(form.mode === 'template'
        ? { template_id: form.template_id, variables: form.variables }
        : { custom_subject: form.custom_subject.trim(), custom_body: form.custom_body.trim() }),
    }
    await sendMail(payload)
    ElMessage.success('邮件发送成功')
    visible.value = false
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '发送失败')
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  void loadTemplates()
})

defineExpose({ open })
</script>

<style scoped lang="scss">
.send-dialog {
  &__form {
    max-height: 60vh;
    overflow-y: auto;
    padding-right: var(--space-2);
  }

  &__vars {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  &__var-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  &__var-label {
    flex-shrink: 0;
    width: 140px;
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
    background-color: var(--color-bg-overlay);
    padding: 4px 8px;
    border-radius: var(--radius-sm);
  }

  &__preview {
    width: 100%;
    min-height: 100px;
    max-height: 200px;
    overflow-y: auto;
    padding: var(--space-4);
    background-color: var(--color-bg-overlay);
    border: 1px solid var(--color-line);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    line-height: 1.6;
    color: var(--color-ink);

    :deep(h1), :deep(h2), :deep(h3) {
      margin: 0 0 var(--space-2);
    }
    :deep(p) {
      margin: 0 0 var(--space-2);
    }
    :deep(ul) {
      margin: 0 0 var(--space-2);
      padding-left: var(--space-5);
    }
  }
}
</style>
