/**
 * 文件名: utils/download.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 文件下载工具
 */

/** Blob 流下载（用于 Excel 导出） */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

/** 根据响应生成默认文件名 */
export function defaultFilename(prefix: string, ext: string): string {
  const d = new Date()
  const stamp = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`
  return `${prefix}_${stamp}.${ext}`
}
