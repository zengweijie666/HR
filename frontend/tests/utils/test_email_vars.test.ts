/**
 * 文件名: tests/utils/test_email_vars.test.ts
 * 创建时间: 2026-06-27
 * 作者: TalentSense Team
 * 功能描述: 邮件模板变量含义映射测试
 *   - 已知变量返回中文 label + 有含义的 placeholder
 *   - 未知变量回退为变量名本身
 */
import { describe, it, expect } from 'vitest'
import { getEmailVarMeta, EMAIL_VAR_LABELS } from '@/utils/constant'

describe('utils/constant.getEmailVarMeta', () => {
  it('已知变量 candidate_name 返回中文标签与占位符', () => {
    const meta = getEmailVarMeta('candidate_name')
    expect(meta.label).toBe('候选人姓名')
    expect(meta.placeholder).toBe('如：张三')
  })

  it('已知变量 interview_time 返回面试时间占位符', () => {
    const meta = getEmailVarMeta('interview_time')
    expect(meta.label).toBe('面试时间')
    expect(meta.placeholder).toContain('2026-07-01')
  })

  it('未知变量回退为变量名本身 + 通用占位符', () => {
    const meta = getEmailVarMeta('unknown_field')
    expect(meta.label).toBe('unknown_field')
    expect(meta.placeholder).toBe('请输入 unknown_field')
  })

  it('EMAIL_VAR_LABELS 包含常见业务变量', () => {
    expect(EMAIL_VAR_LABELS).toHaveProperty('candidate_name')
    expect(EMAIL_VAR_LABELS).toHaveProperty('position')
    expect(EMAIL_VAR_LABELS).toHaveProperty('company')
    expect(EMAIL_VAR_LABELS).toHaveProperty('salary')
    expect(EMAIL_VAR_LABELS).toHaveProperty('interview_time')
  })
})
