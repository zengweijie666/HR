/**
 * 文件名: types/auth.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 认证类型，对应 API-Design.md 一
 */
export type UserRole = 'admin' | 'hr'
export type UserStatus = 'approved' | 'pending' | 'disabled'

export interface LoginRequest {
  email: string
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
  role: UserRole
  status?: UserStatus
  email?: string
  name?: string
}

export interface RegisterRequest {
  username: string
  password: string
  email: string
  name: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}
