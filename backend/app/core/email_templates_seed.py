"""
文件名: app/core/email_templates_seed.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: 预置邮件模板种子数据，启动时若 email_templates 集合为空则插入
入参: db（MongoDB 数据库实例）
出参: 无（直接写入集合）
"""
import uuid
from datetime import datetime, timezone

# 预置模板：4 个常用场景
BUILTIN_TEMPLATES = [
    {
        "name": "面试邀请",
        "subject": "【{{ company }}】面试邀请 - {{ position }}",
        "body": """<html><body>
<h2>{{ candidate_name }} 您好，</h2>
<p>感谢您对 {{ company }} {{ position }} 职位的关注。</p>
<p>我们诚挚邀请您参加面试：</p>
<ul>
  <li><strong>时间：</strong>{{ interview_time }}</li>
  <li><strong>地点：</strong>线上面试（具体链接将另行通知）</li>
  <li><strong>期望薪资：</strong>{{ salary }}</li>
</ul>
<p>如时间不便，请回复邮件另行约定。</p>
<p>此致<br/>{{ company }} 招聘团队</p>
</body></html>""",
        "category": "interview",
    },
    {
        "name": "Offer 通知",
        "subject": "【{{ company }}】Offer 通知 - {{ position }}",
        "body": """<html><body>
<h2>{{ candidate_name }} 您好，</h2>
<p>恭喜您通过 {{ company }} {{ position }} 职位的全部面试环节。</p>
<p>我们很高兴向您发放 Offer：</p>
<ul>
  <li><strong>职位：</strong>{{ position }}</li>
  <li><strong>薪资：</strong>{{ salary }}</li>
  <li><strong>入职时间：</strong>{{ interview_time }}</li>
</ul>
<p>请在 3 个工作日内回复确认。</p>
<p>此致<br/>{{ company }} 招聘团队</p>
</body></html>""",
        "category": "offer",
    },
    {
        "name": "面试未通过通知",
        "subject": "【{{ company }}】面试结果通知",
        "body": """<html><body>
<h2>{{ candidate_name }} 您好，</h2>
<p>感谢您对 {{ company }} {{ position }} 职位的关注及参加面试。</p>
<p>经过综合评估，很遗憾您本次未通过该职位面试。您的简历已存入人才库，后续有合适机会我们将优先联系您。</p>
<p>祝您求职顺利。</p>
<p>此致<br/>{{ company }} 招聘团队</p>
</body></html>""",
        "category": "reject",
    },
    {
        "name": "招聘进度通知",
        "subject": "【{{ company }}】招聘进度更新",
        "body": """<html><body>
<h2>{{ candidate_name }} 您好，</h2>
<p>您应聘的 {{ company }} {{ position }} 职位进度已更新。</p>
<p>当前状态：<strong>{{ interview_time }}</strong></p>
<p>如有疑问请随时联系我们。</p>
<p>此致<br/>{{ company }} 招聘团队</p>
</body></html>""",
        "category": "progress",
    },
]


async def seed_builtin_templates(db):
    """若 email_templates 集合为空，插入预置模板

    入参:
        db: MongoDB 数据库实例
    """
    count = await db.email_templates.count_documents({})
    if count > 0:
        return
    now = datetime.now(timezone.utc).isoformat()
    for tpl in BUILTIN_TEMPLATES:
        await db.email_templates.insert_one({
            "template_id": f"tpl_{uuid.uuid4().hex[:12]}",
            "name": tpl["name"],
            "subject": tpl["subject"],
            "body": tpl["body"],
            "category": tpl["category"],
            "is_builtin": True,
            "created_at": now,
            "updated_at": now,
        })
