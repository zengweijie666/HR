/**
 * 文件名: api/candidate.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 候选人相关接口（导出/相似/对比）
 */
import request from './request'
import type { CandidateCard, CompareResult } from '@/types/candidate'

/** 导出请求参数 */
export interface ExportParams {
  candidate_ids: string[]
  columns: string[]
}

/**
 * 导出候选人 Excel
 * @param params 导出参数 { candidate_ids, columns }
 * @returns Blob 文件流
 */
export function exportExcel(params: ExportParams): Promise<Blob> {
  return request.post('/candidates/export', params, {
    responseType: 'blob',
  }) as unknown as Promise<Blob>
}

/**
 * 获取相似候选人
 * @param resumeId 简历 ID
 * @param topK 返回数量
 */
export function getSimilar(resumeId: string, topK: number): Promise<CandidateCard[]> {
  return request.get(`/resumes/${resumeId}/similar`, {
    params: { top_k: topK },
  }) as unknown as Promise<CandidateCard[]>
}

/**
 * 多候选人对比
 * @param candidateIds 候选人 ID 数组
 */
export function compare(candidateIds: string[]): Promise<CompareResult> {
  return request.post('/candidates/compare', { candidate_ids: candidateIds }) as unknown as Promise<CompareResult>
}
