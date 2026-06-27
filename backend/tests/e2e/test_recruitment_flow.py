"""
文件名: tests/e2e/test_recruitment_flow.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 端到端招聘业务流程集成测试
入参: e2e_env fixture
出参: 无

测试流程（完整招聘闭环）：
  1. HR 登录 → 获取 token
  2. 上传新简历 → 解析入库
  3. 查询简历列表 → 验证数据流转
  4. 获取简历详情
  5. 标签管理（添加标签 + 收藏 + 备注）
  6. 自然语言检索候选人
  7. 创建对话会话 → SSE 流式对话
  8. JD 匹配候选人
  9. 生成面试题 + 保存面试评价
  10. 候选人对比 + 相似推荐
  11. 导出 Excel
  12. 发送推荐邮件
  13. 数据看板统计
  14. 删除简历 → 验证清理

设计原则：
- 数据在 FakeMongo 中真实流转，步骤间有依赖关系
- 每步验证统一响应格式 {code, message, data, trace_id}
- 验证业务逻辑正确性（数据持久化、状态变更、跨模块数据一致性）
"""
import json
import pytest
from tests.e2e.conftest import _auth_header, parse_sse_events


def test_01_login(e2e_env):
    """步骤1: HR 登录获取 token"""
    client = e2e_env["client"]
    r = client.post("/api/v1/auth/login", json={
        "email": "admin@talentsense.com",
        "password": "admin123",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]
    assert body["data"]["user"]["username"] == "admin"
    e2e_env["state"]["token"] = body["data"]["access_token"]


def test_02_login_wrong_password(e2e_env):
    """步骤1b: 错误密码登录失败"""
    client = e2e_env["client"]
    r = client.post("/api/v1/auth/login", json={
        "email": "admin@talentsense.com",
        "password": "wrong",
    })
    body = r.json()
    assert body["code"] == 1002  # AuthError


def test_03_get_current_user(e2e_env):
    """步骤1c: 用 token 获取当前用户信息"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/auth/me", headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "admin"


def test_04_list_resumes_initial(e2e_env):
    """步骤2: 查询简历列表（初始 2 条预置数据）"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/resumes", headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 2
    assert len(body["data"]["list"]) == 2


def test_05_upload_resume(e2e_env):
    """步骤3: 上传新简历（mock MinIO/OCR/LLM/Embedding）"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    # 准备 LLM 返回结构化简历 JSON
    e2e_env["llm_chat_responses"][:] = [
        json.dumps({
            "name": "王五", "phone": "13700001111", "email": "wangwu@example.com",
            "gender": "男", "age": 28, "location": "北京",
            "education": "本科", "education_level": 2,
            "work_years": 4, "skills": ["Go", "Kubernetes", "Docker"],
            "work_experience": [], "education_detail": [],
            "summary": "4 年 Go 后端开发，云原生经验", "salary": "25-35K",
        }, ensure_ascii=False),
    ]
    e2e_env["llm_chat_call_count"]["i"] = 0

    fake_pdf = b"%PDF-1.4 fake content"
    r = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("wangwu.pdf", fake_pdf, "application/pdf")},
        data={"overwrite": "false"},
        headers=_auth_header(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["resume_id"]
    assert body["data"]["candidate_id"]
    e2e_env["state"]["resume_id_wang"] = body["data"]["resume_id"]
    e2e_env["state"]["candidate_id_wang"] = body["data"]["candidate_id"]


def test_06_list_resumes_after_upload(e2e_env):
    """步骤4: 上传后查询简历列表（应有 3 条）"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/resumes", headers=_auth_header(token))
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 3


def test_07_get_resume_detail(e2e_env):
    """步骤5: 获取王五简历详情"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    resume_id = e2e_env["state"]["resume_id_wang"]
    r = client.get(f"/api/v1/resumes/{resume_id}", headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["resume_id"] == resume_id


def test_08_get_detail_not_found(e2e_env):
    """步骤5b: 不存在的简历返回 404"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/resumes/res_not_exist", headers=_auth_header(token))
    body = r.json()
    assert body["code"] == 1004  # NotFoundError


def test_09_update_tags(e2e_env):
    """步骤6a: 给张三添加标签"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.put("/api/v1/resumes/res_demo_zhang/tags", json={
        "tags": ["高潜力", "Java方向"]
    }, headers=_auth_header(token))
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["tags"] == ["高潜力", "Java方向"]


def test_10_toggle_favorite(e2e_env):
    """步骤6b: 收藏张三"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.put("/api/v1/resumes/res_demo_zhang/favorite", json={
        "is_favorite": True
    }, headers=_auth_header(token))
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["is_favorite"] is True


def test_11_update_notes(e2e_env):
    """步骤6c: 更新张三评价备注"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.put("/api/v1/resumes/res_demo_zhang/notes", json={
        "notes": "技术能力扎实，沟通良好，推荐进入下一轮"
    }, headers=_auth_header(token))
    body = r.json()
    assert body["code"] == 0
    assert "推荐进入下一轮" in body["data"]["notes"]


def test_12_list_with_filter(e2e_env):
    """步骤6d: 按收藏过滤简历列表"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/resumes?is_favorite=true", headers=_auth_header(token))
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 1
    assert body["data"]["list"][0]["is_favorite"] is True


def test_13_search_candidates(e2e_env):
    """步骤7: 自然语言检索候选人"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    # 重置 LLM 调用计数，设置检索评分响应
    e2e_env["llm_chat_responses"][:] = [
        "92",  # 张三评分
        "张三匹配度高，5 年 Java 经验",  # 张三理由
        "78",  # 李四评分
        "李四 Python 经验，部分匹配",  # 李四理由
    ]
    e2e_env["llm_chat_call_count"]["i"] = 0

    r = client.post("/api/v1/search", json={
        "query": "Java 5年经验",
        "filters": {},
        "top_k": 5,
    }, headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1
    # 验证候选人卡片字段
    cand = body["data"][0]
    assert "candidate_id" in cand
    assert "name" in cand
    assert "score" in cand
    assert "reason" in cand


def test_14_create_chat_session(e2e_env):
    """步骤8a: 创建对话会话"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.post("/api/v1/chat/sessions", json={"title": "Java 候选人咨询"}, headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["session_id"]
    e2e_env["state"]["session_id"] = body["data"]["session_id"]


def test_15_chat_stream(e2e_env):
    """步骤8b: SSE 流式对话"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    session_id = e2e_env["state"]["session_id"]

    # 意图识别返回 search
    e2e_env["llm_chat_responses"][:] = ["search"]
    e2e_env["llm_chat_call_count"]["i"] = 0

    with client.stream("POST", f"/api/v1/chat/sessions/{session_id}/messages",
                       json={"query": "找一个 Java 工程师"},
                       headers=_auth_header(token)) as response:
        assert response.status_code == 200
        full_text = ""
        for chunk in response.iter_text():
            full_text += chunk

    events = parse_sse_events(full_text)
    event_names = [e["event"] for e in events]
    assert "intent" in event_names
    assert "done" in event_names
    # search 意图应有 retrieval 事件
    assert "retrieval" in event_names


def test_16_get_chat_sessions(e2e_env):
    """步骤8c: 查询会话列表"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/chat/sessions", headers=_auth_header(token))
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["total"] >= 1


def test_17_jd_match(e2e_env):
    """步骤9: JD 匹配候选人"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    e2e_env["llm_chat_responses"][:] = [
        json.dumps({
            "title": "Java 高级工程师",
            "skills": ["Java", "Spring"],
            "work_years_min": 3,
            "salary_max": 30,
        }, ensure_ascii=False),
        "匹配度高，5 年 Java 经验",  # 张三匹配理由
        "匹配度一般，Python 方向",  # 李四匹配理由
    ]
    e2e_env["llm_chat_call_count"]["i"] = 0

    r = client.post("/api/v1/jd", json={
        "jd_text": "招聘 Java 高级工程师，3 年经验，30K 以内",
        "top_k": 5,
    }, headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert "title" in body["data"]["jd"]
    assert "candidates" in body["data"]
    assert len(body["data"]["candidates"]) >= 1
    cand = body["data"]["candidates"][0]
    assert "match_score" in cand
    assert "reason" in cand


def test_18_generate_interview_questions(e2e_env):
    """步骤10a: 生成面试题"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    e2e_env["llm_chat_responses"][:] = [
        json.dumps([
            {"question": "请介绍 Spring Boot 的自动装配原理", "category": "技术"},
            {"question": "讲一个你做过的微服务项目", "category": "项目"},
            {"question": "如何处理团队意见分歧", "category": "行为"},
        ], ensure_ascii=False)
    ]
    e2e_env["llm_chat_call_count"]["i"] = 0

    r = client.post("/api/v1/interview/questions", json={
        "resume_id": "res_demo_zhang",
        "job_title": "Java 高级工程师",
        "count": 3,
    }, headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert len(body["data"]) == 3
    assert body["data"][0]["question"]
    assert "category" in body["data"][0]


def test_19_save_interview_note(e2e_env):
    """步骤10b: 保存面试评价"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.post("/api/v1/interview/notes", json={
        "resume_id": "res_demo_zhang",
        "interviewer": "HR-小李",
        "rating": 4,
        "result": "通过",
        "content": "技术基础扎实，项目经验丰富，推荐进入终面",
    }, headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["note_id"]
    assert body["data"]["rating"] == 4
    e2e_env["state"]["note_id"] = body["data"]["note_id"]


def test_20_get_interview_notes(e2e_env):
    """步骤10c: 查询面试评价列表"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/interview/notes/res_demo_zhang", headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert len(body["data"]) >= 1
    assert body["data"][0]["note_id"] == e2e_env["state"]["note_id"]


def test_21_compare_candidates(e2e_env):
    """步骤11a: 候选人对比（张三 vs 李四）"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.post("/api/v1/candidates/compare", json={
        "candidate_ids": ["cand_zhang", "cand_li"]
    }, headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert len(body["data"]["candidates"]) == 2
    assert "dimensions" in body["data"]
    # 验证对比维度字段
    zhang = next(c for c in body["data"]["candidates"] if c["candidate_id"] == "cand_zhang")
    assert zhang["name"] == "张三"
    assert zhang["work_years"] == 5


def test_22_get_similar(e2e_env):
    """步骤11b: 相似候选人推荐（基于张三）"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/candidates/similar/res_demo_zhang", headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)


def test_23_export_excel(e2e_env):
    """步骤12: 导出 Excel"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.post("/api/v1/candidates/export", json={
        "candidate_ids": ["cand_zhang", "cand_li"],
        "columns": ["name", "education", "work_years", "skills", "expected_salary"],
    }, headers=_auth_header(token))
    assert r.status_code == 200
    # Excel 响应 Content-Type
    assert "spreadsheet" in r.headers.get("content-type", "")
    assert len(r.content) > 0


def test_24_send_email(e2e_env):
    """步骤13: 发送邮件（自定义主题+正文）"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.post("/api/v1/email/send", json={
        "to_email": "boss@talentsense.com",
        "custom_subject": "候选人推荐 - Java 高级工程师",
        "custom_body": "<html><body><p>推荐张三、李四</p></body></html>",
    }, headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "success"
    e2e_env["aiosmtp_send_mock"].assert_called_once()


def test_25_get_email_config(e2e_env):
    """步骤13b: 获取 SMTP 配置（脱敏）"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/email/config", headers=_auth_header(token))
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["smtp_host"] == "smtp.example.com"
    assert body["data"]["smtp_password"] == ""  # 不返回密码


def test_26_dashboard_stats(e2e_env):
    """步骤14: 数据看板统计"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/dashboard/stats", headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["total_resumes"] == 3  # 2 预置 + 1 上传
    assert body["data"]["favorite_count"] == 1  # 张三被收藏
    assert "top_skills" in body["data"]
    assert "education_distribution" in body["data"]
    assert "salary_distribution" in body["data"]


def test_27_resume_preview(e2e_env):
    """步骤15: 生成简历预签名 URL"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/resumes/res_demo_zhang/preview", headers=_auth_header(token))
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["preview_url"]
    assert body["data"]["file_type"] == "pdf"


def test_28_delete_resume(e2e_env):
    """步骤16: 删除简历，验证清理"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    resume_id = e2e_env["state"]["resume_id_wang"]
    r = client.delete(f"/api/v1/resumes/{resume_id}", headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0


def test_29_verify_deleted(e2e_env):
    """步骤16b: 验证简历已删除（列表回到 2 条）"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/resumes", headers=_auth_header(token))
    body = r.json()
    assert body["data"]["total"] == 2


def test_30_delete_chat_session(e2e_env):
    """步骤17: 删除对话会话"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    session_id = e2e_env["state"]["session_id"]
    r = client.delete(f"/api/v1/chat/sessions/{session_id}", headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0


def test_31_unauthorized_access(e2e_env):
    """步骤18: 无 token 访问受保护接口返回 401"""
    client = e2e_env["client"]
    r = client.get("/api/v1/resumes")
    body = r.json()
    assert body["code"] == 1002  # AuthError


def test_32_unified_response_format(e2e_env):
    """步骤19: 验证所有响应包含统一字段 {code, message, data, trace_id}"""
    client = e2e_env["client"]
    token = e2e_env["state"]["token"]
    r = client.get("/api/v1/resumes", headers=_auth_header(token))
    body = r.json()
    for field in ("code", "message", "data", "trace_id"):
        assert field in body, f"响应缺少字段: {field}"
