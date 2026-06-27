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

/**
 * 邮件模板变量含义映射
 * key 为模板中的变量名（不含 {{ }}），value 为 { label, placeholder }
 * - label: 变量显示名称（左侧标签）
 * - placeholder: 输入框占位提示，方便用户填写
 */
export interface EmailVarMeta {
  label: string
  placeholder: string
}

export const EMAIL_VAR_LABELS: Record<string, EmailVarMeta> = {
  candidate_name: { label: '候选人姓名', placeholder: '如：张三' },
  position: { label: '应聘职位', placeholder: '如：Java 工程师' },
  company: { label: '公司名称', placeholder: '如：TalentSense' },
  salary: { label: '薪资范围', placeholder: '如：20-30K' },
  interview_time: { label: '面试时间', placeholder: '如：2026-07-01 14:00' },
  interview_location: { label: '面试地点', placeholder: '如：上海市浦东新区 XX 大厦 10 楼' },
  interviewer: { label: '面试官', placeholder: '如：李经理' },
  hr_name: { label: 'HR 签名', placeholder: '如：王HR' },
  hr_phone: { label: 'HR 联系电话', placeholder: '如：13800138000' },
  onboarding_date: { label: '入职日期', placeholder: '如：2026-07-15' },
  deadline: { label: '回复截止时间', placeholder: '如：2026-07-03 18:00' },
  offer_url: { label: 'Offer 链接', placeholder: '如：https://example.com/offer/xxx' },
}

/**
 * 获取邮件变量的含义信息
 * 已知变量返回对应 { label, placeholder }，未知变量回退为变量名本身
 */
export function getEmailVarMeta(varName: string): EmailVarMeta {
  return (
    EMAIL_VAR_LABELS[varName] ?? {
      label: varName,
      placeholder: `请输入 ${varName}`,
    }
  )
}
