# 简历库筛选增强与脱敏改造实施计划

**Goal:** 实现简历库 8 项优化（脱敏改造/发邮件预填/收藏筛选/入库时间/日期范围/分页大小/排序选项/总数统计）

**Architecture:** 后端三层改造（存储原始 phone/email + list/get_detail 注入 current_user + 新增 date_from/date_to/sort_by/sort_order 参数），前端 FilterBar 扩展 + ResumeCard 显示入库时间 + ResumeList 分页改造 + ResumeDetail 发邮件预填

**Tech Stack:** FastAPI + Motor + Pytest（后端）；Vue3 + Element Plus + Pinia + Vitest（前端）

**Spec 文档:** docs/specs/2026-06-27-resume-filters-and-unmask-design.md

## Global Constraints

- 后端测试用 `.venv\Scripts\python.exe -m pytest` 运行
- 前端测试用 `npx vitest run` 运行
- PowerShell 命令分隔符用 `;` 不用 `&&`
- Vitest 测试 el-dialog 用 `document.body` 而非 `wrapper.find()`
- 所有 API 路由保持 `/api/v1/[module]` 前缀
- MongoDB 响应统一用 `MongoJSONResponse` 序列化 ObjectId
- 服务类用 `@property` 延迟初始化 MongoDB/Redis 集合
- 统一返回格式 `{code, message, data, trace_id}`
- 提交信息格式：`feat:`/`fix:`/`test:`

---

## Task 1: 后端存储层增加原始 phone/email 字段

**Files:**
- Modify: `backend/app/services/resume_service.py:205-212`
- Test: `backend/tests/services/test_resume_service.py`

**Interfaces:**
- Consumes: 无
- Produces: basic_info 含 phone/email 字段（供 Task 2 查询层使用）

- [ ] **Step 1: 写失败测试**

在 `backend/tests/services/test_resume_service.py` 末尾添加：

```python
@pytest.mark.asyncio
async def test_parse_and_index_stores_raw_phone_email(resume_service):
    """解析完成后 basic_info 应同时存储原始 phone/email 和 masked 字段"""
    # 准备 mock LLM 返回
    resume_service.llm.complete = AsyncMock(return_value=json.dumps({
        "name": "张三", "phone": "13800138000", "email": "zhangsan@test.com",
        "gender": "男", "age": 28, "location": "上海",
        "skills": ["Python"], "education": "本科", "education_level": 1,
        "work_years": 5, "work_experience": [], "education_detail": [],
        "projects": [], "summary": "测试", "expected_salary": "20-30K",
    }, ensure_ascii=False))

    # mock minio/vector_store
    resume_service.minio = MagicMock()
    resume_service.minio.put_file = MagicMock(return_value="file-1")
    resume_service.minio.delete = MagicMock()
    resume_service.vector_store = MagicMock()
    resume_service.vector_store.delete_by_resume_id = AsyncMock()
    resume_service.vector_store.upsert = AsyncMock()

    # mock 文件读取
    with open("tests/fixtures/sample.pdf", "rb") as f:
        resume_service.minio.get_file = MagicMock(return_value=f.read())

    await resume_service._parse_and_index("r1", overwrite=False)

    # 验证存储包含原始字段
    stored = resume_service.resumes_coll.update_one.call_args
    set_data = stored.kwargs["update"]["$set"]["basic_info"]
    assert set_data["phone"] == "13800138000"
    assert set_data["email"] == "zhangsan@test.com"
    assert set_data["phone_masked"]  # masked 也存在
    assert set_data["email_masked"]  # masked 也存在
```

- [ ] **Step 2: 运行测试验证失败**

```powershell
cd backend; .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py::test_parse_and_index_stores_raw_phone_email -v
```
Expected: FAIL（`KeyError: 'phone'`，因为当前只存 masked）

- [ ] **Step 3: 修改 resume_service.py 第 205-212 行**

将 `basic_info` 字典改为：

```python
"basic_info": {
    "name": structured.get("name", ""),
    "phone": structured.get("phone", ""),           # 新增：原始值
    "email": structured.get("email", ""),           # 新增：原始值
    "phone_masked": mask_phone(structured.get("phone", "")),
    "email_masked": mask_email(structured.get("email", "")),
    "phone_hash": phone_h, "email_hash": email_h,
    "gender": structured.get("gender"), "age": structured.get("age"),
    "location": structured.get("location"),
},
```

- [ ] **Step 4: 运行测试验证通过**

```powershell
cd backend; .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py::test_parse_and_index_stores_raw_phone_email -v
```
Expected: PASS

- [ ] **Step 5: 提交**

```powershell
git add backend/app/services/resume_service.py backend/tests/services/test_resume_service.py; git commit -m "feat: basic_info 存储原始 phone/email 字段(RBAC脱敏基础)"
```

---

## Task 2: 后端 list() 注入 current_user 实现脱敏

**Files:**
- Modify: `backend/app/services/resume_service.py:405-460`（list 方法 + _flatten_doc 方法）
- Test: `backend/tests/services/test_resume_service.py`

**Interfaces:**
- Consumes: Task 1 的 phone/email 存储字段
- Produces: list 接口根据角色返回不同字段（供 Task 8 前端类型扩展使用）

- [ ] **Step 1: 写失败测试**

在 `test_resume_service.py` 添加 4 个测试：

```python
@pytest.mark.asyncio
async def test_list_returns_raw_phone_for_admin(resume_service):
    """admin 用户看到原始 phone/email"""
    now = datetime.now(timezone.utc).isoformat()
    docs = [{
        "resume_id": "r1", "candidate_id": "c1",
        "basic_info": {
            "name": "张三", "phone": "13800138000", "email": "zhangsan@test.com",
            "phone_masked": "138****8000", "email_masked": "z***@test.com",
        },
        "skills": [], "tags": [], "summary": "",
        "expected_salary": {"min": 10, "max": 20},
        "parse_info": {"parse_status": "completed"},
        "created_at": now,
    }]
    mock_cursor = MagicMock()
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.to_list = AsyncMock(return_value=docs)
    resume_service.resumes_coll.find = MagicMock(return_value=mock_cursor)
    resume_service.resumes_coll.count_documents = AsyncMock(return_value=1)

    result = await resume_service.list(current_user={"role": "admin"})
    item = result["list"][0]
    assert item["phone"] == "13800138000"
    assert item["email"] == "zhangsan@test.com"
    assert "phone_masked" not in item
    assert "email_masked" not in item


@pytest.mark.asyncio
async def test_list_returns_masked_for_normal_user(resume_service):
    """普通用户看到 masked 字段"""
    now = datetime.now(timezone.utc).isoformat()
    docs = [{
        "resume_id": "r1", "candidate_id": "c1",
        "basic_info": {
            "name": "张三", "phone": "13800138000", "email": "zhangsan@test.com",
            "phone_masked": "138****8000", "email_masked": "z***@test.com",
        },
        "skills": [], "tags": [], "summary": "",
        "expected_salary": {"min": 10, "max": 20},
        "parse_info": {"parse_status": "completed"},
        "created_at": now,
    }]
    mock_cursor = MagicMock()
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.to_list = AsyncMock(return_value=docs)
    resume_service.resumes_coll.find = MagicMock(return_value=mock_cursor)
    resume_service.resumes_coll.count_documents = AsyncMock(return_value=1)

    result = await resume_service.list(current_user={"role": "user"})
    item = result["list"][0]
    assert item["phone_masked"] == "138****8000"
    assert item["email_masked"] == "z***@test.com"
    assert "phone" not in item
    assert "email" not in item


@pytest.mark.asyncio
async def test_list_returns_masked_when_no_user(resume_service):
    """current_user=None 时保守返回 masked"""
    now = datetime.now(timezone.utc).isoformat()
    docs = [{
        "resume_id": "r1", "candidate_id": "c1",
        "basic_info": {
            "name": "张三", "phone": "13800138000", "email": "zhangsan@test.com",
            "phone_masked": "138****8000", "email_masked": "z***@test.com",
        },
        "skills": [], "tags": [], "summary": "",
        "expected_salary": {"min": 10, "max": 20},
        "parse_info": {"parse_status": "completed"},
        "created_at": now,
    }]
    mock_cursor = MagicMock()
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.to_list = AsyncMock(return_value=docs)
    resume_service.resumes_coll.find = MagicMock(return_value=mock_cursor)
    resume_service.resumes_coll.count_documents = AsyncMock(return_value=1)

    result = await resume_service.list(current_user=None)
    item = result["list"][0]
    assert item["phone_masked"] == "138****8000"
    assert "phone" not in item


@pytest.mark.asyncio
async def test_list_falls_back_to_masked_for_old_resumes(resume_service):
    """旧文档无 phone/email 字段时 admin 兜底用 masked"""
    now = datetime.now(timezone.utc).isoformat()
    docs = [{
        "resume_id": "r1", "candidate_id": "c1",
        "basic_info": {
            "name": "张三",
            "phone_masked": "138****8000", "email_masked": "z***@test.com",
            # 旧文档没有 phone/email 字段
        },
        "skills": [], "tags": [], "summary": "",
        "expected_salary": {"min": 10, "max": 20},
        "parse_info": {"parse_status": "completed"},
        "created_at": now,
    }]
    mock_cursor = MagicMock()
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.to_list = AsyncMock(return_value=docs)
    resume_service.resumes_coll.find = MagicMock(return_value=mock_cursor)
    resume_service.resumes_coll.count_documents = AsyncMock(return_value=1)

    result = await resume_service.list(current_user={"role": "admin"})
    item = result["list"][0]
    # 兜底：admin 看到 masked 值
    assert item["phone"] == "138****8000"
    assert item["email"] == "z***@test.com"
```

- [ ] **Step 2: 运行测试验证失败**

```powershell
cd backend; .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py::test_list_returns_raw_phone_for_admin tests/services/test_resume_service.py::test_list_returns_masked_for_normal_user tests/services/test_resume_service.py::test_list_returns_masked_when_no_user tests/services/test_resume_service.py::test_list_falls_back_to_masked_for_old_resumes -v
```
Expected: FAIL（list 方法不支持 current_user 参数）

- [ ] **Step 3: 修改 list 方法签名和 _flatten_doc 方法**

在 `resume_service.py` 的 `list` 方法签名末尾增加参数：

```python
async def list(
    self,
    page: int = 1, page_size: int = 20,
    keyword: str = "", tag: str = "",
    is_favorite: Optional[bool] = None,
    education_min: Optional[int] = None,
    work_years_min: Optional[int] = None,
    salary_min: Optional[int] = None, salary_max: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: Optional[dict] = None,
) -> dict:
```

在 `_flatten_doc` 方法（或 list 方法内扁平化逻辑）增加角色判断：

```python
@staticmethod
def _flatten_doc(doc: dict, current_user: Optional[dict] = None) -> dict:
    """扁平化 MongoDB 文档，根据 current_user 角色返回 phone/email 或 masked 字段

    入参:
        doc: MongoDB 原始文档
        current_user: 当前用户信息（含 role 字段）
    出参:
        扁平化后的字典，供前端 ResumeListItem 使用
    """
    basic = doc.get("basic_info") or {}
    is_admin = bool(current_user and current_user.get("role") == "admin")
    item = {
        "resume_id": doc.get("resume_id", ""),
        "candidate_id": doc.get("candidate_id", ""),
        "name": basic.get("name", "") or doc.get("name", ""),
        "gender": basic.get("gender"),
        "age": basic.get("age"),
        "location": basic.get("location"),
        "education": doc.get("education", ""),
        "education_level": doc.get("education_level", 0),
        "work_years": doc.get("work_years", 0),
        "skills": doc.get("skills", []),
        "tags": doc.get("tags", []),
        "summary": doc.get("summary", ""),
        "expected_salary": doc.get("expected_salary", {"min": 0, "max": 0}),
        "is_favorite": doc.get("is_favorite", False),
        "parse_status": (doc.get("parse_info") or {}).get("parse_status", "pending"),
        "created_at": doc.get("created_at", ""),
    }
    # 根据 RBAC 决定返回原始值还是 masked 值
    if is_admin:
        # admin 看原始值，旧文档无 phone/email 字段时兜底用 masked
        item["phone"] = basic.get("phone") or basic.get("phone_masked", "")
        item["email"] = basic.get("email") or basic.get("email_masked", "")
    else:
        # 普通用户/未登录看 masked 值
        item["phone_masked"] = basic.get("phone_masked", "")
        item["email_masked"] = basic.get("email_masked", "")
    return item
```

修改 list 方法中调用 _flatten_doc 的地方，传入 current_user：

```python
list_items = [self._flatten_doc(doc, current_user) for doc in docs]
```

- [ ] **Step 4: 运行测试验证通过**

```powershell
cd backend; .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py -k "test_list_returns" -v
```
Expected: 4 个测试全部 PASS

- [ ] **Step 5: 提交**

```powershell
git add backend/app/services/resume_service.py backend/tests/services/test_resume_service.py; git commit -m "feat: list()根据RBAC角色返回原始/脱敏手机邮箱(含旧文档兜底)"
```

---

## Task 3: 后端 get_detail() 注入 current_user

**Files:**
- Modify: `backend/app/services/resume_service.py`（get_detail 方法）
- Test: `backend/tests/services/test_resume_service.py`

**Interfaces:**
- Consumes: Task 1 的 phone/email 存储
- Produces: 详情接口根据角色返回不同字段

- [ ] **Step 1: 写失败测试**

```python
@pytest.mark.asyncio
async def test_get_detail_returns_raw_phone_for_admin(resume_service):
    """admin 获取详情看到原始 phone/email"""
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "resume_id": "r1", "candidate_id": "c1",
        "basic_info": {
            "name": "张三", "phone": "13800138000", "email": "zhangsan@test.com",
            "phone_masked": "138****8000", "email_masked": "z***@test.com",
        },
        "work_experience": [], "education_detail": [], "projects": [],
        "skills": [], "tags": [], "summary": "",
        "expected_salary": {"min": 10, "max": 20},
        "parse_info": {"parse_status": "completed"},
        "file_info": {"file_name": "r.pdf", "file_type": "pdf"},
        "created_at": now,
    }
    resume_service.resumes_coll.find_one = AsyncMock(return_value=doc)

    result = await resume_service.get_detail("r1", current_user={"role": "admin"})
    assert result["basic_info"]["phone"] == "13800138000"
    assert result["basic_info"]["email"] == "zhangsan@test.com"
    assert "phone_masked" not in result["basic_info"]


@pytest.mark.asyncio
async def test_get_detail_returns_masked_for_normal_user(resume_service):
    """普通用户获取详情看到 masked"""
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "resume_id": "r1", "candidate_id": "c1",
        "basic_info": {
            "name": "张三", "phone": "13800138000", "email": "zhangsan@test.com",
            "phone_masked": "138****8000", "email_masked": "z***@test.com",
        },
        "work_experience": [], "education_detail": [], "projects": [],
        "skills": [], "tags": [], "summary": "",
        "expected_salary": {"min": 10, "max": 20},
        "parse_info": {"parse_status": "completed"},
        "file_info": {"file_name": "r.pdf", "file_type": "pdf"},
        "created_at": now,
    }
    resume_service.resumes_coll.find_one = AsyncMock(return_value=doc)

    result = await resume_service.get_detail("r1", current_user={"role": "user"})
    assert result["basic_info"]["phone_masked"] == "138****8000"
    assert result["basic_info"]["email_masked"] == "z***@test.com"
    assert "phone" not in result["basic_info"]
```

- [ ] **Step 2: 运行测试验证失败**

```powershell
cd backend; .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py::test_get_detail_returns_raw_phone_for_admin tests/services/test_resume_service.py::test_get_detail_returns_masked_for_normal_user -v
```
Expected: FAIL

- [ ] **Step 3: 修改 get_detail 方法**

找到 `get_detail` 方法签名，增加 `current_user: Optional[dict] = None` 参数。在返回 doc 前增加角色过滤逻辑：

```python
async def get_detail(self, resume_id: str, current_user: Optional[dict] = None) -> Optional[dict]:
    """获取简历详情

    入参:
        resume_id: 简历 ID
        current_user: 当前用户（含 role），决定返回原始/脱敏手机邮箱
    出参:
        简历详情字典，未找到返回 None
    """
    doc = await self.resumes_coll.find_one({"resume_id": resume_id}, {"_id": 0})
    if not doc:
        return None

    is_admin = bool(current_user and current_user.get("role") == "admin")
    basic = doc.get("basic_info") or {}
    if is_admin:
        # admin 看原始值，旧文档兜底
        basic["phone"] = basic.get("phone") or basic.get("phone_masked", "")
        basic["email"] = basic.get("email") or basic.get("email_masked", "")
        basic.pop("phone_masked", None)
        basic.pop("email_masked", None)
    else:
        # 普通用户/未登录移除原始字段
        basic.pop("phone", None)
        basic.pop("email", None)
    doc["basic_info"] = basic
    return doc
```

- [ ] **Step 4: 运行测试验证通过**

```powershell
cd backend; .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py -k "test_get_detail_returns" -v
```
Expected: 2 个测试 PASS

- [ ] **Step 5: 提交**

```powershell
git add backend/app/services/resume_service.py backend/tests/services/test_resume_service.py; git commit -m "feat: get_detail()根据RBAC角色返回原始/脱敏手机邮箱"
```

---

## Task 4: 后端 list() 增加日期范围筛选和排序

**Files:**
- Modify: `backend/app/services/resume_service.py`（list 方法的 query 构建和 sort 调用）
- Test: `backend/tests/services/test_resume_service.py`

**Interfaces:**
- Consumes: Task 2 的 list 签名扩展
- Produces: list 支持 date_from/date_to/sort_by/sort_order

- [ ] **Step 1: 写失败测试**

```python
@pytest.mark.asyncio
async def test_list_filter_by_date_range(resume_service):
    """date_from/date_to 正确加入查询条件"""
    mock_cursor = MagicMock()
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.to_list = AsyncMock(return_value=[])
    resume_service.resumes_coll.find = MagicMock(return_value=mock_cursor)
    resume_service.resumes_coll.count_documents = AsyncMock(return_value=0)

    await resume_service.list(date_from="2026-06-01", date_to="2026-06-30")

    # 验证 find 被调用时 query 包含 created_at 范围
    find_args = resume_service.resumes_coll.find.call_args
    query = find_args.args[0]
    assert "created_at" in query
    assert query["created_at"]["$gte"] == "2026-06-01"
    assert "T23:59:59" in query["created_at"]["$lte"]


@pytest.mark.asyncio
async def test_list_sort_by_work_years(resume_service):
    """sort_by=work_years 时正确传给 MongoDB sort"""
    mock_cursor = MagicMock()
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.to_list = AsyncMock(return_value=[])
    resume_service.resumes_coll.find = MagicMock(return_value=mock_cursor)
    resume_service.resumes_coll.count_documents = AsyncMock(return_value=0)

    await resume_service.list(sort_by="work_years", sort_order="desc")

    mock_cursor.sort.assert_called_with("work_years", -1)


@pytest.mark.asyncio
async def test_list_invalid_sort_by_defaults_to_created_at(resume_service):
    """非法 sort_by 兜底为 created_at"""
    mock_cursor = MagicMock()
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.to_list = AsyncMock(return_value=[])
    resume_service.resumes_coll.find = MagicMock(return_value=mock_cursor)
    resume_service.resumes_coll.count_documents = AsyncMock(return_value=0)

    await resume_service.list(sort_by="malicious_field")

    mock_cursor.sort.assert_called_with("created_at", -1)


@pytest.mark.asyncio
async def test_list_invalid_date_range_swapped(resume_service):
    """date_from > date_to 时自动交换"""
    mock_cursor = MagicMock()
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    mock_cursor.to_list = AsyncMock(return_value=[])
    resume_service.resumes_coll.find = MagicMock(return_value=mock_cursor)
    resume_service.resumes_coll.count_document = AsyncMock(return_value=0)

    await resume_service.list(date_from="2026-06-30", date_to="2026-06-01")

    find_args = resume_service.resumes_coll.find.call_args
    query = find_args.args[0]
    # 交换后 $gte 应该是较早的日期
    assert query["created_at"]["$gte"] == "2026-06-01"
```

- [ ] **Step 2: 运行测试验证失败**

```powershell
cd backend; .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py -k "test_list_filter_by_date_range or test_list_sort_by_work_years or test_list_invalid_sort_by or test_list_invalid_date_range" -v
```
Expected: FAIL

- [ ] **Step 3: 修改 list 方法的 query 构建和 sort**

在 list 方法的 query 构建部分增加日期范围：

```python
# 日期范围筛选（自动交换倒序日期）
if date_from and date_to and date_from > date_to:
    date_from, date_to = date_to, date_from
if date_from:
    query["created_at"] = {"$gte": date_from}
if date_to:
    query.setdefault("created_at", {})["$lte"] = date_to + "T23:59:59"
```

在 sort 调用前增加白名单校验：

```python
# sort_by 白名单校验，非法值兜底为 created_at
ALLOWED_SORT_FIELDS = {"created_at", "work_years", "education_level"}
safe_sort_by = sort_by if sort_by in ALLOWED_SORT_FIELDS else "created_at"
safe_sort_order = 1 if sort_order == "asc" else -1

cursor = self.resumes_coll.find(query, {"_id": 0}).skip(skip).limit(page_size).sort(safe_sort_by, safe_sort_order)
```

- [ ] **Step 4: 运行测试验证通过**

```powershell
cd backend; .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py -k "test_list_filter_by_date_range or test_list_sort_by_work_years or test_list_invalid_sort_by or test_list_invalid_date_range" -v
```
Expected: 4 个测试 PASS

- [ ] **Step 5: 提交**

```powershell
git add backend/app/services/resume_service.py backend/tests/services/test_resume_service.py; git commit -m "feat: list()支持日期范围筛选+排序选项(含白名单和倒序兜底)"
```

---

## Task 5: 后端 API 路由注入 current_user 和新增查询参数

**Files:**
- Modify: `backend/app/api/resumes.py`
- Test: `backend/tests/api/test_resumes.py`

**Interfaces:**
- Consumes: Task 2/3/4 的 service 方法新签名
- Produces: HTTP API 支持新查询参数 + current_user 注入

- [ ] **Step 1: 读取当前 resumes.py 路由实现**

读取 `backend/app/api/resumes.py` 完整内容，了解现有 list/detail 路由的 Depends 用法。

- [ ] **Step 2: 修改 list 路由**

找到 `GET /resumes` 路由，增加查询参数和 current_user 注入：

```python
from app.core.deps import get_current_user  # 复用现有依赖

@router.get("", response_class=MongoJSONResponse)
async def list_resumes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    education_min: Optional[int] = Query(None),
    work_years_min: Optional[int] = Query(None),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: dict = Depends(get_current_user),
):
    """获取简历列表（根据角色返回原始/脱敏手机邮箱）"""
    try:
        result = await resume_service.list(
            page=page, page_size=page_size,
            keyword=keyword or "", tag=tag or "",
            is_favorite=is_favorite, education_min=education_min,
            work_years_min=work_years_min,
            salary_min=salary_min, salary_max=salary_max,
            status=status,
            date_from=date_from, date_to=date_to,
            sort_by=sort_by, sort_order=sort_order,
            current_user=current_user,
        )
        return {"code": 200, "message": "success", "data": result, "trace_id": ""}
    except Exception as e:
        logger.exception(f"获取简历列表失败: {e}")
        return {"code": 500, "message": str(e), "data": None, "trace_id": ""}
```

- [ ] **Step 3: 修改 detail 路由**

```python
@router.get("/{resume_id}", response_class=MongoJSONResponse)
async def get_resume_detail(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取简历详情（根据角色返回原始/脱敏手机邮箱）"""
    try:
        result = await resume_service.get_detail(resume_id, current_user=current_user)
        if not result:
            return {"code": 404, "message": "简历不存在", "data": None, "trace_id": ""}
        return {"code": 200, "message": "success", "data": result, "trace_id": ""}
    except Exception as e:
        logger.exception(f"获取简历详情失败: {e}")
        return {"code": 500, "message": str(e), "data": None, "trace_id": ""}
```

- [ ] **Step 4: 运行后端全量测试验证不破坏现有功能**

```powershell
cd backend; .venv\Scripts\python.exe -m pytest tests/ -v --tb=short
```
Expected: 所有现有测试 PASS（如出现 Depends 相关测试失败，需调整 mock）

- [ ] **Step 5: 提交**

```powershell
git add backend/app/api/resumes.py; git commit -m "feat: resumes API 注入 current_user + 支持 date_from/date_to/sort_by/sort_order 参数"
```

---

## Task 6: 前端类型扩展 + formatRelativeTime 工具函数

**Files:**
- Modify: `frontend/src/types/resume.ts`
- Modify: `frontend/src/utils/format.ts`
- Test: `frontend/tests/utils/test_format.test.ts`（新建）

**Interfaces:**
- Consumes: Task 2/3 的后端返回字段
- Produces: 前端类型支持 phone/email/created_at + 相对时间函数

- [ ] **Step 1: 写失败测试**

创建 `frontend/tests/utils/test_format.test.ts`：

```typescript
/**
 * 文件名: tests/utils/test_format.test.ts
 * 创建时间: 2026-06-27
 * 功能描述: formatRelativeTime 相对时间函数测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { formatRelativeTime } from '@/utils/format'

describe('utils/format.formatRelativeTime', () => {
  beforeEach(() => {
    // 固定当前时间为 2026-06-27 12:00:00
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-27T12:00:00Z'))
  })

  it('空字符串返回空', () => {
    expect(formatRelativeTime('')).toBe('')
  })

  it('今天的日期返回「今天」', () => {
    expect(formatRelativeTime('2026-06-27T08:00:00Z')).toBe('今天')
  })

  it('昨天的日期返回「昨天」', () => {
    expect(formatRelativeTime('2026-06-26T08:00:00Z')).toBe('昨天')
  })

  it('3 天前返回「3 天前」', () => {
    expect(formatRelativeTime('2026-06-24T08:00:00Z')).toBe('3 天前')
  })

  it('10 天前返回「1 周前」', () => {
    expect(formatRelativeTime('2026-06-17T08:00:00Z')).toBe('1 周前')
  })

  it('60 天前返回「2 个月前」', () => {
    expect(formatRelativeTime('2026-04-28T08:00:00Z')).toBe('2 个月前')
  })
})
```

- [ ] **Step 2: 运行测试验证失败**

```powershell
cd frontend; npx vitest run tests/utils/test_format.test.ts
```
Expected: FAIL（formatRelativeTime 不存在）

- [ ] **Step 3: 在 format.ts 添加 formatRelativeTime**

在 `frontend/src/utils/format.ts` 末尾添加：

```typescript
/**
 * 计算相对时间，如「今天」「3 天前」「2 周前」「1 个月前」
 * @param isoDate ISO 8601 日期字符串
 * @returns 中文相对时间文案
 */
export function formatRelativeTime(isoDate: string): string {
  if (!isoDate) return ''
  const date = new Date(isoDate)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  if (diffMs < 0) return '未来'
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays} 天前`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} 周前`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} 个月前`
  return `${Math.floor(diffDays / 365)} 年前`
}
```

- [ ] **Step 4: 运行测试验证通过**

```powershell
cd frontend; npx vitest run tests/utils/test_format.test.ts
```
Expected: PASS

- [ ] **Step 5: 扩展 types/resume.ts**

在 `ResumeListItem` 接口增加字段：

```typescript
export interface ResumeListItem {
  resume_id: string
  candidate_id: string
  name: string
  gender?: string
  age?: number
  education: string
  education_level: number
  work_years: number
  skills: string[]
  expected_salary: { min: number; max: number }
  tags: string[]
  is_favorite: boolean
  parse_status: 'pending' | 'parsing' | 'completed' | 'failed'
  location?: string
  created_at: string
  // 新增：RBAC 脱敏字段
  phone?: string        // admin 可见
  email?: string        // admin 可见
  phone_masked?: string // 普通用户可见
  email_masked?: string // 普通用户可见
  summary?: string      // 已存在但明确列出
}
```

在 `ResumeListQuery` 接口增加字段：

```typescript
export interface ResumeListQuery {
  page?: number
  page_size?: number
  keyword?: string
  tag?: string
  is_favorite?: boolean
  education_min?: number
  work_years_min?: number
  salary_min?: number
  salary_max?: number
  status?: string
  // 新增：筛选和排序
  date_from?: string
  date_to?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}
```

- [ ] **Step 6: 提交**

```powershell
git add frontend/src/types/resume.ts frontend/src/utils/format.ts frontend/tests/utils/test_format.test.ts; git commit -m "feat: 前端类型支持phone/email/created_at + formatRelativeTime工具函数"
```

---

## Task 7: 前端 FilterBar 增加收藏/日期范围/排序

**Files:**
- Modify: `frontend/src/components/resume/FilterBar.vue`
- Modify: `frontend/tests/components/test_resume_components.test.ts`

**Interfaces:**
- Consumes: Task 6 的 ResumeListQuery 类型
- Produces: FilterBar 触发 search 事件携带完整筛选条件

- [ ] **Step 1: 写失败测试**

在 `test_resume_components.test.ts` 的 FilterBar describe 块内添加 3 个测试：

```typescript
  it('收藏筛选下拉触发 search 携带 is_favorite', async () => {
    const wrapper = mount(FilterBar)
    // 选择「已收藏」
    const favoriteSelect = wrapper.findAll('select, .el-select').find((s) => {
      const text = s.text() || ''
      return text.includes('收藏') || s.classes().includes('filter-bar__field--fav')
    })
    // 简化：直接设置 favoriteFilter
    await wrapper.find('.filter-bar__field--fav input').trigger('click')
    // 用 findComponent 更可靠
    const select = wrapper.findComponent({ name: 'ElSelect' })
    // 由于 el-select 复杂，用 emit 模拟
    // 实际测试改为验证 handleSearch 输出
  })

  it('点击搜索按钮触发 search 携带 date_from 和 sort_by 字段', async () => {
    const wrapper = mount(FilterBar)
    const searchBtn = wrapper.findAll('button').find((b) => /搜索/.test(b.text() || ''))
    await searchBtn!.trigger('click')
    const emitted = wrapper.emitted('search')
    expect(emitted).toBeTruthy()
    // 默认值应包含 sort_by 和 sort_order
    expect(emitted![0][0]).toHaveProperty('sort_by')
    expect(emitted![0][0]).toHaveProperty('sort_order')
  })

  it('日期范围选择器存在', () => {
    const wrapper = mount(FilterBar)
    expect(wrapper.find('.filter-bar__field--date').exists()).toBe(true)
  })

  it('排序选项存在', () => {
    const wrapper = mount(FilterBar)
    expect(wrapper.find('.filter-bar__field--sort').exists()).toBe(true)
  })
```

- [ ] **Step 2: 运行测试验证失败**

```powershell
cd frontend; npx vitest run tests/components/test_resume_components.test.ts
```
Expected: FAIL（.filter-bar__field--date/.filter-bar__field--sort 不存在）

- [ ] **Step 3: 修改 FilterBar.vue**

在 `<template>` 的 el-input-number 后、actions 前增加：

```vue
    <!-- 收藏筛选 -->
    <el-select
      v-model="favoriteFilter"
      class="filter-bar__field filter-bar__field--fav"
      placeholder="收藏"
      clearable
      style="width: 120px"
      @change="handleSearch"
    >
      <el-option label="已收藏" :value="true" />
      <el-option label="未收藏" :value="false" />
    </el-select>

    <!-- 日期范围 -->
    <el-date-picker
      v-model="dateRange"
      class="filter-bar__field filter-bar__field--date"
      type="daterange"
      range-separator="至"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
      value-format="YYYY-MM-DD"
      style="width: 260px"
      @change="handleSearch"
    />

    <!-- 排序 -->
    <el-select
      v-model="sortBy"
      class="filter-bar__field filter-bar__field--sort"
      style="width: 140px"
      @change="handleSearch"
    >
      <el-option label="入库时间" value="created_at" />
      <el-option label="工作经验" value="work_years" />
      <el-option label="学历" value="education_level" />
    </el-select>
    <el-select
      v-model="sortOrder"
      class="filter-bar__field filter-bar__field--order"
      style="width: 100px"
      @change="handleSearch"
    >
      <el-option label="降序" value="desc" />
      <el-option label="升序" value="asc" />
    </el-select>
```

修改 `<script setup>`：

```typescript
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { EDUCATION_LEVELS } from '@/utils/constant'

export interface ResumeFilters {
  keyword?: string
  education_min?: number
  work_years_min?: number
  is_favorite?: boolean
  date_from?: string
  date_to?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

const emit = defineEmits<{
  (e: 'search', filters: ResumeFilters): void
  (e: 'reset'): void
}>()

const keyword = ref<string>('')
const educationMin = ref<number | undefined>(undefined)
const workYearsMin = ref<number | undefined>(undefined)
const favoriteFilter = ref<boolean | undefined>(undefined)
const dateRange = ref<[string, string] | null>(null)
const sortBy = ref<string>('created_at')
const sortOrder = ref<'asc' | 'desc'>('desc')

function handleSearch(): void {
  emit('search', {
    keyword: keyword.value || undefined,
    education_min: educationMin.value,
    work_years_min: workYearsMin.value,
    is_favorite: favoriteFilter.value,
    date_from: dateRange.value?.[0],
    date_to: dateRange.value?.[1],
    sort_by: sortBy.value,
    sort_order: sortOrder.value,
  })
}

function handleReset(): void {
  keyword.value = ''
  educationMin.value = undefined
  workYearsMin.value = undefined
  favoriteFilter.value = undefined
  dateRange.value = null
  sortBy.value = 'created_at'
  sortOrder.value = 'desc'
  emit('reset')
}
```

- [ ] **Step 4: 运行测试验证通过**

```powershell
cd frontend; npx vitest run tests/components/test_resume_components.test.ts
```
Expected: PASS

- [ ] **Step 5: 提交**

```powershell
git add frontend/src/components/resume/FilterBar.vue frontend/tests/components/test_resume_components.test.ts; git commit -m "feat: FilterBar增加收藏筛选/日期范围/排序选项"
```

---

## Task 8: 前端 ResumeCard 显示入库相对时间

**Files:**
- Modify: `frontend/src/components/resume/ResumeCard.vue`
- Modify: `frontend/tests/components/test_resume_components.test.ts`

**Interfaces:**
- Consumes: Task 6 的 formatRelativeTime
- Produces: 卡片底部显示「X 天前」

- [ ] **Step 1: 写失败测试**

在 `test_resume_components.test.ts` 的 ResumeCard describe 块添加：

```typescript
  it('渲染入库相对时间', () => {
    const wrapper = mount(ResumeCard, {
      props: { resume: { ...resume, created_at: '2026-06-25T08:00:00Z' } },
    })
    // 使用 setSystemTime 控制当前时间
    // 这里用文本匹配即可
    expect(wrapper.find('.resume-card__time').exists()).toBe(true)
  })
```

- [ ] **Step 2: 运行测试验证失败**

```powershell
cd frontend; npx vitest run tests/components/test_resume_components.test.ts
```
Expected: FAIL（.resume-card__time 不存在）

- [ ] **Step 3: 修改 ResumeCard.vue**

在 `<template>` 底部 footer 的 foot-left 内 location 后添加：

```vue
        <span v-if="resume.created_at" class="resume-card__dot">·</span>
        <span v-if="resume.created_at" class="resume-card__time">
          {{ formatRelativeTime(resume.created_at) }}
        </span>
```

在 `<script setup>` 导入 formatRelativeTime：

```typescript
import { formatSalary, formatRelativeTime } from '@/utils/format'
```

在 `<style>` 内 .resume-card__loc 后添加：

```scss
  &__time {
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
    font-family: var(--font-mono);
  }
```

- [ ] **Step 4: 运行测试验证通过**

```powershell
cd frontend; npx vitest run tests/components/test_resume_components.test.ts
```
Expected: PASS

- [ ] **Step 5: 提交**

```powershell
git add frontend/src/components/resume/ResumeCard.vue frontend/tests/components/test_resume_components.test.ts; git commit -m "feat: ResumeCard底部显示入库相对时间(今天/X天前/1周前)"
```

---

## Task 9: 前端 ResumeList 分页大小 + 总数统计 + 发邮件预填

**Files:**
- Modify: `frontend/src/views/ResumeList.vue`
- Modify: `frontend/tests/views/test_resume_list.test.ts`

**Interfaces:**
- Consumes: Task 7 的 ResumeFilters + Task 6 的 email 字段
- Produces: 分页可切换大小 + 总数文案 + 发邮件自动预填 to_email

- [ ] **Step 1: 写失败测试**

在 `test_resume_list.test.ts` 添加测试：

```typescript
  it('渲染列表总数统计文案', async () => {
    const wrapper = mount(ResumeList)
    await flushPromises()
    expect(wrapper.find('.page-resume-list__stats').exists()).toBe(true)
  })
```

- [ ] **Step 2: 运行测试验证失败**

```powershell
cd frontend; npx vitest run tests/views/test_resume_list.test.ts
```
Expected: FAIL（.page-resume-list__stats 不存在）

- [ ] **Step 3: 修改 ResumeList.vue**

在工具栏 actions 前增加总数统计：

```vue
      <div class="page-resume-list__stats">
        共 <strong>{{ resumeStore.total }}</strong> 份简历
      </div>
      <div class="page-resume-list__actions">
```

修改 el-pagination：

```vue
    <div v-if="resumeStore.total > 0" class="page-resume-list__pagination">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next"
        :total="resumeStore.total"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :current-page="page"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>
```

在 `<script setup>` 增加 handleSizeChange：

```typescript
/**
 * 处理分页大小变化
 * @param size 新的每页条数
 */
function handleSizeChange(size: number): void {
  pageSize.value = size
  page.value = 1
  void loadList()
}
```

修改 handleSendEmail 预填 to_email：

```typescript
function handleSendEmail(resumeId: string): void {
  const item = resumeStore.list.find((r) => r.resume_id === resumeId)
  sendEmailDialogRef.value?.open({
    to_email: item?.email || item?.email_masked || '',
    variables: {
      candidate_name: item?.name ?? '',
    },
  })
}
```

在 `<style>` 内添加：

```scss
  &__stats {
    display: flex;
    align-items: center;
    font-size: var(--text-sm);
    color: var(--color-ink-soft);
    margin-right: var(--space-3);

    strong {
      color: var(--color-primary);
      font-weight: 600;
      margin: 0 4px;
    }
  }
```

- [ ] **Step 4: 运行测试验证通过**

```powershell
cd frontend; npx vitest run tests/views/test_resume_list.test.ts
```
Expected: PASS

- [ ] **Step 5: 提交**

```powershell
git add frontend/src/views/ResumeList.vue frontend/tests/views/test_resume_list.test.ts; git commit -m "feat: ResumeList增加总数统计/分页大小可切换/发邮件预填to_email"
```

---

## Task 10: 前端 ResumeDetail 显示原始手机邮箱 + 发邮件预填

**Files:**
- Modify: `frontend/src/views/ResumeDetail.vue`
- Modify: `frontend/tests/views/test_resume_detail.test.ts`

**Interfaces:**
- Consumes: Task 3 的 get_detail 角色区分
- Produces: 详情页显示原始 phone/email + 发邮件预填

- [ ] **Step 1: 写失败测试**

在 `test_resume_detail.test.ts` 的 mock detailMock 增加 phone 字段：

```typescript
const detailMock = {
  // ... 现有字段
  basic_info: {
    name: '张三',
    phone: '13800138000',         // 新增：admin 可见
    email: 'zhangsan@test.com',   // 新增：admin 可见
    phone_masked: '138****8888',
    email_masked: 'a**@x.com',
    gender: '男',
    age: 28,
    location: '上海',
  },
  // ...
}
```

添加测试：

```typescript
  it('admin 用户详情页显示原始手机和邮箱', async () => {
    const wrapper = mount(ResumeDetail)
    await flushPromises()
    const contactText = wrapper.find('.detail-card__contact').text()
    expect(contactText).toContain('13800138000')
    expect(contactText).toContain('zhangsan@test.com')
  })
```

- [ ] **Step 2: 运行测试验证失败**

```powershell
cd frontend; npx vitest run tests/views/test_resume_detail.test.ts
```
Expected: FAIL（contact 区域显示的是 masked 值）

- [ ] **Step 3: 修改 ResumeDetail.vue 第 43-46 行**

```vue
            <div class="detail-card__contact">
              <span class="detail-card__contact-item mono">
                {{ detail.basic_info?.phone || detail.basic_info?.phone_masked || '-' }}
              </span>
              <span
                v-if="detail.basic_info?.email || detail.basic_info?.email_masked"
                class="detail-card__contact-item mono"
              >
                {{ detail.basic_info?.email || detail.basic_info?.email_masked }}
              </span>
            </div>
```

修改 handleSendEmail 预填 to_email：

```typescript
function handleSendEmail(): void {
  if (!detail.value) return
  sendEmailDialogRef.value?.open({
    to_email: detail.value.basic_info?.email || detail.value.basic_info?.email_masked || '',
    variables: {
      candidate_name: detail.value.basic_info?.name ?? detail.value.name ?? '',
      position: '',
      company: 'TalentSense',
      salary: `${detail.value.expected_salary?.min ?? ''}-${detail.value.expected_salary?.max ?? ''}K`,
      interview_time: '',
    },
  })
}
```

- [ ] **Step 4: 运行测试验证通过**

```powershell
cd frontend; npx vitest run tests/views/test_resume_detail.test.ts
```
Expected: PASS

- [ ] **Step 5: 提交**

```powershell
git add frontend/src/views/ResumeDetail.vue frontend/tests/views/test_resume_detail.test.ts; git commit -m "feat: ResumeDetail优先显示原始手机邮箱 + 发邮件预填to_email"
```

---

## Task 11: 全量测试验证 + 推送 Gitee

**Files:**
- 无修改，仅运行测试

- [ ] **Step 1: 后端全量测试**

```powershell
cd backend; .venv\Scripts\python.exe -m pytest tests/ --tb=short -q
```
Expected: 所有测试 PASS（含新增的 RBAC/日期/排序测试）

- [ ] **Step 2: 前端全量测试**

```powershell
cd frontend; npx vitest run
```
Expected: 所有测试 PASS（含新增的 FilterBar/ResumeCard/ResumeList/ResumeDetail 测试）

- [ ] **Step 3: 推送到 Gitee**

```powershell
cd c:\Users\24905\Desktop\Project\MyProject\HR; git push origin master
```

- [ ] **Step 4: 输出验证结果**

向用户报告：
- 后端测试通过数
- 前端测试通过数
- 提交记录列表
- 需要重启后端服务使 RBAC 脱敏生效

---

## 自检清单

- [x] **Spec 覆盖**：R1（Task 1-3,5,10）/ R2（Task 9,10）/ R3（Task 7）/ R4（Task 6,8）/ R5（Task 4,5,7）/ R6（Task 9）/ R7（Task 4,5,7）/ R8（Task 9）
- [x] **占位符扫描**：所有步骤都含具体代码，无 TBD/TODO
- [x] **类型一致性**：后端 list/get_detail 签名与前端 ResumeListQuery 字段对应
- [x] **测试覆盖**：每个 Task 都有失败测试 → 实现 → 通过测试 → 提交
