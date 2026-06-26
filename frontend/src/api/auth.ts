/**
 * 文件名: api/auth.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 认证相关接口
 */
import request from './request'
import type { LoginRequest, TokenResponse, UserInfo } from '@/types/auth'

/**
 * 登录
 * @param payload 用户名密码
 * @returns TokenResponse
 */
export function login(payload: LoginRequest): Promise<TokenResponse> {
  return request.post('/auth/login', payload) as unknown as Promise<TokenResponse>
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
