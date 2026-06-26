/**
 * 文件名: utils/format.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 薪资/日期/通用格式化
 */

/** 格式化薪资范围：{min:20,max:30} → "20-30K" */
export function formatSalary(salary: { min: number; max: number } | undefined): string {
  if (!salary) return '面议'
  const { min, max } = salary
  if (min && max) return `${min}-${max}K`
  if (max) return `≤${max}K`
  if (min) return `≥${min}K`
  return '面议'
}

/** 格式化日期：ISO 字符串 → "2026-06-26" */
export function formatDate(iso: string | undefined, withTime = false): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return '-'
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  if (!withTime) return `${y}-${m}-${day}`
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

/** 相对时间：返回"刚刚/3分钟前/2小时前/3天前" */
export function formatRelative(iso: string | undefined): string {
  if (!iso) return '-'
  const t = new Date(iso).getTime()
  if (isNaN(t)) return '-'
  const diff = Date.now() - t
  const min = Math.floor(diff / 60000)
  const hour = Math.floor(diff / 3600000)
  const day = Math.floor(diff / 86400000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min}分钟前`
  if (hour < 24) return `${hour}小时前`
  if (day < 30) return `${day}天前`
  return formatDate(iso)
}

/** 候选人分数 → 等级 */
export function scoreLevel(score: number): { label: string; color: string } {
  if (score >= 90) return { label: '极佳', color: '#1a3a32' }
  if (score >= 80) return { label: '优秀', color: '#2d5247' }
  if (score >= 70) return { label: '良好', color: '#c8924a' }
  if (score >= 60) return { label: '一般', color: '#d97757' }
  return { label: '较弱', color: '#918b82' }
}

/** 文件大小格式化 */
export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}
