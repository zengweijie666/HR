/**
 * 文件名: utils/constant.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 全局枚举常量，与 API 文档 0.6 节一致
 */

/** 意图类型 */
export const INTENT_TYPES = {
  chitchat: '闲聊',
  search: '搜索推荐',
  detail: '详情查询',
  compare: '对比',
} as const

/** 检索策略 */
export const STRATEGY_TYPES = {
  direct: '直接检索',
  hyde: '假设文档',
  subquery: '子查询',
  backtracking: '回溯简化',
} as const

/** 解析状态 */
export const PARSE_STATUS = {
  pending: '待解析',
  parsing: '解析中',
  completed: '已解析',
  failed: '解析失败',
} as const

/** 学历等级（0-3） */
export const EDUCATION_LEVELS: Record<number, string> = {
  0: '专科',
  1: '本科',
  2: '硕士',
  3: '博士',
}

/** SSE 事件类型 */
export const SSE_EVENTS = {
  intent: 'intent',
  rewrite: 'rewrite',
  retrieval: 'retrieval',
  rank: 'rank',
  token: 'token',
  candidates: 'candidates',
  done: 'done',
  error: 'error',
} as const

/** 面试结果 */
export const INTERVIEW_RESULTS = {
  pass: '通过',
  fail: '不通过',
  pending: '待定',
  strong: '强烈推荐',
} as const
