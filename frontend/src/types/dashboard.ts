/**
 * 文件名: types/dashboard.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 看板类型，对应 API-Design.md 9.0
 */
export interface DashboardStats {
  total_resumes: number
  favorite_count: number
  parsing_count: number
  total_sessions: number
  top_skills: { _id: string; count: number }[]
  education_distribution: { _id: string; count: number }[]
  salary_distribution: { _id: string | number; count: number }[]
  recruitment_funnel: { stage: string; count: number }[]
  resume_trend: { date: string; count: number }[]
  work_years_distribution: { range: string; count: number }[]
  interview_result_distribution: { result: string; count: number }[]
}
