/**
 * 文件名: src/utils/monitor.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 前端错误与性能监控，上报到后端 /api/v1/monitor
 *   - JS运行时错误、Promise未捕获rejection、资源加载错误
 *   - Web Vitals 基础性能指标 (FP/LCP)
 *   - 支持主动上报 manualError()
 */

const MAX_STACK_LENGTH = 2000
let initialized = false
let lastReportTs = 0
const THROTTLE_MS = 500

function getToken(): string {
  try {
    return localStorage.getItem('access_token') || ''
  } catch {
    return ''
  }
}

function postJSON(path: string, body: Record<string, any>): void {
  const now = Date.now()
  if (now - lastReportTs < THROTTLE_MS) return
  lastReportTs = now
  try {
    const token = getToken()
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    fetch(path, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      keepalive: true,
    }).catch(() => {})
  } catch {}
}

function reportError(errorData: Record<string, any>): void {
  postJSON('/api/v1/monitor/error', {
    ...errorData,
    user_agent: navigator.userAgent,
    url: window.location.href,
  })
}

function parseErrorEvent(event: ErrorEvent): Record<string, any> {
  const { message, filename, lineno, colno, error } = event
  return {
    error_type: 'js_error',
    message: (message || String(error || '')).slice(0, 500),
    stack: error?.stack?.slice(0, MAX_STACK_LENGTH) || '',
    filename: filename || '',
    line: lineno || 0,
    col: colno || 0,
  }
}

function parseRejection(event: PromiseRejectionEvent): Record<string, any> {
  const reason = event.reason
  let msg = ''
  let stack = ''
  if (reason instanceof Error) {
    msg = reason.message
    stack = reason.stack?.slice(0, MAX_STACK_LENGTH) || ''
  } else {
    try {
      msg = typeof reason === 'string' ? reason : JSON.stringify(reason)
    } catch {
      msg = String(reason)
    }
  }
  return {
    error_type: 'promise_rejection',
    message: msg.slice(0, 500),
    stack,
    filename: '',
    line: 0,
    col: 0,
  }
}

function parseResourceError(event: Event): Record<string, any> | null {
  const target = event.target as any
  if (!target || (!target.src && !target.href)) return null
  return {
    error_type: 'resource_error',
    message: `资源加载失败: ${target.src || target.href}`,
    stack: '',
    filename: target.src || target.href,
    line: 0,
    col: 0,
    extra: { tagName: target.tagName },
  }
}

function reportPerf(metric: string, value: number, extra?: Record<string, any>): void {
  postJSON('/api/v1/monitor/perf', {
    metric,
    value,
    url: window.location.href,
    extra,
  })
}

function collectWebVitals(): void {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return

  try {
    const fpObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-paint') {
          reportPerf('fp', entry.startTime)
        }
      }
    })
    fpObserver.observe({ type: 'paint', buffered: true })
  } catch {}

  try {
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      if (entries.length > 0) {
        const last = entries[entries.length - 1] as any
        reportPerf('lcp', last.startTime)
      }
    })
    lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true })
  } catch {}
}

export function initMonitor(): void {
  if (initialized) return
  initialized = true

  window.addEventListener('error', (event) => {
    if (event.target && (event.target as any).tagName && (event.target as any).tagName !== 'BODY' && (event.target as any).tagName !== 'HTML') {
      const info = parseResourceError(event)
      if (info) reportError(info)
      return
    }
    reportError(parseErrorEvent(event))
  }, true)

  window.addEventListener('unhandledrejection', (event) => {
    reportError(parseRejection(event))
  })

  window.addEventListener('load', () => {
    setTimeout(collectWebVitals, 1000)
  })
}

export function manualError(err: Error | string, extra?: Record<string, any>): void {
  const msg = err instanceof Error ? err.message : err
  const stack = err instanceof Error ? err.stack?.slice(0, MAX_STACK_LENGTH) || '' : ''
  reportError({
    error_type: 'manual',
    message: msg.slice(0, 500),
    stack,
    filename: '',
    line: 0,
    col: 0,
    extra,
  })
}
