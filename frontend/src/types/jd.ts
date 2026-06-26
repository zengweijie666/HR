/**
 * 文件名: types/jd.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: JD 匹配类型，对应 API-Design.md 7.0
 */
import type { CandidateCard } from './candidate'

export interface JdInfo {
  title: string
  skills: string[]
  work_years_min: number
  salary_max: number
}

export interface JdMatchCandidate extends CandidateCard {
  match_score: number
  reason: string
}

export interface JdMatchResult {
  jd: JdInfo
  candidates: JdMatchCandidate[]
}
