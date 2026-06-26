/**
 * 文件名: tests/api/test_request.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 测试 axios 实例拦截器
 *   - 成功响应剥离外层 data
 *   - 业务错误 code!=200 时 reject
 */
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import request from '@/api/request'

/** msw 模拟服务器，使用 RegExp 匹配路径以兼容不同 origin 解析 */
const server = setupServer(
  http.get(/\/api\/v1\/success$/, () => {
    return HttpResponse.json({
      code: 0,
      message: 'ok',
      data: { foo: 'bar' },
      trace_id: 't1',
    })
  }),
  http.get(/\/api\/v1\/error$/, () => {
    return HttpResponse.json({
      code: 1001,
      message: '业务错误',
      data: null,
      trace_id: 't2',
    })
  }),
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('api/request', () => {
  it('成功响应剥离外层返回 data', async () => {
    const data = await request.get('/success')
    expect(data).toEqual({ foo: 'bar' })
  })

  it('业务错误 code!=200 时 reject', async () => {
    await expect(request.get('/error')).rejects.toThrow('业务错误')
  })
})
