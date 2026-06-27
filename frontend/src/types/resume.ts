/**
 * 文件名: types/resume.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 简历类型，对应 API-Design.md 2.0 / 第十章
 */

export interface ResumeListItem {
  resume_id: string
  candidate_id: string
  name: string
  gender?: string
  age?: number
  education: string
  education_level: number
  work_years: number
  skills: string[]
  expected_salary: { min: number; max: number }
  tags: string[]
  is_favorite: boolean
  parse_status: 'pending' | 'parsing' | 'completed' | 'failed'
  location?: string
  created_at: string
  // RBAC 脱敏字段：admin 可见原始值，普通用户可见 masked
  phone?: string
  email?: string
  phone_masked?: string
  email_masked?: string
  summary?: string
}

export interface WorkExperience {
  company: string
  position: string
  start_date: string
  end_date: string
  description: string
}

export interface EducationDetail {
  school: string
  major: string
  degree: string
  start_date: string
  end_date: string
}

export interface ProjectItem {
  name: string
  role: string
  description: string
}

export interface InterviewNoteItem {
  note_id: string
  interviewer: string
  rating: number
  result: string
  content: string
  created_at: string
}

export interface ResumeDetail extends ResumeListItem {
  basic_info: {
    name: string
    phone_masked: string
    email_masked?: string
    gender?: string
    age?: number
    location?: string
  }
  work_experience: WorkExperience[]
  education_detail: EducationDetail[]
  projects?: ProjectItem[]
  summary: string
  file_info: { file_name: string; file_type: string; file_size?: number }
  parse_info: { parse_status: string; parse_time?: string }
  notes: string
  interview_notes?: InterviewNoteItem[]
  updated_at?: string
}

export interface UploadResponse {
  resume_id: string
  candidate_id: string
  file_name: string
  parse_status: string
  is_duplicate: boolean
  duplicate_with: string | null
}

export interface ResumeListQuery {
  page?: number
  page_size?: number
  keyword?: string
  tag?: string
  is_favorite?: boolean
  education_min?: number
  work_years_min?: number
  salary_min?: number
  salary_max?: number
  status?: string
  // 筛选和排序（新增）
  date_from?: string
  date_to?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}
