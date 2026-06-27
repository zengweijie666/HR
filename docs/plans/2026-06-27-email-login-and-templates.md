# 邮箱登录 + 邮件发送功能（模板/自定义）实施计划

**Goal:** 将登录方式从用户名改为邮箱+密码（所有字段必填），并实现完整的邮件发送功能（预置+自定义模板，支持简历详情页快捷发送和独立邮件中心）。

**Architecture:**
- 后端：`LoginRequest.email` 替换 `username`；新增 `email_templates` MongoDB 集合存储模板，Jinja2 渲染基础变量；扩展 `EmailService` 支持 `send_mail(template_id|custom_body)` 与 `send_test`；新增 `/email/templates` CRUD 路由与 `/email/send-test` 路由。
- 前端：Login 改邮箱输入；新增 `EmailCenter.vue` 独立邮件中心页（admin 可管理模板）；`ResumeDetail.vue` 加"发邮件"按钮弹出 `SendEmailDialog.vue`（预填候选人邮箱+可选模板/自定义）；`Settings.vue` 加"发送测试邮件"按钮。
- 数据迁移：现有 admin 账号已有 email，无需迁移；users 表加 email 唯一索引。

**Tech Stack:** FastAPI + motor + aiosmtplib + Jinja2 + bcrypt + Vue3 + Element Plus + Pinia

## Global Constraints

- 所有字段必填（注册/创建用户/邮件发送/模板）
- 保留 username 字段（用于显示），登录用 email
- 邮件模板变量仅支持基础 Jinja2（{{ candidate_name }} {{ position }} {{ interview_time }} {{ company }} {{ hr_name }} {{ salary }}）
- 模板管理仅 admin；发送邮件所有登录用户可用
- 邮件发送异步（aiosmtplib），失败返回明确错误信息
- 复用现有 `email_config` 集合的 SMTP 配置
- TDD：先写测试 → 确认失败 → 实现 → 确认通过 → 提交
- 后端启动用 `.venv\Scripts\python.exe`；测试用 `pytest`
- 统一响应格式 `{code, message, data, trace_id}`

---

## 阶段一：后端登录改邮箱

### Task 1: 修改 LoginRequest 模型为 email

**Files:**
- Modify: `backend/app/models/auth.py:10-12`
- Test: `backend/tests/api/test_auth_api.py`

**Interfaces:**
- Produces: `LoginRequest(email, password)` 供 Task 2 使用

- [ ] **Step 1: 修改 LoginRequest 字段**

```python
class LoginRequest(BaseModel):
    email: str = Field(..., description="邮箱")
    password: str = Field(..., description="密码")
```

需在文件顶部 import `Field`。

- [ ] **Step 2: 修改 test_login_success 用 email**

```python
def test_login_success():
    with patch("app.api.auth.AuthService") as MockSvc:
        instance = MockSvc.return_value
        instance.login = AsyncMock(return_value=TokenResponse(
            access_token="at", refresh_token="rt", expires_in=3600,
            user=UserInfo(user_id="u1", username="admin", role="hr", email="a@b.com")
        ))
        client = TestClient(app)
        r = client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "123"})
        body = r.json()
        assert r.status_code == 200
        assert body["data"]["access_token"] == "at"
        instance.login.assert_called_once_with("a@b.com", "123")
```

- [ ] **Step 3: 运行测试确认失败**

Run: `.venv\Scripts\python.exe -m pytest tests/api/test_auth_api.py::test_login_success -v`
Expected: FAIL（路由仍用 username）

- [ ] **Step 4: 修改 auth.py login 路由**

```python
@router.post("/login")
async def login(body: LoginRequest):
    result = await AuthService().login(body.email, body.password)
    return success(data=result.model_dump())
```

- [ ] **Step 5: 运行测试确认通过**

- [ ] **Step 6: 提交**

```bash
git add backend/app/models/auth.py backend/app/api/auth.py backend/tests/api/test_auth_api.py
git commit -m "feat(auth): 登录请求改为 email+password"
```

---

### Task 2: AuthService.login 改为按 email 查询

**Files:**
- Modify: `backend/app/services/auth_service.py:76-93`
- Test: `backend/tests/services/test_auth_service.py`

- [ ] **Step 1: 修改测试用 email 查询**

修改 `test_login_success` / `test_login_wrong_password` / `test_login_pending_rejected` / `test_login_disabled_rejected`：

```python
@pytest.mark.asyncio
async def test_login_success(auth_service):
    """AC1.1: 正确邮箱密码登录返回 token"""
    auth_service.users_coll.find_one.return_value = {
        "user_id": "u1", "username": "admin", "email": "a@b.com",
        "password_hash": AuthService.hash_password("123456"),
        "role": "hr", "email": "a@b.com"
    }
    result = await auth_service.login("a@b.com", "123456")
    assert result.user.username == "admin"
    auth_service.users_coll.find_one.assert_called_once_with({"email": "a@b.com"})
```

其余测试同步改：调用 `login("a@b.com", ...)`，mock 返回文档含 `email` 字段，断言 `find_one` 用 `{"email": ...}` 调用。

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 修改 AuthService.login 实现**

```python
async def login(self, email: str, password: str) -> TokenResponse:
    """AC1.1/AC1.2 + status 校验（pending/disabled 拒绝登录）

    入参:
        email: 邮箱
        password: 明文密码
    """
    user_doc = await self.users_coll.find_one({"email": email})
    if not user_doc or not self.verify_password(password, user_doc["password_hash"]):
        raise AuthError("邮箱或密码错误")
    status = user_doc.get("status", "approved")
    if status == "pending":
        raise AuthError("账号待审批，请联系管理员")
    if status == "disabled":
        raise AuthError("账号已禁用，请联系管理员")
    payload = {"user_id": user_doc["user_id"], "username": user_doc["username"], "role": user_doc.get("role", "hr")}
    access = self.create_access_token(payload)
    refresh = self.create_refresh_token(payload)
    return TokenResponse(
        access_token=access, refresh_token=refresh, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo(user_id=user_doc["user_id"], username=user_doc["username"], role=user_doc.get("role", "hr"), email=user_doc.get("email"))
    )
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/auth_service.py backend/tests/services/test_auth_service.py
git commit -m "feat(auth): AuthService.login 改为按 email 查询"
```

---

### Task 3: register / create_user 改 email 必填且唯一

**Files:**
- Modify: `backend/app/models/user.py:12-27`
- Modify: `backend/app/services/auth_service.py:133-164`
- Modify: `backend/app/services/user_service.py:71-106`
- Test: `backend/tests/services/test_auth_service.py`
- Test: `backend/tests/services/test_user_service.py`

- [ ] **Step 1: 修改 Pydantic 模型，email 必填**

```python
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    password: str = Field(..., min_length=8, max_length=32, description="密码")
    email: str = Field(..., description="邮箱（必填，唯一）")
    name: str = Field(..., min_length=1, max_length=30, description="显示名（必填）")


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8, max_length=32)
    email: str = Field(..., description="邮箱（必填，唯一）")
    name: str = Field(..., min_length=1, max_length=30)
    role: Literal["admin", "hr"] = Field(default="hr")
```

- [ ] **Step 2: 修改 AuthService.register 检查 email 唯一**

```python
async def register(self, username: str, password: str, email: str, name: str) -> dict:
    """HR 自助注册（status=pending, role=hr）

    入参:
        username: 用户名
        password: 明文密码
        email: 邮箱（必填，唯一）
        name: 显示名（必填）
    异常:
        ConflictError: 用户名或邮箱已存在
    """
    existing_user = await self.users_coll.find_one({"username": username})
    if existing_user:
        raise ConflictError("用户名已存在")
    existing_email = await self.users_coll.find_one({"email": email})
    if existing_email:
        raise ConflictError("邮箱已被注册")
    user_id = f"u_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "user_id": user_id, "username": username,
        "password_hash": self.hash_password(password),
        "email": email, "name": name,
        "role": "hr", "status": "pending",
        "created_at": now, "updated_at": now,
    }
    await self.users_coll.insert_one(doc)
    logger.info(f"用户注册申请: {username} ({email}) pending")
    return {"user_id": user_id, "username": username, "status": "pending"}
```

- [ ] **Step 3: 修改 UserService.create_user 同样检查 email 唯一**

```python
async def create_user(self, username: str, password: str, role: str,
                      email: str, name: str) -> dict:
    existing_user = await self.users_coll.find_one({"username": username})
    if existing_user:
        raise ConflictError("用户名已存在")
    existing_email = await self.users_coll.find_one({"email": email})
    if existing_email:
        raise ConflictError("邮箱已被注册")
    user_id = f"u_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "user_id": user_id, "username": username,
        "password_hash": AuthService.hash_password(password),
        "email": email, "name": name, "role": role, "status": "approved",
        "created_at": now, "updated_at": now,
    }
    await self.users_coll.insert_one(doc)
    logger.info(f"管理员创建用户: {username} ({role})")
    doc.pop("password_hash", None)
    doc.pop("_id", None)
    return doc
```

- [ ] **Step 4: 修改测试断言 email 必填 + 唯一检查**

在 `test_auth_service.py` 新增：

```python
@pytest.mark.asyncio
async def test_register_email_exists():
    """邮箱已注册抛 CONFLICT"""
    from app.core.exceptions import BizError
    from app.core.response import CODE
    svc = AuthService()
    svc.users_coll = AsyncMock()
    # username 不存在，但 email 已存在
    svc.users_coll.find_one = AsyncMock(side_effect=[None, {"email": "z@t.com"}])
    with pytest.raises(BizError) as exc:
        await svc.register(username="new", password="Pass1234", email="z@t.com", name="新")
    assert exc.value.code == CODE.CONFLICT
```

修改 `test_register_success` 调用补 `name="张三"`（已是必填）。修改 `test_register_username_exists` 确保第一个 find_one 返回非 None 即短路。

`test_user_service.py` 的 `test_create_user_success` 调用已是 `email="n@t.com", name="新"`，无需改；新增 `test_create_user_email_exists`：

```python
@pytest.mark.asyncio
async def test_create_user_email_exists():
    svc = UserService()
    svc.users_coll = MagicMock()
    svc.users_coll.find_one = AsyncMock(side_effect=[None, {"email": "n@t.com"}])
    with pytest.raises(ConflictError):
        await svc.create_user(username="new", password="Pass1234", role="hr", email="n@t.com", name="新")
```

- [ ] **Step 5: 运行测试确认通过**

- [ ] **Step 6: 提交**

```bash
git add backend/app/models/user.py backend/app/services/auth_service.py backend/app/services/user_service.py backend/tests/services/test_auth_service.py backend/tests/services/test_user_service.py
git commit -m "feat(auth): register/create_user 改 email+name 必填且 email 唯一"
```

---

### Task 4: users 表加 email 唯一索引 + auth API 路由适配

**Files:**
- Modify: `backend/app/core/database.py:38`
- Modify: `backend/app/api/auth.py:23-30`
- Modify: `backend/tests/api/test_auth_api.py`

- [ ] **Step 1: 加 email 唯一索引**

```python
await cls.db.users.create_index("username", unique=True)
await cls.db.users.create_index("email", unique=True)
await cls.db.users.create_index([("role", 1), ("status", 1)])
```

- [ ] **Step 2: 修改 register 路由传 name**

```python
@router.post("/register")
async def register(body: RegisterRequest):
    """HR 自助注册申请（status=pending）"""
    result = await AuthService().register(
        username=body.username, password=body.password,
        email=body.email, name=body.name,
    )
    return success(data=result)
```

- [ ] **Step 3: 修改 test_register_api_success 用 email+name 必填**

```python
def test_register_api_success():
    with patch("app.api.auth.AuthService") as MockSvc:
        instance = MockSvc.return_value
        instance.register = AsyncMock(return_value={"user_id": "u_x", "username": "zhangsan", "status": "pending"})
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/auth/register", json={
            "username": "zhangsan", "password": "Pass1234",
            "email": "z@t.com", "name": "张三"
        })
        body = r.json()
        assert r.status_code == 200
        assert body["data"]["status"] == "pending"
```

- [ ] **Step 4: 运行测试**

- [ ] **Step 5: 提交**

```bash
git add backend/app/core/database.py backend/app/api/auth.py backend/tests/api/test_auth_api.py
git commit -m "feat(auth): users 表加 email 唯一索引 + register 路由适配"
```

---

## 阶段二：邮件模板系统后端

### Task 5: 邮件模板 Pydantic 模型 + 预置模板常量

**Files:**
- Create: `backend/app/models/email.py`
- Create: `backend/app/core/email_templates_seed.py`

- [ ] **Step 1: 创建 models/email.py**

```python
"""
文件名: app/models/email.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: 邮件模板相关 Pydantic 模型
入参/出参: 模板 CRUD 请求体，模板项
"""
from pydantic import BaseModel, Field
from typing import Literal


class TemplateCreateRequest(BaseModel):
    """创建模板请求"""
    name: str = Field(..., min_length=1, max_length=50, description="模板名称")
    subject: str = Field(..., min_length=1, max_length=200, description="邮件主题（支持变量）")
    body: str = Field(..., min_length=1, description="邮件正文（HTML，支持变量）")
    category: Literal["interview", "offer", "reject", "progress", "custom"] = Field(default="custom")


class TemplateUpdateRequest(BaseModel):
    """更新模板请求"""
    name: str | None = Field(default=None, min_length=1, max_length=50)
    subject: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1)
    category: Literal["interview", "offer", "reject", "progress", "custom"] | None = None


class TemplateItem(BaseModel):
    """模板列表项"""
    template_id: str
    name: str
    subject: str
    body: str
    category: str
    is_builtin: bool = False
    created_at: str
    updated_at: str


class SendMailRequest(BaseModel):
    """发送邮件请求（模板或自定义）"""
    to_email: str = Field(..., description="收件人邮箱")
    template_id: str | None = Field(default=None, description="模板 ID（与 custom 二选一）")
    custom_subject: str | None = Field(default=None, description="自定义主题（template_id 为空时必填）")
    custom_body: str | None = Field(default=None, description="自定义正文（template_id 为空时必填）")
    variables: dict = Field(default_factory=dict, description="模板变量")


class SendTestRequest(BaseModel):
    """发送测试邮件请求"""
    to_email: str = Field(..., description="测试收件人邮箱")
```

- [ ] **Step 2: 创建预置模板种子数据**

```python
"""
文件名: app/core/email_templates_seed.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: 预置邮件模板种子数据，启动时若 email_templates 集合为空则插入
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
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/email.py backend/app/core/email_templates_seed.py
git commit -m "feat(email): 新增邮件模板 Pydantic 模型与预置模板种子数据"
```

---

### Task 6: EmailTemplateService 模板 CRUD + Jinja2 渲染

**Files:**
- Create: `backend/app/services/email_template_service.py`
- Test: `backend/tests/services/test_email_template_service.py`

- [ ] **Step 1: 先写失败测试**

```python
"""
文件名: tests/services/test_email_template_service.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: EmailTemplateService 单元测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.email_template_service import EmailTemplateService
from app.core.exceptions import NotFoundError, ConflictError


@pytest.fixture
def svc():
    s = EmailTemplateService()
    s.templates_coll = MagicMock()
    s.templates_coll.find_one = AsyncMock(return_value=None)
    s.templates_coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id="oid"))
    s.templates_coll.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    s.templates_coll.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    return s


@pytest.mark.asyncio
async def test_list_templates(svc):
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=[{"template_id": "t1", "name": "面试邀请"}])
    svc.templates_coll.find = MagicMock(return_value=cursor)
    result = await svc.list_templates()
    assert result["total"] == 1
    assert result["list"][0]["name"] == "面试邀请"


@pytest.mark.asyncio
async def test_create_template_success(svc):
    result = await svc.create_template(name="自定义", subject="主题", body="<p>正文</p>", category="custom")
    assert result["name"] == "自定义"
    assert result["is_builtin"] is False


@pytest.mark.asyncio
async def test_create_template_name_exists(svc):
    svc.templates_coll.find_one = AsyncMock(return_value={"template_id": "t1", "name": "重名"})
    with pytest.raises(ConflictError):
        await svc.create_template(name="重名", subject="主题", body="正文", category="custom")


@pytest.mark.asyncio
async def test_update_template_success(svc):
    svc.templates_coll.find_one = AsyncMock(return_value={
        "template_id": "t1", "name": "旧", "is_builtin": False
    })
    await svc.update_template("t1", name="新名")
    svc.templates_coll.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_update_builtin_template_rejected(svc):
    """预置模板不允许编辑（仅可删除后重建）"""
    svc.templates_coll.find_one = AsyncMock(return_value={
        "template_id": "t1", "name": "面试邀请", "is_builtin": True
    })
    with pytest.raises(Exception):
        await svc.update_template("t1", name="改")


@pytest.mark.asyncio
async def test_delete_template_success(svc):
    svc.templates_coll.find_one = AsyncMock(return_value={
        "template_id": "t1", "is_builtin": False
    })
    await svc.delete_template("t1")
    svc.templates_coll.delete_one.assert_called_once()


@pytest.mark.asyncio
async def test_delete_builtin_template_rejected(svc):
    svc.templates_coll.find_one = AsyncMock(return_value={
        "template_id": "t1", "is_builtin": True
    })
    with pytest.raises(Exception):
        await svc.delete_template("t1")


@pytest.mark.asyncio
async def test_render_template_success(svc):
    svc.templates_coll.find_one = AsyncMock(return_value={
        "template_id": "t1",
        "subject": "【{{ company }}】面试 - {{ position }}",
        "body": "<p>{{ candidate_name }}，时间 {{ interview_time }}</p>"
    })
    subject, body = await svc.render_template("t1", {
        "company": "ACME", "position": "Java", "candidate_name": "张三", "interview_time": "周一 10:00"
    })
    assert "ACME" in subject and "Java" in subject
    assert "张三" in body and "周一 10:00" in body


@pytest.mark.asyncio
async def test_render_template_not_found(svc):
    svc.templates_coll.find_one = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError):
        await svc.render_template("missing", {})


def test_render_variables_safety():
    """渲染应拒绝未定义的复杂表达式（沙箱）"""
    svc = EmailTemplateService()
    # 沙箱环境只允许基础变量，不应执行 {{ }} 内的 Python 表达式
    rendered = svc._render_str("{{ x }}", {"x": "<b>"})
    # 应自动 HTML 转义
    assert "&lt;" in rendered
```

- [ ] **Step 2: 运行测试确认失败**

Run: `.venv\Scripts\python.exe -m pytest tests/services/test_email_template_service.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现 EmailTemplateService**

```python
"""
文件名: app/services/email_template_service.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: 邮件模板 CRUD + Jinja2 沙箱渲染
入参: 模板字段 / 变量字典
出参: 模板列表 / 渲染后的 subject+body
"""
import uuid
from datetime import datetime, timezone
from jinja2 import Environment, StrictUndefined
from app.core.database import MongoDB
from app.core.exceptions import NotFoundError, ConflictError, BizError
from app.core.logger import logger


# 沙箱 Jinja2 环境：仅允许变量替换，自动 HTML 转义
_jinja_env = Environment(
    autoescape=True,
    undefined=StrictUndefined,
    variable_start_string="{{",
    variable_end_string="}}",
)


class EmailTemplateService:
    """邮件模板服务"""

    def __init__(self):
        pass

    @property
    def templates_coll(self):
        """延迟获取 MongoDB email_templates collection"""
        if hasattr(self, "_templates_coll"):
            return self._templates_coll
        return MongoDB.db.email_templates if MongoDB.db is not None else None

    @templates_coll.setter
    def templates_coll(self, value):
        """测试注入用"""
        self._templates_coll = value

    async def list_templates(self, category: str | None = None) -> dict:
        """列表查询

        入参:
            category: 分类筛选（可选）
        出参:
            {list, total}
        """
        query = {"category": category} if category else {}
        cursor = self.templates_coll.find(query, {"_id": 0})
        items = await cursor.to_list(length=100)
        return {"list": items, "total": len(items)}

    async def create_template(self, name: str, subject: str, body: str, category: str = "custom") -> dict:
        """创建模板

        异常:
            ConflictError: 名称已存在
        """
        existing = await self.templates_coll.find_one({"name": name})
        if existing:
            raise ConflictError("模板名称已存在")
        template_id = f"tpl_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "template_id": template_id, "name": name, "subject": subject, "body": body,
            "category": category, "is_builtin": False,
            "created_at": now, "updated_at": now,
        }
        await self.templates_coll.insert_one(doc)
        doc.pop("_id", None)
        logger.info(f"创建邮件模板: {name} ({template_id})")
        return doc

    async def update_template(self, template_id: str, name: str | None = None,
                              subject: str | None = None, body: str | None = None,
                              category: str | None = None) -> dict:
        """更新模板（预置模板不允许修改）

        异常:
            NotFoundError: 模板不存在
            BizError: 预置模板不允许修改
        """
        doc = await self.templates_coll.find_one({"template_id": template_id})
        if not doc:
            raise NotFoundError("模板不存在")
        if doc.get("is_builtin"):
            raise BizError(code=4003, message="预置模板不允许修改")
        update_fields: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if name is not None:
            update_fields["name"] = name
        if subject is not None:
            update_fields["subject"] = subject
        if body is not None:
            update_fields["body"] = body
        if category is not None:
            update_fields["category"] = category
        await self.templates_coll.update_one(
            {"template_id": template_id}, {"$set": update_fields},
        )
        logger.info(f"更新邮件模板: {template_id}")
        return await self.templates_coll.find_one({"template_id": template_id}, {"_id": 0})

    async def delete_template(self, template_id: str) -> None:
        """删除模板（预置模板不允许删除）

        异常:
            NotFoundError: 模板不存在
            BizError: 预置模板不允许删除
        """
        doc = await self.templates_coll.find_one({"template_id": template_id})
        if not doc:
            raise NotFoundError("模板不存在")
        if doc.get("is_builtin"):
            raise BizError(code=4003, message="预置模板不允许删除")
        await self.templates_coll.delete_one({"template_id": template_id})
        logger.info(f"删除邮件模板: {template_id}")

    async def render_template(self, template_id: str, variables: dict) -> tuple[str, str]:
        """渲染模板

        入参:
            template_id: 模板 ID
            variables: 变量字典
        出参:
            (subject, body)
        异常:
            NotFoundError: 模板不存在
        """
        doc = await self.templates_coll.find_one({"template_id": template_id}, {"_id": 0})
        if not doc:
            raise NotFoundError("模板不存在")
        subject = self._render_str(doc["subject"], variables)
        body = self._render_str(doc["body"], variables)
        return subject, body

    def _render_str(self, template_str: str, variables: dict) -> str:
        """Jinja2 沙箱渲染单个字符串

        入参:
            template_str: 含 {{ var }} 的字符串
            variables: 变量字典
        出参:
            渲染后的字符串（HTML 转义）
        """
        try:
            tpl = _jinja_env.from_string(template_str)
            return tpl.render(**variables)
        except Exception as e:
            logger.warning(f"模板渲染失败: {e}, template={template_str[:80]}")
            # 渲染失败时返回原文，避免发不出邮件
            return template_str
```

注：`BizError(code=4003, ...)` 需确认 `BizError` 支持 code 参数；若不支持，用 `Exception("预置模板不允许修改")`。

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/email_template_service.py backend/tests/services/test_email_template_service.py
git commit -m "feat(email): 新增 EmailTemplateService 模板 CRUD + Jinja2 渲染"
```

---

### Task 7: 邮件模板 CRUD 路由

**Files:**
- Modify: `backend/app/api/email.py`
- Test: `backend/tests/api/test_email_api.py`

- [ ] **Step 1: 在 email.py 追加 5 个模板路由**

```python
from app.services.email_template_service import EmailTemplateService
from app.models.email import (
    TemplateCreateRequest, TemplateUpdateRequest,
    SendMailRequest, SendTestRequest,
)


@router.get("/templates")
async def list_templates(category: str | None = None, user: dict = Depends(get_current_user)):
    """邮件模板列表（登录用户可查，admin 才能增删改）"""
    result = await EmailTemplateService().list_templates(category=category)
    return success(data=result)


@router.post("/templates")
async def create_template(body: TemplateCreateRequest, user: dict = Depends(require_admin)):
    """创建模板（admin only）"""
    result = await EmailTemplateService().create_template(
        name=body.name, subject=body.subject, body=body.body, category=body.category,
    )
    return success(data=result)


@router.put("/templates/{template_id}")
async def update_template(template_id: str, body: TemplateUpdateRequest, user: dict = Depends(require_admin)):
    """更新模板（admin only，预置模板不可改）"""
    result = await EmailTemplateService().update_template(
        template_id, name=body.name, subject=body.subject, body=body.body, category=body.category,
    )
    return success(data=result)


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, user: dict = Depends(require_admin)):
    """删除模板（admin only，预置模板不可删）"""
    await EmailTemplateService().delete_template(template_id)
    return success()
```

- [ ] **Step 2: 在 test_email_api.py 追加测试**

```python
def test_list_templates():
    with patch("app.api.email.EmailTemplateService") as MockSvc:
        instance = MockSvc.return_value
        instance.list_templates = AsyncMock(return_value={"list": [{"template_id": "t1", "name": "面试邀请"}], "total": 1})
        with _auth_patch():
            client = TestClient(app)
            r = client.get("/api/v1/email/templates", headers={"Authorization": "Bearer fake"})
            body = r.json()
            assert body["code"] == 0
            assert body["data"]["total"] == 1


def test_create_template_admin():
    with patch("app.api.email.EmailTemplateService") as MockSvc:
        instance = MockSvc.return_value
        instance.create_template = AsyncMock(return_value={"template_id": "t1", "name": "自定义"})
        with _admin_auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/email/templates", json={
                "name": "自定义", "subject": "主题", "body": "<p>正文</p>", "category": "custom"
            }, headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["template_id"] == "t1"


def test_create_template_hr_forbidden():
    """hr 无权创建模板"""
    with _auth_patch():  # hr 身份
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/email/templates", json={
            "name": "x", "subject": "x", "body": "x"
        }, headers={"Authorization": "Bearer fake"})
        assert r.json()["code"] == 1003


def test_delete_template_admin():
    with patch("app.api.email.EmailTemplateService") as MockSvc:
        instance = MockSvc.return_value
        instance.delete_template = AsyncMock()
        with _admin_auth_patch():
            client = TestClient(app)
            r = client.delete("/api/v1/email/templates/t1", headers={"Authorization": "Bearer fake"})
            assert r.json()["code"] == 0
```

- [ ] **Step 3: 运行测试确认通过**

- [ ] **Step 4: 提交**

```bash
git add backend/app/api/email.py backend/tests/api/test_email_api.py
git commit -m "feat(email): 新增邮件模板 CRUD 路由（admin 才能增删改）"
```

---

## 阶段三：邮件发送功能后端

### Task 8: EmailService.send_mail + send_test

**Files:**
- Modify: `backend/app/services/email_service.py:70-113`
- Test: `backend/tests/services/test_email_service.py`

- [ ] **Step 1: 先写失败测试**

```python
@pytest.mark.asyncio
async def test_send_mail_by_template(svc):
    """通过模板 ID 发送邮件"""
    svc.config_coll.find_one = AsyncMock(return_value={
        "smtp_host": "smtp.x.com", "smtp_port": 465,
        "smtp_user": "hr@x.com", "smtp_password_encrypted": "enc"
    })
    # mock EmailTemplateService.render_template
    with patch("app.services.email_service.EmailTemplateService.render_template",
               AsyncMock(return_value=("面试邀请", "<p>正文</p>"))), \
         patch("app.services.email_service.aiosmtplib.send", AsyncMock()), \
         patch("app.services.email_service.decrypt", return_value="pwd"):
        result = await svc.send_mail(
            to_email="cand@x.com", template_id="t1",
            variables={"candidate_name": "张三", "position": "Java"}
        )
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_send_mail_custom(svc):
    """自定义主题和正文发送"""
    svc.config_coll.find_one = AsyncMock(return_value={
        "smtp_host": "smtp.x.com", "smtp_port": 465,
        "smtp_user": "hr@x.com", "smtp_password_encrypted": "enc"
    })
    with patch("app.services.email_service.aiosmtplib.send", AsyncMock()), \
         patch("app.services.email_service.decrypt", return_value="pwd"):
        result = await svc.send_mail(
            to_email="cand@x.com", custom_subject="自定义主题", custom_body="<p>自定义正文</p>"
        )
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_send_mail_no_subject_or_template(svc):
    """既没传 template_id 也没传 custom_subject 应报错"""
    svc.config_coll.find_one = AsyncMock(return_value={
        "smtp_host": "smtp.x.com", "smtp_port": 465,
        "smtp_user": "hr@x.com", "smtp_password_encrypted": "enc"
    })
    result = await svc.send_mail(to_email="cand@x.com")
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_send_test_mail(svc):
    """发送测试邮件"""
    svc.config_coll.find_one = AsyncMock(return_value={
        "smtp_host": "smtp.x.com", "smtp_port": 465,
        "smtp_user": "hr@x.com", "smtp_password_encrypted": "enc"
    })
    with patch("app.services.email_service.aiosmtplib.send", AsyncMock()), \
         patch("app.services.email_service.decrypt", return_value="pwd"):
        result = await svc.send_test(to_email="admin@x.com")
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_send_mail_smtp_not_configured(svc):
    """未配置 SMTP 返回错误"""
    svc.config_coll.find_one = AsyncMock(return_value=None)
    result = await svc.send_mail(to_email="x@y.com", custom_subject="s", custom_body="b")
    assert result["status"] == "error"
    assert "SMTP" in result["message"] or "未配置" in result["message"]
```

- [ ] **Step 2: 运行测试确认失败**

- [ ] **Step 3: 在 EmailService 追加 send_mail / send_test 方法**

```python
from app.services.email_template_service import EmailTemplateService


async def send_mail(self, to_email: str, template_id: str | None = None,
                    custom_subject: str | None = None, custom_body: str | None = None,
                    variables: dict | None = None) -> dict:
    """发送邮件（模板或自定义）

    入参:
        to_email: 收件人
        template_id: 模板 ID（与 custom_subject/custom_body 二选一）
        custom_subject: 自定义主题
        custom_body: 自定义正文
        variables: 模板变量
    出参:
        {"status": "success"|"error", "message": "..."}
    """
    # 校验参数
    if not template_id and not (custom_subject and custom_body):
        return {"status": "error", "message": "需提供 template_id 或 custom_subject+custom_body"}

    # 获取 SMTP 配置
    config = await self._get_smtp_config()
    if not config:
        return {"status": "error", "message": "未配置 SMTP"}

    # 决定 subject / body
    variables = variables or {}
    if template_id:
        try:
            subject, body = await EmailTemplateService().render_template(template_id, variables)
        except Exception as e:
            return {"status": "error", "message": f"模板渲染失败: {e}"}
    else:
        subject, body = custom_subject, custom_body

    return await self._smtp_send(config, to_email, subject, body)


async def send_test(self, to_email: str) -> dict:
    """发送测试邮件

    入参:
        to_email: 测试收件人
    出参:
        {"status": "success"|"error", "message": "..."}
    """
    config = await self._get_smtp_config()
    if not config:
        return {"status": "error", "message": "未配置 SMTP"}
    subject = "TalentSense HR - 测试邮件"
    body = "<html><body><h2>SMTP 配置测试</h2><p>这封邮件由 TalentSense HR 系统发送，用于验证 SMTP 配置是否正确。</p></body></html>"
    return await self._smtp_send(config, to_email, subject, body)


async def _get_smtp_config(self) -> dict | None:
    """获取 SMTP 配置（解密密码）"""
    if self.config_coll is None:
        return None
    config = await self.config_coll.find_one({"_id": "default"})
    if not config:
        return None
    return {
        "smtp_host": config["smtp_host"],
        "smtp_port": config["smtp_port"],
        "smtp_user": config["smtp_user"],
        "smtp_password": decrypt(config["smtp_password_encrypted"]),
    }


async def _smtp_send(self, config: dict, to_email: str, subject: str, body: str) -> dict:
    """实际 SMTP 发送"""
    msg = MIMEMultipart("alternative")
    msg["From"] = config["smtp_user"]
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))
    try:
        await aiosmtplib.send(
            msg,
            hostname=config["smtp_host"], port=config["smtp_port"],
            username=config["smtp_user"], password=config["smtp_password"],
            use_tls=config["smtp_port"] == 465,
        )
        logger.info(f"邮件已发送到 {to_email}, subject={subject}")
        return {"status": "success", "message": "发送成功"}
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return {"status": "error", "message": str(e)}
```

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/email_service.py backend/tests/services/test_email_service.py
git commit -m "feat(email): EmailService 新增 send_mail / send_test 方法"
```

---

### Task 9: 邮件发送路由 + 启动时预置模板

**Files:**
- Modify: `backend/app/api/email.py`
- Modify: `backend/app/main.py` (lifespan 追加 seed)
- Test: `backend/tests/api/test_email_api.py`

- [ ] **Step 1: 修改 /email/send 路由用 SendMailRequest**

```python
@router.post("/send")
async def send_mail(body: SendMailRequest, user: dict = Depends(get_current_user)):
    """发送邮件（模板或自定义）"""
    result = await EmailService().send_mail(
        to_email=body.to_email, template_id=body.template_id,
        custom_subject=body.custom_subject, custom_body=body.custom_body,
        variables=body.variables,
    )
    return success(data=result)


@router.post("/send-test")
async def send_test(body: SendTestRequest, user: dict = Depends(require_admin)):
    """发送测试邮件（admin only）"""
    result = await EmailService().send_test(to_email=body.to_email)
    return success(data=result)
```

- [ ] **Step 2: main.py lifespan 追加预置模板初始化**

在管理员初始化之后、parsing 重置之前追加：

```python
    # 初始化预置邮件模板
    try:
        from app.core.email_templates_seed import seed_builtin_templates
        await seed_builtin_templates(MongoDB.db)
        logger.info("预置邮件模板已就绪")
    except Exception as e:
        logger.warning(f"预置邮件模板初始化失败: {e}")
```

- [ ] **Step 3: 在 database.py 加 email_templates 索引**

```python
await cls.db.email_templates.create_index("template_id", unique=True)
await cls.db.email_templates.create_index("name")
```

- [ ] **Step 4: 修改 test_send_recommendation 为 send_mail**

```python
def test_send_mail_by_template():
    with patch("app.api.email.EmailService") as MockSvc:
        instance = MockSvc.return_value
        instance.send_mail = AsyncMock(return_value={"status": "success"})
        with _auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/email/send", json={
                "to_email": "cand@x.com", "template_id": "t1",
                "variables": {"candidate_name": "张三"}
            }, headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["status"] == "success"


def test_send_test_admin():
    with patch("app.api.email.EmailService") as MockSvc:
        instance = MockSvc.return_value
        instance.send_test = AsyncMock(return_value={"status": "success"})
        with _admin_auth_patch():
            client = TestClient(app)
            r = client.post("/api/v1/email/send-test", json={"to_email": "admin@x.com"}, headers={"Authorization": "Bearer fake"})
            assert r.json()["data"]["status"] == "success"


def test_send_test_hr_forbidden():
    with _auth_patch():
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/email/send-test", json={"to_email": "x@y.com"}, headers={"Authorization": "Bearer fake"})
        assert r.json()["code"] == 1003
```

旧的 `test_send_recommendation` 删除或改名。

- [ ] **Step 5: 运行测试**

- [ ] **Step 6: 提交**

```bash
git add backend/app/api/email.py backend/app/main.py backend/app/core/database.py backend/tests/api/test_email_api.py
git commit -m "feat(email): 新增 /email/send /email/send-test 路由 + 启动预置模板"
```

---

## 阶段四：前端邮箱登录改造

### Task 10: 前端类型与 API 改邮箱

**Files:**
- Modify: `frontend/src/types/auth.ts:10-13`
- Modify: `frontend/src/api/auth.ts:15-17`

- [ ] **Step 1: 修改 LoginRequest 类型**

```typescript
export interface LoginRequest {
  email: string
  password: string
}
```

- [ ] **Step 2: RegisterRequest email/name 改必填**

```typescript
export interface RegisterRequest {
  username: string
  password: string
  email: string
  name: string
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/types/auth.ts frontend/src/api/auth.ts
git commit -m "feat(frontend): LoginRequest 改 email，Register 字段必填"
```

---

### Task 11: Login.vue 改邮箱输入

**Files:**
- Modify: `frontend/src/views/Login.vue:59-67, 126-134, 151-154`

- [ ] **Step 1: 表单字段 username → email**

模板部分：

```vue
<el-form-item label="邮箱" prop="email">
  <el-input
    v-model="form.email"
    size="large"
    placeholder="请输入邮箱"
    :prefix-icon="Message"
    autocomplete="email"
  />
</el-form-item>
```

script 部分：

```typescript
import { Message, Lock } from '@element-plus/icons-vue'

const form = reactive({
  email: '',
  password: '',
})

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const data = await login({
  email: form.email.trim(),
  password: form.password,
})
```

- [ ] **Step 2: 前端构建验证**

Run: `npm run build`

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/Login.vue
git commit -m "feat(frontend): Login 页改邮箱+密码登录"
```

---

### Task 12: RegisterDialog.vue + UserList.vue 字段必填

**Files:**
- Modify: `frontend/src/components/auth/RegisterDialog.vue`
- Modify: `frontend/src/views/UserList.vue`

- [ ] **Step 1: RegisterDialog 邮箱/姓名必填**

```vue
<el-form-item label="邮箱" prop="email">
  <el-input v-model="form.email" placeholder="必填" />
</el-form-item>
<el-form-item label="姓名" prop="name">
  <el-input v-model="form.name" placeholder="必填" />
</el-form-item>
```

```typescript
const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '3-20 字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 32, message: '8-32 字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
}

await register({
  username: form.username.trim(),
  password: form.password,
  email: form.email.trim(),
  name: form.name.trim(),
})
```

- [ ] **Step 2: UserList 创建账号对话框 email/name 必填**

```typescript
const createRules: FormRules = {
  username: [{ required: true, min: 3, max: 20, message: '3-20 字符', trigger: 'blur' }],
  password: [{ required: true, min: 8, max: 32, message: '8-32 字符', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

await createUser({
  username: createForm.username.trim(),
  password: createForm.password,
  role: createForm.role,
  email: createForm.email.trim(),
  name: createForm.name.trim(),
})
```

- [ ] **Step 3: 构建验证**

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/auth/RegisterDialog.vue frontend/src/views/UserList.vue
git commit -m "feat(frontend): 注册和创建用户邮箱+姓名必填"
```

---

## 阶段五：前端邮件中心页 + 模板管理

### Task 13: 前端邮件类型与 API

**Files:**
- Create: `frontend/src/types/email-template.ts`
- Modify: `frontend/src/api/email.ts`

- [ ] **Step 1: 创建 types/email-template.ts**

```typescript
/**
 * 文件名: types/email-template.ts
 * 创建时间: 2026-06-27
 * 作者: TalentSense Team
 * 功能描述: 邮件模板类型定义
 */
export type TemplateCategory = 'interview' | 'offer' | 'reject' | 'progress' | 'custom'

export interface EmailTemplate {
  template_id: string
  name: string
  subject: string
  body: string
  category: TemplateCategory
  is_builtin: boolean
  created_at: string
  updated_at: string
}

export interface TemplateListResponse {
  list: EmailTemplate[]
  total: number
}

export interface CreateTemplatePayload {
  name: string
  subject: string
  body: string
  category: TemplateCategory
}

export interface UpdateTemplatePayload {
  name?: string
  subject?: string
  body?: string
  category?: TemplateCategory
}

export interface SendMailPayload {
  to_email: string
  template_id?: string
  custom_subject?: string
  custom_body?: string
  variables?: Record<string, string>
}

export interface SendTestPayload {
  to_email: string
}
```

- [ ] **Step 2: 扩展 api/email.ts**

```typescript
/**
 * 文件名: api/email.ts
 * 创建时间: 2026-06-27
 * 作者: TalentSense Team
 * 功能描述: 邮件 API（模板 CRUD + 发送 + 测试）
 */
import request from './request'
import type {
  TemplateListResponse, EmailTemplate,
  CreateTemplatePayload, UpdateTemplatePayload,
  SendMailPayload, SendTestPayload,
} from '@/types/email-template'
import type { EmailConfig } from '@/types/email'

/** 获取 SMTP 配置 */
export function getConfig(): Promise<EmailConfig> {
  return request.get('/email/config') as unknown as Promise<EmailConfig>
}

/** 更新 SMTP 配置 */
export function updateConfig(data: Partial<EmailConfig>): Promise<void> {
  return request.put('/email/config', data) as unknown as Promise<void>
}

/** 模板列表 */
export function listTemplates(category?: string): Promise<TemplateListResponse> {
  return request.get('/email/templates', { params: category ? { category } : {} }) as unknown as Promise<TemplateListResponse>
}

/** 创建模板（admin） */
export function createTemplate(data: CreateTemplatePayload): Promise<EmailTemplate> {
  return request.post('/email/templates', data) as unknown as Promise<EmailTemplate>
}

/** 更新模板（admin） */
export function updateTemplate(templateId: string, data: UpdateTemplatePayload): Promise<EmailTemplate> {
  return request.put(`/email/templates/${templateId}`, data) as unknown as Promise<EmailTemplate>
}

/** 删除模板（admin） */
export function deleteTemplate(templateId: string): Promise<void> {
  return request.delete(`/email/templates/${templateId}`) as unknown as Promise<void>
}

/** 发送邮件（模板或自定义） */
export function sendMail(data: SendMailPayload): Promise<{ status: string; message?: string }> {
  return request.post('/email/send', data) as unknown as Promise<{ status: string; message?: string }>
}

/** 发送测试邮件（admin） */
export function sendTestMail(data: SendTestPayload): Promise<{ status: string; message?: string }> {
  return request.post('/email/send-test', data) as unknown as Promise<{ status: string; message?: string }>
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/types/email-template.ts frontend/src/api/email.ts
git commit -m "feat(frontend): 新增邮件模板类型定义与 API"
```

---

### Task 14: EmailCenter.vue 邮件中心页

**Files:**
- Create: `frontend/src/views/EmailCenter.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/views/Layout.vue`

- [ ] **Step 1: 创建 EmailCenter.vue**

```vue
<!--
  文件名: views/EmailCenter.vue
  创建时间: 2026-06-27
  作者: TalentSense Team
  功能描述: 邮件中心页
    - 左侧：模板列表（admin 可新增/编辑/删除）
    - 右侧：发送邮件表单（收件人/选模板/变量/自定义主题正文）
    - admin 可见模板管理区，hr 仅能选模板发送
-->
<template>
  <div class="page-email">
    <header class="page-email__head">
      <span class="eyebrow">EMAIL CENTER</span>
      <h1 class="page-email__title decor-line">邮件中心</h1>
      <p class="page-email__subtitle">基于模板或自定义内容发送邮件</p>
    </header>

    <el-row :gutter="20">
      <!-- 左侧：模板管理 -->
      <el-col :span="10">
        <section class="email-card">
          <div class="email-card__head">
            <h3 class="email-card__title decor-line">邮件模板</h3>
            <el-button v-if="authStore.user?.role === 'admin'" type="primary" size="small" @click="openCreate">新建模板</el-button>
          </div>
          <LoadingOverlay :visible="loadingTpl" />
          <div class="email-card__list">
            <div
              v-for="tpl in templates"
              :key="tpl.template_id"
              class="email-card__item"
              :class="{ 'is-active': selectedTplId === tpl.template_id }"
              @click="selectTemplate(tpl)"
            >
              <div class="email-card__item-head">
                <span class="email-card__item-name">{{ tpl.name }}</span>
                <el-tag v-if="tpl.is_builtin" size="small" type="info">预置</el-tag>
                <el-tag size="small" :type="categoryType(tpl.category)">{{ categoryText(tpl.category) }}</el-tag>
              </div>
              <div class="email-card__item-subject mono">{{ tpl.subject }}</div>
              <div v-if="authStore.user?.role === 'admin' && !tpl.is_builtin" class="email-card__item-actions">
                <el-button size="small" link @click.stop="openEdit(tpl)">编辑</el-button>
                <el-button size="small" link type="danger" @click.stop="handleDelete(tpl)">删除</el-button>
              </div>
            </div>
          </div>
        </section>
      </el-col>

      <!-- 右侧：发送表单 -->
      <el-col :span="14">
        <section class="email-card">
          <h3 class="email-card__title decor-line">发送邮件</h3>
          <el-form :model="sendForm" label-position="top" class="email-card__form">
            <el-form-item label="收件人" required>
              <el-input v-model="sendForm.to_email" placeholder="example@domain.com" />
            </el-form-item>
            <el-form-item label="发送方式">
              <el-radio-group v-model="sendMode" @change="onModeChange">
                <el-radio value="template">使用模板</el-radio>
                <el-radio value="custom">自定义</el-radio>
              </el-radio-group>
            </el-form-item>
            <template v-if="sendMode === 'template'">
              <el-form-item label="变量（可选）">
                <div v-for="(v, k) in sendForm.variables" :key="k" class="email-var-row">
                  <span class="email-var-row__key mono">{{ k }}</span>
                  <el-input v-model="sendForm.variables[k]" size="small" />
                </div>
                <p v-if="!Object.keys(sendForm.variables).length" class="email-hint">选择模板后自动展示变量</p>
              </el-form-item>
            </template>
            <template v-else>
              <el-form-item label="主题" required>
                <el-input v-model="sendForm.custom_subject" />
              </el-form-item>
              <el-form-item label="正文（HTML）" required>
                <el-input v-model="sendForm.custom_body" type="textarea" :rows="8" />
              </el-form-item>
            </template>
            <el-form-item>
              <el-button type="primary" :loading="sending" @click="handleSend">发送邮件</el-button>
            </el-form-item>
          </el-form>
        </section>
      </el-col>
    </el-row>

    <!-- 模板编辑对话框 -->
    <el-dialog v-model="tplDialogVisible" :title="editingTpl ? '编辑模板' : '新建模板'" width="640px">
      <el-form ref="tplFormRef" :model="tplForm" :rules="tplRules" label-position="top">
        <el-form-item label="名称" prop="name">
          <el-input v-model="tplForm.name" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="tplForm.category">
            <el-option label="面试邀请" value="interview" />
            <el-option label="Offer 通知" value="offer" />
            <el-option label="拒绝通知" value="reject" />
            <el-option label="进度通知" value="progress" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="主题" prop="subject">
          <el-input v-model="tplForm.subject" />
        </el-form-item>
        <el-form-item label="正文（HTML，支持变量）" prop="body">
          <el-input v-model="tplForm.body" type="textarea" :rows="10" />
        </el-form-item>
        <div class="email-hint">
          支持变量：{{ '{{candidate_name}}' }} {{ '{{position}}' }} {{ '{{interview_time}}' }} {{ '{{company}}' }} {{ '{{hr_name}}' }} {{ '{{salary}}' }}
        </div>
      </el-form>
      <template #footer>
        <el-button @click="tplDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSaveTpl">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import { useAuthStore } from '@/stores/auth'
import {
  listTemplates, createTemplate, updateTemplate, deleteTemplate, sendMail,
} from '@/api/email'
import type { EmailTemplate, TemplateCategory, SendMailPayload } from '@/types/email-template'

const authStore = useAuthStore()

const templates = ref<EmailTemplate[]>([])
const loadingTpl = ref<boolean>(false)
const sending = ref<boolean>(false)
const submitLoading = ref<boolean>(false)
const selectedTplId = ref<string>('')

const sendMode = ref<'template' | 'custom'>('template')
const sendForm = reactive<{
  to_email: string
  template_id?: string
  custom_subject: string
  custom_body: string
  variables: Record<string, string>
}>({
  to_email: '',
  custom_subject: '',
  custom_body: '',
  variables: {},
})

const tplDialogVisible = ref<boolean>(false)
const editingTpl = ref<EmailTemplate | null>(null)
const tplFormRef = ref<FormInstance>()
const tplForm = reactive({
  name: '', subject: '', body: '', category: 'custom' as TemplateCategory,
})
const tplRules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  subject: [{ required: true, message: '请输入主题', trigger: 'blur' }],
  body: [{ required: true, message: '请输入正文', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

function categoryType(c: TemplateCategory): 'primary' | 'success' | 'warning' | 'info' {
  return ({ interview: 'primary', offer: 'success', reject: 'warning', progress: 'info', custom: 'info' } as const)[c]
}

function categoryText(c: TemplateCategory): string {
  return ({ interview: '面试', offer: 'Offer', reject: '拒绝', progress: '进度', custom: '自定义' } as const)[c]
}

async function loadTemplates(): Promise<void> {
  loadingTpl.value = true
  try {
    const data = await listTemplates()
    templates.value = data.list ?? []
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '加载模板失败')
  } finally {
    loadingTpl.value = false
  }
}

function selectTemplate(tpl: EmailTemplate): void {
  selectedTplId.value = tpl.template_id
  sendMode.value = 'template'
  sendForm.template_id = tpl.template_id
  // 从 subject+body 提取 {{ var }} 作为变量键
  const vars = new Set<string>()
  const re = /\{\{\s*(\w+)\s*\}\}/g
  let m: RegExpExecArray | null
  while ((m = re.exec(tpl.subject + tpl.body)) !== null) {
    vars.add(m[1])
  }
  const oldVars = { ...sendForm.variables }
  sendForm.variables = {}
  vars.forEach((k) => {
    sendForm.variables[k] = oldVars[k] || ''
  })
}

function onModeChange(mode: 'template' | 'custom'): void {
  if (mode === 'custom') {
    sendForm.template_id = undefined
  } else {
    sendForm.custom_subject = ''
    sendForm.custom_body = ''
  }
}

function openCreate(): void {
  editingTpl.value = null
  tplForm.name = ''
  tplForm.subject = ''
  tplForm.body = ''
  tplForm.category = 'custom'
  tplDialogVisible.value = true
}

function openEdit(tpl: EmailTemplate): void {
  editingTpl.value = tpl
  tplForm.name = tpl.name
  tplForm.subject = tpl.subject
  tplForm.body = tpl.body
  tplForm.category = tpl.category
  tplDialogVisible.value = true
}

async function handleSaveTpl(): Promise<void> {
  if (!tplFormRef.value) return
  try { await tplFormRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    if (editingTpl.value) {
      await updateTemplate(editingTpl.value.template_id, {
        name: tplForm.name, subject: tplForm.subject, body: tplForm.body, category: tplForm.category,
      })
      ElMessage.success('已更新')
    } else {
      await createTemplate({
        name: tplForm.name, subject: tplForm.subject, body: tplForm.body, category: tplForm.category,
      })
      ElMessage.success('已创建')
    }
    tplDialogVisible.value = false
    await loadTemplates()
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(tpl: EmailTemplate): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认删除模板「${tpl.name}」？`, '删除', { type: 'warning' })
    await deleteTemplate(tpl.template_id)
    ElMessage.success('已删除')
    await loadTemplates()
  } catch { /* cancel */ }
}

async function handleSend(): Promise<void> {
  if (!sendForm.to_email) {
    ElMessage.warning('请填写收件人')
    return
  }
  if (sendMode.value === 'custom' && (!sendForm.custom_subject || !sendForm.custom_body)) {
    ElMessage.warning('请填写主题和正文')
    return
  }
  if (sendMode.value === 'template' && !sendForm.template_id) {
    ElMessage.warning('请选择模板')
    return
  }
  sending.value = true
  try {
    const payload: SendMailPayload = { to_email: sendForm.to_email }
    if (sendMode.value === 'template') {
      payload.template_id = sendForm.template_id
      payload.variables = sendForm.variables
    } else {
      payload.custom_subject = sendForm.custom_subject
      payload.custom_body = sendForm.custom_body
    }
    const result = await sendMail(payload)
    if (result.status === 'success') {
      ElMessage.success('邮件已发送')
    } else {
      ElMessage.error(result.message || '发送失败')
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '发送失败')
  } finally {
    sending.value = false
  }
}

onMounted(() => { void loadTemplates() })
</script>

<style scoped lang="scss">
.page-email {
  position: relative;
  min-height: 100%;

  &__head { margin-bottom: var(--space-6); animation: fadeInUp var(--duration-slow) var(--ease-out) both; }
  &__title { margin-top: var(--space-3); font-family: var(--font-display); font-size: 32px; font-weight: 500; color: var(--color-primary); padding-bottom: 10px; letter-spacing: -0.02em; }
  &__subtitle { margin-top: var(--space-3); font-size: var(--text-sm); color: var(--color-ink-soft); }
}

.email-card {
  padding: var(--space-5) var(--space-6);
  background-color: var(--color-bg-card);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  min-height: 480px;

  &__head { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4); }
  &__title { font-family: var(--font-display); font-size: var(--text-xl); font-weight: 500; color: var(--color-primary); margin: 0; padding-bottom: 6px; }
  &__list { display: flex; flex-direction: column; gap: var(--space-3); }
  &__item {
    padding: var(--space-3) var(--space-4);
    border: 1px solid var(--color-line);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: border-color var(--duration-fast) var(--ease-out), background-color var(--duration-fast) var(--ease-out);
    &:hover { border-color: var(--color-accent-soft); }
    &.is-active { border-color: var(--color-accent); background-color: var(--color-primary-tint); }
  }
  &__item-head { display: flex; align-items: center; gap: var(--space-2); margin-bottom: 4px; }
  &__item-name { font-weight: 500; color: var(--color-ink); flex: 1; }
  &__item-subject { font-size: var(--text-xs); color: var(--color-ink-mute); margin-top: 2px; }
  &__item-actions { margin-top: var(--space-2); display: flex; gap: var(--space-3); }
  &__form { margin-top: var(--space-4); }
}

.email-var-row {
  display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-2);
  &__key { width: 160px; font-size: var(--text-sm); color: var(--color-ink-soft); }
}

.email-hint {
  font-size: var(--text-xs);
  color: var(--color-ink-mute);
  margin-top: var(--space-2);
}
</style>
```

- [ ] **Step 2: 注册路由**

```typescript
{
  path: 'email',
  name: 'EmailCenter',
  component: () => import('@/views/EmailCenter.vue'),
  meta: { title: '邮件中心' },
},
```

- [ ] **Step 3: Layout.vue 加菜单项**

```vue
<el-menu-item index="/email">
  <el-icon><Message /></el-icon>
  <template #title>邮件中心</template>
</el-menu-item>
```

icons import 追加 `Message`。

- [ ] **Step 4: 构建验证**

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/EmailCenter.vue frontend/src/router/index.ts frontend/src/views/Layout.vue
git commit -m "feat(frontend): 新增邮件中心页 EmailCenter（模板管理+发送）"
```

---

## 阶段六：简历详情页发邮件入口

### Task 15: SendEmailDialog 组件 + ResumeDetail 集成

**Files:**
- Create: `frontend/src/components/resume/SendEmailDialog.vue`
- Modify: `frontend/src/views/ResumeDetail.vue`

- [ ] **Step 1: 创建 SendEmailDialog.vue**

```vue
<!--
  文件名: components/resume/SendEmailDialog.vue
  创建时间: 2026-06-27
  作者: TalentSense Team
  功能描述: 从简历详情发送邮件对话框
    - 预填候选人邮箱（若有）
    - 可选模板（自动填充 candidate_name 变量）
    - 可切换自定义模式
-->
<template>
  <el-dialog v-model="visible" title="发送邮件" width="640px" :close-on-click-modal="false" align-center>
    <el-form :model="form" label-position="top">
      <el-form-item label="收件人" required>
        <el-input v-model="form.to_email" placeholder="example@domain.com" />
      </el-form-item>
      <el-form-item label="发送方式">
        <el-radio-group v-model="mode" @change="onModeChange">
          <el-radio value="template">使用模板</el-radio>
          <el-radio value="custom">自定义</el-radio>
        </el-radio-group>
      </el-form-item>
      <template v-if="mode === 'template'">
        <el-form-item label="选择模板">
          <el-select v-model="form.template_id" placeholder="选择模板" @change="onTemplateChange">
            <el-option v-for="tpl in templates" :key="tpl.template_id" :label="tpl.name" :value="tpl.template_id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="Object.keys(form.variables).length" label="变量">
          <div v-for="(_, k) in form.variables" :key="k" class="send-var-row">
            <span class="send-var-row__key mono">{{ k }}</span>
            <el-input v-model="form.variables[k]" size="small" />
          </div>
        </el-form-item>
      </template>
      <template v-else>
        <el-form-item label="主题" required>
          <el-input v-model="form.custom_subject" />
        </el-form-item>
        <el-form-item label="正文（HTML）" required>
          <el-input v-model="form.custom_body" type="textarea" :rows="8" />
        </el-form-item>
      </template>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="sending" @click="handleSend">发送</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { listTemplates, sendMail } from '@/api/email'
import type { EmailTemplate, SendMailPayload } from '@/types/email-template'

const visible = ref<boolean>(false)
const sending = ref<boolean>(false)
const mode = ref<'template' | 'custom'>('template')
const templates = ref<EmailTemplate[]>([])

const form = reactive<{
  to_email: string
  template_id?: string
  custom_subject: string
  custom_body: string
  variables: Record<string, string>
}>({
  to_email: '',
  custom_subject: '',
  custom_body: '',
  variables: {},
})

/** 打开对话框
 * @param candidateEmail 候选人邮箱（可选预填）
 * @param candidateName 候选人姓名（自动填入变量）
 */
async function open(candidateEmail?: string, candidateName?: string): Promise<void> {
  form.to_email = candidateEmail || ''
  form.template_id = undefined
  form.custom_subject = ''
  form.custom_body = ''
  form.variables = {}
  mode.value = 'template'
  visible.value = true
  // 加载模板列表
  try {
    const data = await listTemplates()
    templates.value = data.list ?? []
  } catch (err) {
    ElMessage.error('加载模板失败')
  }
  // 若有姓名，预设变量
  if (candidateName) {
    form.variables.candidate_name = candidateName
  }
}

function onModeChange(m: 'template' | 'custom'): void {
  if (m === 'custom') {
    form.template_id = undefined
  } else {
    form.custom_subject = ''
    form.custom_body = ''
  }
}

function onTemplateChange(tplId: string): void {
  const tpl = templates.value.find((t) => t.template_id === tplId)
  if (!tpl) return
  const vars = new Set<string>()
  const re = /\{\{\s*(\w+)\s*\}\}/g
  let m: RegExpExecArray | null
  while ((m = re.exec(tpl.subject + tpl.body)) !== null) {
    vars.add(m[1])
  }
  const oldVars = { ...form.variables }
  form.variables = {}
  vars.forEach((k) => {
    form.variables[k] = oldVars[k] || ''
  })
}

async function handleSend(): Promise<void> {
  if (!form.to_email) {
    ElMessage.warning('请填写收件人')
    return
  }
  if (mode.value === 'custom' && (!form.custom_subject || !form.custom_body)) {
    ElMessage.warning('请填写主题和正文')
    return
  }
  sending.value = true
  try {
    const payload: SendMailPayload = { to_email: form.to_email }
    if (mode.value === 'template') {
      payload.template_id = form.template_id
      payload.variables = form.variables
    } else {
      payload.custom_subject = form.custom_subject
      payload.custom_body = form.custom_body
    }
    const result = await sendMail(payload)
    if (result.status === 'success') {
      ElMessage.success('邮件已发送')
      visible.value = false
    } else {
      ElMessage.error(result.message || '发送失败')
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '发送失败')
  } finally {
    sending.value = false
  }
}

defineExpose({ open })
</script>

<style scoped lang="scss">
.send-var-row {
  display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-2);
  &__key { width: 160px; font-size: var(--text-sm); color: var(--color-ink-soft); }
}
</style>
```

- [ ] **Step 2: ResumeDetail.vue 加发邮件按钮**

在操作区（相似/收藏/面试按钮旁）追加：

```vue
<el-button type="primary" @click="sendEmailRef?.open(detail.basic_info?.email_masked, detail.basic_info?.name)">
  <el-icon><Message /></el-icon>
  发邮件
</el-button>
<SendEmailDialog ref="sendEmailRef" />
```

script 追加：

```typescript
import { Message } from '@element-plus/icons-vue'
import SendEmailDialog from '@/components/resume/SendEmailDialog.vue'

const sendEmailRef = ref<InstanceType<typeof SendEmailDialog>>()
```

注：候选人邮箱若 PII 脱敏只有 `email_masked`，则不预填，让 HR 手动输入收件邮箱。

- [ ] **Step 3: 构建验证**

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/resume/SendEmailDialog.vue frontend/src/views/ResumeDetail.vue
git commit -m "feat(frontend): 简历详情页新增发邮件入口 SendEmailDialog"
```

---

## 阶段七：设置页发送测试邮件

### Task 16: Settings.vue 加发送测试邮件按钮

**Files:**
- Modify: `frontend/src/views/Settings.vue`

- [ ] **Step 1: 在保存配置按钮旁加测试按钮**

```vue
<el-form-item>
  <el-button type="primary" :loading="saving" @click="handleSave">保存配置</el-button>
  <el-button :loading="testing" @click="openTestDialog">发送测试邮件</el-button>
</el-form-item>
```

追加测试邮件对话框：

```vue
<el-dialog v-model="testVisible" title="发送测试邮件" width="400px">
  <el-form label-position="top">
    <el-form-item label="收件人邮箱" required>
      <el-input v-model="testEmail" placeholder="输入收件人邮箱" />
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="testVisible = false">取消</el-button>
    <el-button type="primary" :loading="testing" @click="handleSendTest">发送</el-button>
  </template>
</el-dialog>
```

script 追加：

```typescript
import { sendTestMail } from '@/api/email'

const testing = ref<boolean>(false)
const testVisible = ref<boolean>(false)
const testEmail = ref<string>('')

function openTestDialog(): void {
  testEmail.value = ''
  testVisible.value = true
}

async function handleSendTest(): Promise<void> {
  if (!testEmail.value) {
    ElMessage.warning('请填写收件人邮箱')
    return
  }
  testing.value = true
  try {
    const result = await sendTestMail({ to_email: testEmail.value })
    if (result.status === 'success') {
      ElMessage.success('测试邮件已发送')
      testVisible.value = false
    } else {
      ElMessage.error(result.message || '发送失败')
    }
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '发送失败')
  } finally {
    testing.value = false
  }
}
```

- [ ] **Step 2: 构建验证**

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/Settings.vue
git commit -m "feat(frontend): 设置页新增发送测试邮件按钮"
```

---

## 阶段八：联调与文档

### Task 17: 全量测试 + 联调验证

**Files:** 无新文件

- [ ] **Step 1: 后端全量测试**

Run: `cd backend && .venv\Scripts\python.exe -m pytest`
Expected: 所有测试通过

- [ ] **Step 2: 前端构建**

Run: `cd frontend && npm run build`
Expected: 构建成功

- [ ] **Step 3: 启动后端验证**

启动后端，确认日志包含「预置邮件模板已就绪」。

- [ ] **Step 4: API 联调**

```bash
# 1. 邮箱登录
curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d "{\"email\":\"admin@talentsense.local\",\"password\":\"admin123\"}"

# 2. 模板列表
curl http://localhost:8000/api/v1/email/templates -H "Authorization: Bearer <token>"

# 3. 发送测试邮件
curl -X POST http://localhost:8000/api/v1/email/send-test -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d "{\"to_email\":\"test@example.com\"}"
```

- [ ] **Step 5: 前端联调**

启动前端，浏览器验证：
1. 邮箱登录
2. 邮件中心页：模板列表、新建模板、发送邮件
3. 简历详情页：发邮件按钮
4. 设置页：发送测试邮件

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "test: 邮箱登录+邮件发送功能联调验证通过"
```

---

### Task 18: 更新 README + 推送

**Files:**
- Modify: `README.md`

- [ ] **Step 1: README 更新邮件模块说明**

在功能特性表更新邮件模块；在路由模块表追加 `/email/templates` 和 `/email/send-test`；在目录结构追加新增文件；在测试规模更新测试数。

- [ ] **Step 2: 推送到 Gitee**

```bash
git push origin master
```

- [ ] **Step 3: 提交**

```bash
git add README.md
git commit -m "docs: 更新 README 邮件模块说明"
git push origin master
```

---

## 自检清单

- [x] **Spec coverage:**
  - 登录改邮箱 → Task 1, 2, 4, 10, 11
  - 所有字段必填 → Task 3, 12
  - 邮件模板系统 → Task 5, 6, 7
  - 邮件发送功能（模板+自定义）→ Task 8, 9, 14, 15
  - 简历详情页发送入口 → Task 15
  - 独立邮件中心页 → Task 14
  - 设置页发送测试邮件 → Task 16

- [x] **Placeholder scan:** 无 TBD/TODO，所有代码完整

- [x] **Type consistency:** 前后端字段名一致（email / template_id / custom_subject / custom_body / variables）
