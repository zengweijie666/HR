/**
 * 文件名: types/user.ts
 * 创建时间: 2026-06-27
 * 作者: TalentSense Team
 * 功能描述: 用户管理类型定义
 */
import type { UserRole, UserStatus } from './auth'

export interface UserListItem {
  user_id: string
  username: string
  email: string | null
  name: string | null
  role: UserRole
  status: UserStatus
  created_at: string
  updated_at: string
}

export interface UserListResponse {
  list: UserListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface CreateUserPayload {
  username: string
  password: string
  role: UserRole
  email?: string
  name?: string
}

export interface ListUsersParams {
  page?: number
  page_size?: number
  status?: UserStatus
  role?: UserRole
  keyword?: string
}
