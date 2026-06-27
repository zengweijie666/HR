"""
文件名: app/agent/prompts.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 集中管理所有 Prompt 模板
"""

RESUME_EXTRACT_PROMPT = """请从以下简历文本中提取结构化信息，并以严格的 JSON 格式返回。

要求提取的字段及格式如下：
{{
  "name": "姓名（字符串，中文全名，如'张三'）",
  "phone": "手机号（字符串，11位中国大陆手机号，如'13800138000'）",
  "email": "邮箱（字符串，标准邮箱格式）",
  "gender": "性别（字符串：'男'或'女'，无法判断则填空字符串）",
  "age": "年龄（整数，从出生年份推算或直接提取，如28；无法判断填0）",
  "location": "所在地/现居城市（字符串，如'北京'、'上海'）",
  "education": "最高学历（字符串：'专科'/'本科'/'硕士'/'博士'/'高中'，无法判断填空字符串）",
  "education_level": 学历等级（整数：0=专科/高中及以下，1=本科，2=硕士，3=博士）,
  "work_years": 工作年限（整数，如3、5、10；从工作经历的起止日期推算或直接提取，无法判断填0）,
  "skills": ["技能1", "技能2"],
  "work_experience": [
    {{
      "company": "公司名称",
      "position": "职位/岗位",
      "start_date": "开始日期，格式YYYY-MM，只有年份则补'-01'",
      "end_date": "结束日期，格式YYYY-MM；至今/在职填'至今'",
      "description": "工作职责与成就描述（字符串）"
    }}
  ],
  "education_detail": [
    {{
      "school": "学校名称",
      "major": "专业",
      "degree": "学历/学位（如'本科'、'硕士'）",
      "start_date": "开始日期，格式YYYY-MM",
      "end_date": "结束日期，格式YYYY-MM"
    }}
  ],
  "projects": [
    {{
      "name": "项目名称",
      "role": "担任角色",
      "description": "项目描述与职责"
    }}
  ],
  "summary": "个人总结/自我评价（字符串，简要概括核心优势）",
  "salary": "期望薪资（字符串，如'15K-25K'、'20k'；没有则填空字符串）"
}}

提取规则：
1. 字符串字段：找不到信息填空字符串""，绝对不要返回null
2. 数字字段（age/education_level/work_years）：找不到填0，绝对不要返回null
3. 数组字段（skills/work_experience/education_detail/projects）：找不到填空数组[]
4. education_level必须根据education字段推算：专科/高中=0，本科=1，硕士=2，博士=3
5. work_years应根据work_experience中的起止日期计算总年限；如果简历直接写了"X年经验"则直接用
6. skills要从简历全文提取所有技术/业务技能关键词（如Python、Java、Vue、MySQL、项目管理等）
7. work_experience要提取所有工作经历，不要遗漏；description字段要包含职责和成就
8. education_detail要提取所有教育经历（本科、硕士等），不要遗漏
9. **【重要】projects字段必须提取所有项目经历**。简历中常见的项目经历段落标题包括"项目经历"、"项目经验"、"主要项目"、"项目作品"等。如果工作经历中的 description 包含具体项目名称、技术栈、职责描述，也应提取为独立的 project 条目。即使简历没有明确的项目段落，也要从工作经历中识别出参与的项目。
10. 姓名通常出现在简历最开头或个人信息区域；手机号以1开头共11位；邮箱包含@符号
11. 日期格式统一为YYYY-MM，如2020-07表示2020年7月；只有年份如"2020"则写"2020-01"
12. 只返回JSON，不要包含任何其他文字说明、markdown标记或代码块包裹

简历文本如下：
---
{text}
---"""

# ===== 检索策略相关 Prompt =====
STRATEGY_SELECT_PROMPT = """你是招聘检索策略选择器。根据用户查询选择最合适的改写策略：
- direct: 明确具体的查询（包含明确岗位名称或技术栈，如"Java工程师"、"找NLP算法"、"要2名Python开发"）
- hyde: 模糊描述（如"找个Java大佬"、"推荐厉害的算法"）
- subquery: 复杂多条件查询（如"Java且会Python，5年以上经验，本科"）
- backtracking: 指代历史内容的查询（如"刚说的那个"、"他的详情"）
判断原则：
1. 只要包含明确岗位/技能关键词（如工程师、Java、NLP、Python、算法、开发等），优先选direct
2. 只有当查询非常模糊（只有"大佬/高手/厉害"等形容词，没有具体技能）时才选hyde
查询：{query}
历史：{history}
只返回策略名（direct/hyde/subquery/backtracking）："""

HYDE_PROMPT = """你是招聘检索关键词扩展器。用户给出了一个模糊的招聘需求，请扩展出3-8个相关的技能关键词、同义词或岗位别称，用空格分隔，用于向量检索。

规则：
1. 只输出关键词，用空格分隔，不要句子，不要markdown，不要解释
2. 包含岗位名称的同义词（如"算法工程师"→"算法 机器学习工程师"）
3. 包含相关技术栈关键词
4. 总长度控制在100字以内

用户需求：{query}
关键词："""

SUBQUERY_PROMPT = """将以下复杂招聘查询拆解为多个子查询，返回 JSON 数组：
查询：{query}
子查询 JSON 数组："""

BACKTRACKING_PROMPT = """根据历史对话简化当前问题，使其独立可检索：
当前问题：{query}
历史：{history}
简化后的问题："""

# ===== LLM 评分 Prompt =====
SCORE_PROMPT = """你是招聘评分员。根据需求给候选人打分，按 4 个维度分别打分（0-100），并给出综合评分和一句话理由。

需求：{query}
候选人：{candidate}

评分维度：
- skill: 技能匹配度（候选人技能与需求关键词的重合度）
- experience: 工作经验匹配度（年限与岗位级别匹配）
- education: 学历匹配度（学历层次与岗位要求匹配）
- salary: 薪资匹配度（期望薪资与市场水平合理性）

严格按以下 JSON 格式返回，禁止返回 null，禁止添加任何其他文字：
{{"skill": 85, "experience": 70, "education": 90, "salary": 60, "overall": 78, "reason": "技能高度匹配，但薪资期望偏高"}}"""

# ===== 对话模块 Prompt =====
INTENT_PROMPT = """你是招聘助手意图分类器。根据用户查询分类意图：
- chitchat: 闲聊/打招呼（你好/谢谢/你是谁）
- search: 搜索/推荐候选人
- detail: 查询某候选人详情
- compare: 对比候选人
- qa: HR 知识问答/系统使用帮助/通用问答（不涉及具体候选人推荐）
查询：{query}
历史：{history}
只返回意图名（chitchat/search/detail/compare/qa）："""

CHITCHAT_PROMPT = """你是 TalentSense HR 招聘助手。友好回答用户的闲聊：
用户：{query}
助手："""

QA_PROMPT = """你是 TalentSense 智能招聘助手。你可以回答 HR 流程咨询、系统使用帮助、通用知识问答。

规则：
1. 不编造候选人信息，不提供虚假简历
2. 涉及具体候选人推荐时，引导用户使用"推荐/搜索/查找候选人"等语句
3. 回答简洁专业，HR 领域问题给出可执行建议
4. 系统使用问题基于 TalentSense HR 平台功能回答（简历库/工作台/邮件中心/数据看板/用户管理）

用户问题：{query}

请直接回答："""

CLARIFY_PROMPT = """没找到匹配的候选人。引导用户提供更多细节（技术栈/年限/薪资/学历）：
用户需求：{query}
引导话术："""

DETAIL_PROMPT = """根据候选人详情，生成简洁介绍：
查询：{query}
候选人：{candidate}
介绍："""

SEARCH_RESPOND_PROMPT = """你是 TalentSense HR 招聘助手。请严格根据提供的候选人列表回答用户需求。

【重要规则】
1. 只能使用下方提供的候选人数据，绝对禁止编造不存在的候选人或信息
2. 如果用户要求N名（如"两名"、"2个"、"几位"），只展示前N名匹配度最高的候选人
3. 每个候选人引用姓名、工作年限、核心技能、匹配理由
4. 如果候选人列表为空，直接说"当前简历库中没有找到匹配的候选人，建议您补充需求细节（如技术栈、年限、学历等）或上传更多简历"
5. 不要输出"理想候选人简历描述"或任何你自己生成的虚假简历
6. 回答简洁专业，用中文

用户需求：{query}

检索到的候选人数据（JSON格式）：
{candidates}

请回答："""

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
