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

SYNONYM_EXPAND_PROMPT = """你是招聘技能同义词扩展器。用户给出了一个包含明确技能/岗位关键词的查询，请扩展出相关的具体技术、框架、工具或领域同义词，用于语义检索召回更多匹配候选人。

规则：
1. 只输出关键词，用空格分隔，不要句子，不要markdown，不要解释
2. 扩展出该领域常见的技术栈和工具（如"NLP"→"NLP BERT GPT Transformer FastText Word2Vec TextCNN 自然语言处理 文本分类 命名实体识别"）
3. 扩展出岗位别称（如"前端"→"前端 Vue React HTML CSS JavaScript TypeScript"）
4. 保留原始查询词，扩展3-10个关键词
5. 总长度控制在150字以内

用户查询：{query}
扩展关键词："""

SUBQUERY_PROMPT = """将以下复杂招聘查询拆解为多个子查询，返回 JSON 数组：
查询：{query}
子查询 JSON 数组："""

BACKTRACKING_PROMPT = """根据历史对话简化当前问题，使其独立可检索：
当前问题：{query}
历史：{history}
简化后的问题："""

# ===== 自然语言过滤条件提取 Prompt =====
FILTER_EXTRACT_PROMPT = """你是招聘需求过滤器提取器。从用户自然语言查询中提取硬性过滤条件，以严格JSON返回。

提取规则：
- education_min: 最低学历等级（整数：0=专科/高中及以下，1=本科，2=硕士，3=博士）；
  * "专科以上/大专及以上" → 0
  * "本科以上/本科及以上/本科" → 1
  * "硕士以上/硕士及以上/硕士/研究生" → 2
  * "博士以上/博士" → 3
  * 未提及学历要求 → null
- work_years_min: 最低工作年限（整数，单位：年）；
  * "3年以上/3年经验/3年及以上" → 3
  * "应届生/应届毕业生/无经验要求" → 0
  * 未提及年限要求 → null
- salary_max: 最高期望薪资（整数，单位：K/千）；
  * "30K以内/30k以下/30K及以下/薪资不超过30K" → 30
  * "25k以内" → 25
  * 未提及薪资要求 → null
- required_skills: 必须具备的技能关键词列表（字符串数组）；
  * "有没有会html的" → ["html"]
  * "会Python的工程师" → ["python"]
  * "懂React和Vue的前端" → ["react", "vue"]
  * "有NLP项目经验的" → ["nlp"]
  * "会Java或Spring的" → ["java", "spring"]
  * 未提及具体技能要求 → []

注意：
1. 只提取明确硬性条件，不要猜测
2. 数字必须是整数，不要字符串
3. 没有提到的条件必须返回 null（不要返回0）
4. required_skills为空数组时表示无技能硬性要求
5. 技能关键词统一小写
6. 只返回JSON，禁止其他文字

用户查询：{query}
JSON："""

# ===== LLM 评分 Prompt =====
SCORE_PROMPT = """你是招聘评分员。根据招聘需求给候选人打分，按 4 个维度分别打分（0-100）。
【重要】同一次招聘需求下，不同候选人的分数必须有明显区分度，禁止给所有候选人相同分数！
区分度来自候选人的实际工作年限、项目深度、技能覆盖度差异，而非平均分。

需求：{query}
候选人核心信息：{candidate}

评分维度（严格按以下基准打分）：
- skill: 技能匹配度
  * 90-100: 技能完全覆盖需求，且有对口岗位≥2年工作经验
  * 75-89: 技能高度匹配，有相关项目落地经验
  * 60-74: 部分核心技能匹配，项目经验有限
  * 40-59: 仅边缘技能沾边
  * 0-39: 技能不匹配

- experience: 工作经验匹配度（核心区分维度，必须按年限拉开差距）
  * 90-100: 工作年限≥3年且岗位完全对口
  * 75-89: 1-3年对口岗位经验
  * 55-74: 应届生/实习但有完整对口项目
  * 30-54: 仅有课程作业或少量沾边项目
  * 0-29: 无对口经验

- education: 学历匹配度
  * 90-100: 硕士及以上且专业对口
  * 75-89: 本科且专业对口，或硕士跨专业
  * 60-74: 普通本科
  * 40-59: 专科
  * 0-39: 高中及以下

- salary: 薪资匹配度
  * 85-100: 期望薪资合理或未填（未填给85）
  * 60-84: 期望略高但在合理范围
  * 0-59: 期望过高

评分示例（必须体现区分度）：
- 4年NLP工程师 + BERT项目落地 → skill=92, experience=90
- 0年经验应届生 + 仅有BERT课程项目 → skill=72, experience=50

严格按以下 JSON 格式返回，禁止返回 null，禁止添加任何其他文字：
{{"skill": 85, "experience": 70, "education": 90, "salary": 85, "overall": 80, "reason": "技能高度匹配，4年对口经验"}}"""

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

COMPARE_PROMPT = """你是 TalentSense HR 招聘助手。请对比以下候选人，给出结构化对比分析。

用户问题：{query}

候选人数据（JSON格式，仅使用以下数据，禁止编造信息）：
{candidates}

对比规则：
1. 先明确指出被对比的候选人姓名
2. 从以下维度对比：工作年限、核心技能、项目/工作经验、学历、匹配度评分
3. 给出明确的对比结论：各自优势、适合场景、推荐优先级
4. 如果某候选人在用户提到的方面明显占优，直接指出
5. 用中文简洁专业回答，可使用列表和加粗突出重点
6. 评分差异要解释清楚原因（如年限差距、技能匹配度差异等）

请直接回答："""

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


# ===== 查询分解 Prompt =====
QUERY_DECOMPOSE_PROMPT = """你是招聘查询分解器。将用户查询分解为主查询、子查询列表和结构化过滤条件，以严格JSON返回。

要求：
1. main_query: 原始查询的核心语义版本（去除口语化词如"有没有"、"帮我找"）
2. sub_queries: 拆解出 1-3 个子查询，每个聚焦一个条件维度（技能/经验/岗位），用于多路召回
3. structured_filters: 提取硬性条件
   - required_skills: 技能关键词列表（小写），如 ["python", "docker"]
   - work_years_min: 最低工作年限（整数，无则不填）
   - salary_max: 最高期望薪资（K，整数，无则不填）
   - education_min: 最低学历等级（0=专科/1=本科/2=硕士/3=博士，无则不填）
   - job_type: 岗位类型（如"后端"/"前端"/"算法"，无则填空字符串）

示例：
查询"3年经验后端工程师会Python和Docker 30K以内"
{{
  "main_query": "后端工程师 Python Docker 3年经验 30K以内",
  "sub_queries": ["后端工程师 Python Docker", "3年经验后端开发", "Python Docker 微服务"],
  "structured_filters": {{
    "required_skills": ["python", "docker"],
    "work_years_min": 3,
    "salary_max": 30,
    "job_type": "后端"
  }}
}}

查询"有没有会html的"
{{
  "main_query": "html",
  "sub_queries": ["html 前端"],
  "structured_filters": {{
    "required_skills": ["html"],
    "job_type": "前端"
  }}
}}

查询"nlp相关的呢"
{{
  "main_query": "nlp",
  "sub_queries": ["nlp 自然语言处理", "bert transformer"],
  "structured_filters": {{
    "required_skills": ["nlp"],
    "job_type": "算法"
  }}
}}

现在分解以下查询，只返回JSON，不要其他文字：
查询：{query}
"""


# ===== 上下文压缩 Prompt =====
CONTEXT_COMPRESS_PROMPT = """你是简历上下文压缩器。将同一简历的多个检索片段合并压缩为单一精炼摘要，聚焦于与查询的相关性。

要求：
1. 输出 ≤500 字
2. 聚焦三个维度：技能匹配点、经验匹配点、项目匹配点
3. 去除重复信息，保留关键事实（技能名、年限、公司、项目名）
4. 不要评价，只陈述事实

查询：{query}

简历片段（按相关性排序）：
{chunks_text}

只输出压缩后的摘要，不要其他文字："""
