/**
 * 文件名: types/interview.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 面试类型，对应 API-Design.md 8.0
 */
export interface InterviewQuestion {
  question: string
  category: string
}

export interface InterviewNoteRequest {
  resume_id: string
  interviewer: string
  rating: number
  result: string
  content: string
}

export interface InterviewNoteItem {
  note_id: string
  resume_id: string
  interviewer: string
  rating: number
  result: string
  content: string
  created_at: string
}
