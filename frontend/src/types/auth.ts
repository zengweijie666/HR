/**
 * 文件名: types/auth.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 认证类型，对应 API-Design.md 一
 */
export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user?: UserInfo
}

export interface UserInfo {
  user_id: string
  username: string
  role: string
  email?: string
  name?: string
}
