/**
 * 文件名: api/request.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: Axios 实例与拦截器
 *   - 请求拦截：从 localStorage 注入 Bearer Token
 *   - 响应拦截：剥离 { code, message, data } 外层，按 code 分发处理
 */
import axios, { type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types/api'

/** localStorage 中存储的 access_token 键名 */
const ACCESS_TOKEN_KEY = 'access_token'
/** localStorage 中存储的 refresh_token 键名 */
const REFRESH_TOKEN_KEY = 'refresh_token'
/** token 失效业务码 */
const CODE_TOKEN_EXPIRED = 1002
/** 成功业务码（后端 CODE.SUCCESS = 0） */
const CODE_SUCCESS = 0

/** Axios 实例：baseURL 取自环境变量，默认 /api/v1 */
const request = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api/v1',
  timeout: 30000,
})

/** 清空本地凭证并跳转登录页 */
function clearAuthAndRedirect(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  window.location.href = '/login'
}

// 请求拦截：注入 Authorization 头
request.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：剥离外层 envelope，处理业务码与网络异常
request.interceptors.response.use(
  /**
   * 成功响应处理
   * @param response Axios 响应对象，data 为 ApiResponse 信封
   * @returns 剥离后的 data 字段；非信封响应（如 Blob）原样返回
   */
  ((response: AxiosResponse<ApiResponse>) => {
    const res = response.data
    // 非标准信封（如二进制流、纯文本）原样返回
    if (!res || typeof res !== 'object' || !('code' in res)) {
      return res
    }
    if (res.code === CODE_SUCCESS) {
      return res.data
    }
    if (res.code === CODE_TOKEN_EXPIRED) {
      clearAuthAndRedirect()
      return Promise.reject(new Error(res.message || '登录已过期'))
    }
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message || '请求失败'))
  }) as unknown as (response: AxiosResponse) => AxiosResponse | Promise<AxiosResponse>,
  /**
   * 网络或 HTTP 错误兜底
   * 后端业务异常返回 HTTP 4xx/5xx（如 401/403/404），需在此处理跳转与提示
   * @param error 请求错误对象
   */
  (error: unknown) => {
    // axios 错误：从 response 中提取 HTTP 状态码与业务码
    const axiosErr = error as { response?: { status?: number; data?: ApiResponse }; message?: string }
    const status = axiosErr.response?.status
    const bizCode = axiosErr.response?.data?.code
    // HTTP 401 或业务码 1002（token 失效）：清空凭证并跳转登录页
    if (status === 401 || bizCode === CODE_TOKEN_EXPIRED) {
      clearAuthAndRedirect()
      return Promise.reject(new Error(axiosErr.response?.data?.message || '登录已过期'))
    }
    // 其他业务错误：提取后端 message，无则用网络异常兜底
    const msg = axiosErr.response?.data?.message || (error instanceof Error ? error.message : '网络异常，请稍后重试')
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

export default request
