/**
 * 文件名: types/candidate.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 候选人类型，对应 API-Design.md 5.0
 */
export interface CandidateCard {
  candidate_id: string
  resume_id: string
  name: string
  work_years: number
  education: string
  skills: string[]
  expected_salary: { min: number; max: number }
  score: number
  reason: string
  tags: string[]
  is_favorite: boolean
}

export interface ExportRequest {
  candidate_ids: string[]
  columns: string[]
}

export interface CompareResult {
  candidates: CandidateCard[]
  dimensions: string[]
}
