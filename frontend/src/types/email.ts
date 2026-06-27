/**
 * 文件名: types/email.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 邮件类型 + 邮件模板类型，对应 API-Design.md 六、Email
 */
export interface EmailRequest {
  to_email: string
  candidate_ids: string[]
  job_title: string
}

export interface EmailConfig {
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_password?: string
  use_ssl?: boolean
  sender_name?: string
  signature?: string
}

/** 模板分类 */
export type TemplateCategory = 'interview' | 'offer' | 'reject' | 'progress' | 'custom'

/** 模板列表项 */
export interface TemplateItem {
  template_id: string
  name: string
  subject: string
  body: string
  category: TemplateCategory
  is_builtin: boolean
  created_at: string
  updated_at: string
}

/** 创建模板请求 */
export interface TemplateCreatePayload {
  name: string
  subject: string
  body: string
  category: TemplateCategory
}

/** 更新模板请求（部分字段） */
export interface TemplateUpdatePayload {
  name?: string
  subject?: string
  body?: string
  category?: TemplateCategory
}

/** 发送邮件请求（template_id 或 custom 二选一） */
export interface SendMailPayload {
  to_email: string
  template_id?: string
  custom_subject?: string
  custom_body?: string
  variables?: Record<string, string>
}

/** 发送邮件响应 */
export interface SendMailResult {
  status: string
  message_id?: string
}

/** 发送测试邮件请求 */
export interface SendTestPayload {
  to_email: string
}

/** 模板分类标签映射 */
export const TEMPLATE_CATEGORY_LABEL: Record<TemplateCategory, string> = {
  interview: '面试邀请',
  offer: 'Offer 通知',
  reject: '拒绝通知',
  progress: '进度通知',
  custom: '自定义',
}
