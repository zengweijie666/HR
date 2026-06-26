/**
 * 文件名: types/api.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 通用 API 类型，对应 API-Design.md 0.4
 */

/** 统一响应格式 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
  trace_id: string
}

/** 分页查询 */
export interface PageQuery {
  page: number
  page_size: number
}

/** 分页结果 */
export interface PageResult<T = unknown> {
  list: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
