/**
 * 文件名: api/interview.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 面试相关接口（生成问题/笔记）
 */
import request from './request'
import type {
  InterviewQuestion,
  InterviewNoteRequest,
  InterviewNoteItem,
} from '@/types/interview'

/** 保存笔记响应 */
export interface SaveNoteResult {
  note_id: string
}

/**
 * 生成面试问题
 * @param resumeId 简历 ID
 * @param jobTitle 目标岗位
 * @param count 问题数量
 */
export function generateQuestions(
  resumeId: string,
  jobTitle: string,
  count: number,
): Promise<InterviewQuestion[]> {
  return request.post('/interview/questions', {
    resume_id: resumeId,
    job_title: jobTitle,
    count,
  }) as unknown as Promise<InterviewQuestion[]>
}

/**
 * 保存面试笔记
 * @param data 笔记请求体
 */
export function saveNote(data: InterviewNoteRequest): Promise<SaveNoteResult> {
  return request.post('/interview/notes', data) as unknown as Promise<SaveNoteResult>
}

/**
 * 获取简历的面试笔记列表
 * @param resumeId 简历 ID
 */
export function getNotes(resumeId: string): Promise<InterviewNoteItem[]> {
  return request.get('/interview/notes', {
    params: { resume_id: resumeId },
  }) as unknown as Promise<InterviewNoteItem[]>
}
