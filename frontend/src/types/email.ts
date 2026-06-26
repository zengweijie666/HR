/**
 * 文件名: types/email.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 邮件类型，对应 API-Design.md 6.0
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
}
