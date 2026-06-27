/**
 * 文件名: api/auth.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 认证相关接口
 */
import request from './request'
import type { LoginRequest, TokenResponse, UserInfo, RegisterRequest, ChangePasswordRequest } from '@/types/auth'

/**
 * 登录
 * @param payload 用户名密码
 * @returns TokenResponse
 */
export function login(payload: LoginRequest): Promise<TokenResponse> {
  return request.post('/auth/login', payload) as unknown as Promise<TokenResponse>
}

/**
 * HR 自助注册申请（status=pending，需管理员审批）
 * @param data 注册信息
 * @returns { user_id, username, status }
 */
export function register(data: RegisterRequest): Promise<{ user_id: string; username: string; status: string }> {
  return request.post('/auth/register', data) as unknown as Promise<{ user_id: string; username: string; status: string }>
}

/**
 * 刷新 token
 * @param refreshToken 刷新令牌
 * @returns 新的 TokenResponse
 */
export function refresh(refreshToken: string): Promise<TokenResponse> {
  return request.post('/auth/refresh', { refresh_token: refreshToken }) as unknown as Promise<TokenResponse>
}

/**
 * 获取当前登录用户信息
 * @returns UserInfo
 */
export function getMe(): Promise<UserInfo> {
  return request.get('/auth/me') as unknown as Promise<UserInfo>
}

/**
 * 退出登录
 */
export function logout(): Promise<void> {
  return request.post('/auth/logout') as unknown as Promise<void>
}

/**
 * 修改自己密码
 * @param data 旧密码 + 新密码
 */
export function changePassword(data: ChangePasswordRequest): Promise<void> {
  return request.put('/auth/password', data) as unknown as Promise<void>
}
