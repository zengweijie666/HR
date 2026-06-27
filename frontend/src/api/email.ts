/**
 * 文件名: api/email.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 邮件相关接口（发送 / 测试 / SMTP 配置 / 模板 CRUD）
 */
import request from './request'
import type {
  EmailConfig,
  SendMailPayload,
  SendMailResult,
  SendTestPayload,
  TemplateCreatePayload,
  TemplateItem,
  TemplateUpdatePayload,
} from '@/types/email'

/**
 * 获取邮件配置（脱敏，admin only）
 */
export function getConfig(): Promise<EmailConfig> {
  return request.get('/email/config') as unknown as Promise<EmailConfig>
}

/**
 * 更新邮件配置（admin only）
 * @param data 配置项（部分字段）
 */
export function updateConfig(data: Partial<EmailConfig>): Promise<EmailConfig> {
  return request.put('/email/config', data) as unknown as Promise<EmailConfig>
}

/**
 * 发送邮件（模板或自定义）
 * @param data SendMailPayload（template_id 与 custom_* 二选一）
 */
export function sendMail(data: SendMailPayload): Promise<SendMailResult> {
  return request.post('/email/send', data) as unknown as Promise<SendMailResult>
}

/**
 * 发送测试邮件（admin only）
 * @param data SendTestPayload（仅 to_email）
 */
export function sendTestMail(data: SendTestPayload): Promise<SendMailResult> {
  return request.post('/email/send-test', data) as unknown as Promise<SendMailResult>
}

/**
 * 模板列表（登录用户可查，admin 才能增删改）
 * @param category 可选分类筛选
 * @returns 模板数组（后端返回 {list, total}，此处剥离出 list）
 */
export async function listTemplates(category?: string): Promise<TemplateItem[]> {
  const res = await request.get('/email/templates', { params: category ? { category } : {} }) as unknown as { list: TemplateItem[]; total: number }
  return res?.list ?? []
}

/**
 * 创建模板（admin only）
 * @param data TemplateCreatePayload
 */
export function createTemplate(data: TemplateCreatePayload): Promise<TemplateItem> {
  return request.post('/email/templates', data) as unknown as Promise<TemplateItem>
}

/**
 * 更新模板（admin only，预置模板不可改）
 * @param templateId 模板 ID
 * @param data TemplateUpdatePayload（部分字段）
 */
export function updateTemplate(templateId: string, data: TemplateUpdatePayload): Promise<TemplateItem> {
  return request.put(`/email/templates/${templateId}`, data) as unknown as Promise<TemplateItem>
}

/**
 * 删除模板（admin only，预置模板不可删）
 * @param templateId 模板 ID
 */
export function deleteTemplate(templateId: string): Promise<void> {
  return request.delete(`/email/templates/${templateId}`) as unknown as Promise<void>
}
