/**
 * 文件名: api/search.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 语义搜索接口
 */
import request from './request'
import type { CandidateCard } from '@/types/candidate'

/** 搜索请求参数 */
export interface SearchRequest {
  query: string
  filters?: Record<string, unknown>
  top_k?: number
}

/**
 * 候选人语义搜索
 * @param params 搜索请求 { query, filters, top_k }
 * @returns 候选人卡片数组
 */
export function search(params: SearchRequest): Promise<CandidateCard[]> {
  // 检索+精排+20个候选人 LLM 并发评分耗时较长，单独放宽到 2 分钟
  // 全局 30s timeout 会误杀该接口，此处覆盖
  return request.post('/search', params, { timeout: 120000 }) as unknown as Promise<CandidateCard[]>
}
