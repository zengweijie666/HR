/**
 * 文件名: api/user.ts
 * 创建时间: 2026-06-27
 * 作者: TalentSense Team
 * 功能描述: 用户管理 API（全部 admin only）
 */
import request from './request'
import type { UserListResponse, UserListItem, CreateUserPayload, ListUsersParams, UserStatus } from '@/types/user'

/**
 * 用户列表（admin only）
 * @param params 分页/筛选参数
 * @returns UserListResponse
 */
export function listUsers(params: ListUsersParams): Promise<UserListResponse> {
  return request.get('/users', { params }) as unknown as Promise<UserListResponse>
}

/**
 * 创建账号（admin only，status=approved）
 * @param data 用户信息
 * @returns 新建用户
 */
export function createUser(data: CreateUserPayload): Promise<UserListItem> {
  return request.post('/users', data) as unknown as Promise<UserListItem>
}

/**
 * 审批通过（pending → approved）
 * @param userId 用户 ID
 */
export function approveUser(userId: string): Promise<void> {
  return request.put(`/users/${userId}/approve`) as unknown as Promise<void>
}

/**
 * 拒绝申请（直接删除记录）
 * @param userId 用户 ID
 */
export function rejectUser(userId: string): Promise<void> {
  return request.put(`/users/${userId}/reject`) as unknown as Promise<void>
}

/**
 * 启用/禁用账号
 * @param userId 用户 ID
 * @param status approved / disabled
 */
export function updateUserStatus(userId: string, status: UserStatus): Promise<void> {
  return request.put(`/users/${userId}/status`, { status }) as unknown as Promise<void>
}

/**
 * 重置密码（admin only）
 * @param userId 用户 ID
 * @param newPassword 新密码
 */
export function resetUserPassword(userId: string, newPassword: string): Promise<void> {
  return request.put(`/users/${userId}/password`, { new_password: newPassword }) as unknown as Promise<void>
}

/**
 * 删除账号（admin only，不能删自己）
 * @param userId 用户 ID
 */
export function deleteUser(userId: string): Promise<void> {
  return request.delete(`/users/${userId}`) as unknown as Promise<void>
}
