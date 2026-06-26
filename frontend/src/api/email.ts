/**
 * 文件名: api/email.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 邮件相关接口（推荐/配置）
 */
import request from './request'
import type { EmailRequest, EmailConfig } from '@/types/email'

/** 发送推荐邮件响应 */
export interface SendRecommendationResult {
  status: string
  sent_count: number
}

/**
 * 发送推荐邮件
 * @param data 邮件请求体
 */
export function sendRecommendation(data: EmailRequest): Promise<SendRecommendationResult> {
  return request.post('/email/recommend', data) as unknown as Promise<SendRecommendationResult>
}

/**
 * 获取邮件配置
 */
export function getConfig(): Promise<EmailConfig> {
  return request.get('/email/config') as unknown as Promise<EmailConfig>
}

/**
 * 更新邮件配置
 * @param data 配置项（部分字段）
 */
export function updateConfig(data: Partial<EmailConfig>): Promise<EmailConfig> {
  return request.put('/email/config', data) as unknown as Promise<EmailConfig>
}
