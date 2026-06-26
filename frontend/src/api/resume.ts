/**
 * 文件名: api/resume.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 简历相关接口
 */
import request from './request'
import type { PageResult } from '@/types/api'
import type {
  ResumeListItem,
  ResumeDetail,
  ResumeListQuery,
  UploadResponse,
} from '@/types/resume'

/** 预览地址响应 */
export interface PreviewUrlResult {
  preview_url: string
  file_type: string
  expires_in: number
}

/**
 * 上传简历
 * @param file 简历文件
 * @param overwrite 重复时是否覆盖
 * @returns UploadResponse
 */
export function uploadResume(file: File, overwrite = false): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('overwrite', String(overwrite))
  return request.post('/resumes/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    // 文件上传本身可能较慢（大文件 + 网络），单独放宽到 2 分钟
    // 解析由后端 BackgroundTasks 异步执行，不影响本请求返回
    timeout: 120000,
  }) as unknown as Promise<UploadResponse>
}

/**
 * 获取简历分页列表
 * @param params 查询参数
 * @returns 分页结果
 */
export function getResumeList(params: ResumeListQuery): Promise<PageResult<ResumeListItem>> {
  return request.get('/resumes', { params }) as unknown as Promise<PageResult<ResumeListItem>>
}

/**
 * 获取简历详情
 * @param id 简历 ID
 */
export function getResumeDetail(id: string): Promise<ResumeDetail> {
  return request.get(`/resumes/${id}`) as unknown as Promise<ResumeDetail>
}

/**
 * 删除简历
 * @param id 简历 ID
 */
export function deleteResume(id: string): Promise<void> {
  return request.delete(`/resumes/${id}`) as unknown as Promise<void>
}

/**
 * 获取简历预览地址
 * @param id 简历 ID
 */
export function getPreviewUrl(id: string): Promise<PreviewUrlResult> {
  return request.get(`/resumes/${id}/preview`) as unknown as Promise<PreviewUrlResult>
}

/**
 * 更新简历标签
 * @param id 简历 ID
 * @param tags 标签数组
 */
export function updateTags(id: string, tags: string[]): Promise<void> {
  return request.put(`/resumes/${id}/tags`, { tags }) as unknown as Promise<void>
}

/**
 * 切换收藏状态
 * @param id 简历 ID
 * @param isFavorite 是否收藏
 */
export function toggleFavorite(id: string, isFavorite: boolean): Promise<void> {
  return request.put(`/resumes/${id}/favorite`, { is_favorite: isFavorite }) as unknown as Promise<void>
}

/**
 * 更新备注
 * @param id 简历 ID
 * @param notes 备注内容
 */
export function updateNotes(id: string, notes: string): Promise<void> {
  return request.put(`/resumes/${id}/notes`, { notes }) as unknown as Promise<void>
}
