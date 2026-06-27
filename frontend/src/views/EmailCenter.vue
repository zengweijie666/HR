<!--
  文件名: views/EmailCenter.vue
  创建时间: 2026-06-27
  作者: TalentSense Team
  功能描述: 邮件中心页
    - 顶部页头：eyebrow + 大标题 + 副文案
    - Tab 1 发送邮件：模板/自定义切换 + 收件人 + 变量 + 发送
    - Tab 2 模板管理（admin only）：列表/新建/编辑/删除，预置模板只读
-->
<template>
  <div class="page-email">
    <!-- 页头 -->
    <header class="page-email__head">
      <span class="eyebrow">EMAIL CENTER</span>
      <h1 class="page-email__title decor-line">邮件中心</h1>
      <p class="page-email__subtitle">
        基于模板或自定义内容向候选人/招聘方发送邮件通知
      </p>
    </header>

    <el-tabs v-model="activeTab" class="page-email__tabs">
      <!-- ============ Tab 1: 发送邮件 ============ -->
      <el-tab-pane label="发送邮件" name="send">
        <section class="send-card">
          <LoadingOverlay :visible="sending" />

          <el-form
            ref="sendFormRef"
            :model="sendForm"
            :rules="sendRules"
            label-position="top"
            class="send-card__form"
          >
            <el-form-item label="收件人邮箱" prop="to_email">
              <el-input
                v-model="sendForm.to_email"
                placeholder="example@domain.com"
                :prefix-icon="Message"
              />
            </el-form-item>

            <el-form-item label="发送方式" prop="mode">
              <el-radio-group v-model="sendForm.mode">
                <el-radio value="template">使用模板</el-radio>
                <el-radio value="custom">自定义内容</el-radio>
              </el-radio-group>
            </el-form-item>

            <!-- 模板模式 -->
            <template v-if="sendForm.mode === 'template'">
              <el-form-item label="选择模板" prop="template_id">
                <el-select
                  v-model="sendForm.template_id"
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

              <!-- 模板预览 -->
              <el-form-item v-if="selectedTemplate" label="主题预览">
                <el-input :model-value="renderedSubject" readonly />
              </el-form-item>

              <el-form-item v-if="selectedTemplate" label="变量填写">
                <div class="send-card__vars">
                  <div v-for="v in templateVariables" :key="v" class="send-card__var-item">
                    <span class="send-card__var-label mono">{{ formatVarLabel(v) }}</span>
                    <el-input v-model="sendForm.variables[v]" placeholder="变量值" />
                  </div>
                  <EmptyState v-if="templateVariables.length === 0" text="此模板无需变量" />
                </div>
              </el-form-item>

              <el-form-item v-if="selectedTemplate" label="正文预览">
                <div class="send-card__preview" v-html="renderedBody" />
              </el-form-item>
            </template>

            <!-- 自定义模式 -->
            <template v-else>
              <el-form-item label="主题" prop="custom_subject">
                <el-input v-model="sendForm.custom_subject" placeholder="邮件主题" />
              </el-form-item>
              <el-form-item label="正文（HTML）" prop="custom_body">
                <el-input
                  v-model="sendForm.custom_body"
                  type="textarea"
                  :rows="10"
                  placeholder="<html><body><p>邮件正文...</p></body></html>"
                />
              </el-form-item>
            </template>

            <el-form-item>
              <el-button
                type="primary"
                :loading="sending"
                :disabled="!canSend"
                @click="handleSend"
              >
                <el-icon><Promotion /></el-icon>
                发送邮件
              </el-button>
              <el-button @click="resetSendForm">重置</el-button>
            </el-form-item>
          </el-form>
        </section>
      </el-tab-pane>

      <!-- ============ Tab 2: 模板管理（admin only） ============ -->
      <el-tab-pane v-if="isAdmin" label="模板管理" name="templates">
        <section class="templates-card">
          <LoadingOverlay :visible="templatesLoading" />

          <div class="templates-card__toolbar">
            <div class="templates-card__filters">
              <el-select
                v-model="templateFilter"
                placeholder="全部分类"
                clearable
                style="width: 160px"
                @change="loadTemplates"
              >
                <el-option
                  v-for="(label, key) in categoryOptions"
                  :key="key"
                  :label="label"
                  :value="key"
                />
              </el-select>
            </div>
            <el-button type="primary" @click="openCreate">
              <el-icon><Plus /></el-icon>
              新建模板
            </el-button>
          </div>

          <el-table :data="templates" class="templates-card__table">
            <el-table-column prop="name" label="模板名称" min-width="160" />
            <el-table-column label="分类" width="120">
              <template #default="{ row }">
                <el-tag size="small" :type="categoryTagType(row.category)">
                  {{ categoryLabel(row.category) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="subject" label="主题" min-width="240" show-overflow-tooltip />
            <el-table-column label="类型" width="90">
              <template #default="{ row }">
                <el-tag v-if="row.is_builtin" type="info" size="small">内置</el-tag>
                <el-tag v-else type="success" size="small">自定义</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" width="180" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="openEdit(row)">编辑</el-button>
                <el-button
                  size="small"
                  type="danger"
                  :disabled="row.is_builtin"
                  @click="handleDelete(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>
      </el-tab-pane>
    </el-tabs>

    <!-- ============ 创建/编辑模板对话框 ============ -->
    <el-dialog
      v-model="tplDialogVisible"
      :title="tplEditMode === 'create' ? '新建模板' : '编辑模板'"
      width="680px"
    >
      <el-form
        ref="tplFormRef"
        :model="tplForm"
        :rules="tplRules"
        label-position="top"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="tplForm.name" placeholder="如：面试邀请" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="tplForm.category" placeholder="请选择分类" style="width: 100%">
            <el-option
              v-for="(label, key) in categoryOptions"
              :key="key"
              :label="label"
              :value="key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="主题（支持变量）" prop="subject">
          <el-input v-model="tplForm.subject" placeholder="如：【{{ company }}】面试邀请 - {{ position }}" />
        </el-form-item>
        <el-form-item label="正文 HTML（支持变量）" prop="body">
          <el-input
            v-model="tplForm.body"
            type="textarea"
            :rows="10"
            placeholder="<html><body><p>正文...</p></body></html>"
          />
        </el-form-item>
        <div class="tpl-dialog__hint">
          可用变量语法：<code class="mono">{{ varSyntaxExample }}</code>，常见变量：candidate_name / company / position / salary / interview_time
        </div>
      </el-form>
      <template #footer>
        <el-button @click="tplDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="tplSaving" @click="handleSaveTemplate">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * EmailCenter 邮件中心页
 * - Tab1 发送邮件：模板模式 / 自定义模式
 * - Tab2 模板管理（admin only）：CRUD，预置模板只读
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Message, Promotion, Plus } from '@element-plus/icons-vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useAuthStore } from '@/stores/auth'
import {
  listTemplates, createTemplate, updateTemplate, deleteTemplate, sendMail,
} from '@/api/email'
import type {
  TemplateItem, TemplateCategory, TemplateCreatePayload,
} from '@/types/email'
import { TEMPLATE_CATEGORY_LABEL } from '@/types/email'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const activeTab = ref<'send' | 'templates'>('send')

/* ============ 模板列表 ============ */
const templates = ref<TemplateItem[]>([])
const templatesLoading = ref<boolean>(false)
const templateFilter = ref<string>('')

/** 加载模板列表 */
async function loadTemplates(): Promise<void> {
  templatesLoading.value = true
  try {
    templates.value = await listTemplates(templateFilter.value || undefined)
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载模板失败')
  } finally {
    templatesLoading.value = false
  }
}

/** 分类标签文本 */
function categoryLabel(c: string): string {
  return TEMPLATE_CATEGORY_LABEL[c as TemplateCategory] ?? c
}

/** 格式化变量标签：v -> {{ v }} */
function formatVarLabel(v: string): string {
  return `{{ ${v} }}`
}

/** 变量语法示例（避免模板里嵌套 {{ }} 解析错误） */
const varSyntaxExample = '{{ variable }}'

/** 分类标签颜色 */
function categoryTagType(c: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    interview: 'primary',
    offer: 'success',
    reject: 'danger',
    progress: 'warning',
    custom: 'info',
  }
  return map[c] ?? 'info'
}

const categoryOptions = TEMPLATE_CATEGORY_LABEL

/* ============ 发送邮件 ============ */
const sendFormRef = ref<FormInstance>()
const sending = ref<boolean>(false)

const sendForm = reactive({
  to_email: '',
  mode: 'template' as 'template' | 'custom',
  template_id: '',
  custom_subject: '',
  custom_body: '',
  variables: {} as Record<string, string>,
})

const sendRules: FormRules = {
  to_email: [
    { required: true, message: '请输入收件人邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  template_id: [
    {
      validator: (_rule, value, callback) => {
        if (sendForm.mode === 'template' && !value) {
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
        if (sendForm.mode === 'custom' && !value?.trim()) {
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
        if (sendForm.mode === 'custom' && !value?.trim()) {
          callback(new Error('请输入邮件正文'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

/** 当前选中的模板对象 */
const selectedTemplate = computed<TemplateItem | undefined>(() => {
  return templates.value.find(t => t.template_id === sendForm.template_id)
})

/** 从模板正文/主题提取变量名（{{ var }}） */
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

/** 用 variables 渲染字符串 */
function renderText(text: string): string {
  return text.replace(/\{\{\s*([\w]+)\s*\}\}/g, (_, k: string) => sendForm.variables[k] ?? `{{ ${k} }}`)
}

const renderedSubject = computed(() => {
  return selectedTemplate.value ? renderText(selectedTemplate.value.subject) : ''
})

const renderedBody = computed(() => {
  return selectedTemplate.value ? renderText(selectedTemplate.value.body) : ''
})

/** 是否可发送 */
const canSend = computed(() => {
  if (!sendForm.to_email.trim()) return false
  if (sendForm.mode === 'template') return !!sendForm.template_id
  return !!(sendForm.custom_subject.trim() && sendForm.custom_body.trim())
})

/** 模板切换时重置变量 */
function handleTemplateChange(): void {
  sendForm.variables = {}
}

/** 发送邮件 */
async function handleSend(): Promise<void> {
  if (!sendFormRef.value) return
  try { await sendFormRef.value.validate() } catch { return }
  sending.value = true
  try {
    const payload = {
      to_email: sendForm.to_email.trim(),
      ...(sendForm.mode === 'template'
        ? { template_id: sendForm.template_id, variables: sendForm.variables }
        : { custom_subject: sendForm.custom_subject.trim(), custom_body: sendForm.custom_body.trim() }),
    }
    const result = await sendMail(payload)
    if (result.status === 'error') {
      ElMessage.error(result.message || '发送失败，请检查 SMTP 配置')
      return
    }
    ElMessage.success('邮件发送成功')
    resetSendForm()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '发送失败')
  } finally {
    sending.value = false
  }
}

/** 重置发送表单 */
function resetSendForm(): void {
  sendForm.to_email = ''
  sendForm.template_id = ''
  sendForm.custom_subject = ''
  sendForm.custom_body = ''
  sendForm.variables = {}
}

/* ============ 模板 CRUD ============ */
const tplDialogVisible = ref<boolean>(false)
const tplEditMode = ref<'create' | 'edit'>('create')
const tplEditingId = ref<string>('')
const tplSaving = ref<boolean>(false)
const tplFormRef = ref<FormInstance>()

const tplForm = reactive<TemplateCreatePayload>({
  name: '',
  subject: '',
  body: '',
  category: 'custom',
})

const tplRules: FormRules = {
  name: [{ required: true, min: 1, max: 50, message: '1-50 字符', trigger: 'blur' }],
  subject: [{ required: true, min: 1, max: 200, message: '1-200 字符', trigger: 'blur' }],
  body: [{ required: true, message: '请输入正文', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

/** 打开新建对话框 */
function openCreate(): void {
  tplEditMode.value = 'create'
  tplEditingId.value = ''
  tplForm.name = ''
  tplForm.subject = ''
  tplForm.body = ''
  tplForm.category = 'custom'
  tplDialogVisible.value = true
}

/** 打开编辑对话框（预置模板也可查看，但 is_builtin 字段不允许编辑） */
function openEdit(row: TemplateItem): void {
  if (row.is_builtin) {
    ElMessage.warning('预置模板不可编辑')
    return
  }
  tplEditMode.value = 'edit'
  tplEditingId.value = row.template_id
  tplForm.name = row.name
  tplForm.subject = row.subject
  tplForm.body = row.body
  tplForm.category = row.category
  tplDialogVisible.value = true
}

/** 保存模板（新建/编辑） */
async function handleSaveTemplate(): Promise<void> {
  if (!tplFormRef.value) return
  try { await tplFormRef.value.validate() } catch { return }
  tplSaving.value = true
  try {
    const data: TemplateCreatePayload = {
      name: tplForm.name.trim(),
      subject: tplForm.subject.trim(),
      body: tplForm.body,
      category: tplForm.category,
    }
    if (tplEditMode.value === 'create') {
      await createTemplate(data)
      ElMessage.success('模板已创建')
    } else {
      await updateTemplate(tplEditingId.value, data)
      ElMessage.success('模板已更新')
    }
    tplDialogVisible.value = false
    await loadTemplates()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    tplSaving.value = false
  }
}

/** 删除模板 */
async function handleDelete(row: TemplateItem): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认删除模板「${row.name}」？`, '删除', { type: 'warning' })
    await deleteTemplate(row.template_id)
    ElMessage.success('已删除')
    await loadTemplates()
  } catch { /* cancel */ }
}

onMounted(() => {
  void loadTemplates()
})
</script>

<style scoped lang="scss">
.page-email {
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

  &__tabs {
    :deep(.el-tabs__header) {
      margin-bottom: var(--space-5);
    }
    :deep(.el-tabs__item) {
      font-size: var(--text-md);
      font-weight: 500;
    }
  }
}

/* ============ 发送卡片 ============ */
.send-card {
  position: relative;
  max-width: 880px;
  padding: var(--space-6) var(--space-8);
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);

  &__form {
    max-width: 720px;

    :deep(.el-form-item__label) {
      font-size: var(--text-sm);
      font-weight: 500;
      color: var(--color-ink-soft);
      padding-bottom: 4px;
    }
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
    min-height: 120px;
    padding: var(--space-4);
    background-color: var(--color-bg-overlay);
    border: 1px solid var(--color-line);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    line-height: 1.6;
    color: var(--color-ink);
    overflow-x: auto;

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

/* ============ 模板管理卡片 ============ */
.templates-card {
  position: relative;
  padding: var(--space-4) var(--space-6);
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);

  &__toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-4);
  }

  &__table {
    width: 100%;
  }
}

/* ============ 模板对话框 ============ */
.tpl-dialog__hint {
  margin-top: var(--space-2);
  padding: var(--space-3);
  background-color: var(--color-bg-overlay);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--color-ink-mute);
  line-height: 1.6;

  code {
    background-color: var(--color-bg-card);
    padding: 1px 6px;
    border-radius: 4px;
    color: var(--color-accent);
    font-weight: 500;
  }
}
</style>
