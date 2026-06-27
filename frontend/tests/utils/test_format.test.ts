/**
 * 文件名: tests/utils/test_format.test.ts
 * 创建时间: 2026-06-27
 * 作者: TalentSense Team
 * 功能描述: formatRelativeTime 相对时间函数测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { formatRelativeTime } from '@/utils/format'

describe('utils/format.formatRelativeTime', () => {
  beforeEach(() => {
    // 固定当前时间为 2026-06-27 12:00:00 UTC
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-27T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('空字符串返回空', () => {
    expect(formatRelativeTime('')).toBe('')
  })

  it('今天的日期返回「今天」', () => {
    expect(formatRelativeTime('2026-06-27T08:00:00Z')).toBe('今天')
  })

  it('昨天的日期返回「昨天」', () => {
    expect(formatRelativeTime('2026-06-26T08:00:00Z')).toBe('昨天')
  })

  it('3 天前返回「3 天前」', () => {
    expect(formatRelativeTime('2026-06-24T08:00:00Z')).toBe('3 天前')
  })

  it('10 天前返回「1 周前」', () => {
    expect(formatRelativeTime('2026-06-17T08:00:00Z')).toBe('1 周前')
  })

  it('60 天前返回「2 个月前」', () => {
    expect(formatRelativeTime('2026-04-28T08:00:00Z')).toBe('2 个月前')
  })

  it('400 天前返回「1 年前」', () => {
    expect(formatRelativeTime('2025-05-23T08:00:00Z')).toBe('1 年前')
  })
})
