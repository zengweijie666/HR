/**
 * 文件名: api/dashboard.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 数据看板接口
 */
import request from './request'
import type { DashboardStats } from '@/types/dashboard'

/**
 * 获取看板统计数据
 */
export function getStats(): Promise<DashboardStats> {
  return request.get('/dashboard/stats') as unknown as Promise<DashboardStats>
}
