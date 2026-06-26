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
