/**
 * 文件名: api/jd.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: JD 匹配接口
 */
import request from './request'
import type { JdMatchResult } from '@/types/jd'

/**
 * JD 文本匹配候选人
 * @param jdText JD 文本
 * @param topK 返回数量
 */
export function matchJd(jdText: string, topK: number): Promise<JdMatchResult> {
  return request.post('/jd/match', { jd_text: jdText, top_k: topK }) as unknown as Promise<JdMatchResult>
}
