"""
文件名: app/agent/prompts.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 集中管理所有 Prompt 模板
"""

RESUME_EXTRACT_PROMPT = """从以下简历文本中提取结构化信息，返回 JSON，字段包括：
name, phone, email, gender, age, location, education(专科/本科/硕士/博士), education_level(0-3),
work_years, skills(list), work_experience(list of {{company,position,start_date,end_date,description}}),
education_detail(list of {{school,major,degree,start_date,end_date}}), summary, salary
简历文本：
{text}
返回 JSON："""

# ===== 检索策略相关 Prompt =====
STRATEGY_SELECT_PROMPT = """你是招聘检索策略选择器。根据用户查询选择最合适的改写策略：
- direct: 明确具体的查询（如"Java 5年"）
- hyde: 模糊描述（如"找个Java大佬"）
- subquery: 复杂多条件查询（如"Java且会Python，5年经验"）
- backtracking: 指代历史内容的查询（如"刚说的那个"）
查询：{query}
历史：{history}
只返回策略名（direct/hyde/subquery/backtracking）："""

HYDE_PROMPT = """基于以下招聘需求，生成一段假设的理想候选人简历描述（用于检索匹配）：
需求：{query}
假设简历："""

SUBQUERY_PROMPT = """将以下复杂招聘查询拆解为多个子查询，返回 JSON 数组：
查询：{query}
子查询 JSON 数组："""

BACKTRACKING_PROMPT = """根据历史对话简化当前问题，使其独立可检索：
当前问题：{query}
历史：{history}
简化后的问题："""

# ===== LLM 评分 Prompt =====
SCORE_PROMPT = """你是招聘评分员。根据需求给候选人打分（0-100），只返回数字：
需求：{query}
候选人：{candidate}
评分："""

# ===== 对话模块 Prompt =====
INTENT_PROMPT = """你是招聘助手意图分类器。根据用户查询分类意图：
- chitchat: 闲聊/打招呼
- search: 搜索/推荐候选人
- detail: 查询某候选人详情
- compare: 对比候选人
查询：{query}
历史：{history}
只返回意图名（chitchat/search/detail/compare）："""

CHITCHAT_PROMPT = """你是 TalentSense HR 招聘助手。友好回答用户的闲聊：
用户：{query}
助手："""

CLARIFY_PROMPT = """没找到匹配的候选人。引导用户提供更多细节（技术栈/年限/薪资/学历）：
用户需求：{query}
引导话术："""

DETAIL_PROMPT = """根据候选人详情，生成简洁介绍：
查询：{query}
候选人：{candidate}
介绍："""

SEARCH_RESPOND_PROMPT = """根据检索到的候选人，回答用户需求。引用候选人姓名与核心匹配点：
需求：{query}
候选人：{candidates}
回答："""

# ===== JD 匹配 Prompt =====
JD_PARSE_PROMPT = """从以下招聘需求(JD)中提取结构化信息，返回 JSON：
- title: 岗位名称
- skills: 所需技能列表
- work_years_min: 最低工作年限
- salary_max: 最高薪资(K)
JD 文本：{jd_text}
返回 JSON："""

JD_MATCH_REASON_PROMPT = """用一句话说明为什么该候选人匹配此 JD：
JD：{jd}
候选人：{candidate}
匹配度：{score}
理由："""

# ===== 面试题 Prompt =====
INTERVIEW_QUESTION_PROMPT = """你是招聘面试官。根据候选人简历生成 {count} 道面试题，返回 JSON 数组：
岗位：{job_title}
候选人：{name}
技能：{skills}
工作年限：{work_years} 年
简历摘要：{summary}
每道题包含字段：question(题目), category(分类: 技术/项目/行为/开放)
返回 JSON 数组："""
