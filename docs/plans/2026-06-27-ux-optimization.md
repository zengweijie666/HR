# 简历库体验优化与功能修复 实施计划

**Goal:** 修复简历库 10 个体验/功能问题：批量上传、解析速度、标签搜索、重置/删除刷新、导出空表、覆盖重复、项目经历提取、卡片操作、邮件变量占位符。

**Architecture:** 后端三层架构（api/services/core）+ 前端 Vue3 Composition API。修复分两条线：后端修复 dedup 路径/export 字段/标签搜索/BGE-M3 预热/projects 提取；前端修复批量上传/重置刷新/删除刷新/projects 展示/卡片操作/邮件变量标签。

**Tech Stack:** FastAPI + Motor(MongoDB) + OpenPyXL + BGE-M3 + Vue3 + Element Plus + Pinia + Vitest + Pytest

## Global Constraints

- API 路由前缀 `/api/v1/[module]`，统一响应 `{code, message, data, trace_id}`
- 前端可选字段使用 `??` 兜底
- MongoDB 响应使用 `MongoJSONResponse` 序列化 ObjectId
- 服务类用 `@property` 延迟初始化 MongoDB/Redis collection
- 测试用 `MagicMock()` + `AsyncMock(to_list)` 模拟 motor collection
- 提交信息格式：`feat: ...` / `fix: ...`
- Python 测试：`cd backend && .venv\Scripts\python.exe -m pytest tests/ -v`
- 前端测试：`cd frontend && npm run test`

## 根因分析

| # | 问题 | 根因 | 修复位置 |
|---|------|------|----------|
| 1 | 不支持批量上传 | `UploadDialog.vue` `:limit="1"` 限制单文件 | 前端 |
| 2 | 解析速度慢 | BGE-M3 模型懒加载，首次 encode() 才加载 | 后端 `main.py` |
| 3 | 标签搜索不支持 | `resume_service.py` list() keyword 只查 name/skills，不查 tags | 后端 |
| 4 | 重置不刷新 | `resumeStore.setFilters()` 合并而非替换，旧筛选条件残留 | 前端 |
| 5 | 删除不刷新 | 删除后 selectedMap 未清理；非 admin 调用 403 静默失败 | 前端 |
| 6 | 导出 xlsx 空 | 前端传 resume_id 到 candidate_ids 字段，后端按 candidate_id 过滤 | 后端 |
| 7 | 覆盖重复无效 | (a) dedup.py 查顶层 phone_hash，实际存在 basic_info.phone_hash; (b) overwrite=True 仅跳过去重，不删旧简历 | 后端 |
| 8 | 项目经历未提取 | (a) LLM prompt 不够强调; (b) ResumeDetail.vue 无 projects 展示区; (c) ResumeDetail 类型缺 projects 字段 | 前后端 |
| 9 | 卡片只有薪资 | ResumeCard.vue footer 只显示薪资，缺少邮件/面试操作 | 前端 |
| 10 | 邮件变量占位符无含义 | formatVarLabel 只输出 `{{ var }}`，placeholder 固定"变量值" | 前端 |

---

## Task 1: 修复去重查询路径 + 覆盖重复逻辑（后端）

**Files:**
- Modify: `backend/app/utils/dedup.py`
- Modify: `backend/app/services/resume_service.py:155-169`（去重 + overwrite 分支）
- Test: `backend/tests/utils/test_dedup.py`
- Test: `backend/tests/services/test_resume_service.py`

**Interfaces:**
- Consumes: MongoDB resumes collection
- Produces: 正确的去重检测 + overwrite 时删除旧简历

- [ ] **Step 1: 写 dedup 路径修复的失败测试**

```python
# backend/tests/utils/test_dedup.py 追加
@pytest.mark.asyncio
async def test_dedup_checks_basic_info_path():
    """去重应查询 basic_info.phone_hash / basic_info.email_hash 路径"""
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=None)
    checker = DedupChecker(coll)
    await checker.check("hash_p", "hash_e")
    call_args = coll.find_one.call_args
    query = call_args.args[0]
    # 必须查 basic_info.phone_hash 而非顶层 phone_hash
    assert "basic_info.phone_hash" in str(query) or "basic_info.email_hash" in str(query)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/utils/test_dedup.py::test_dedup_checks_basic_info_path -v`
Expected: FAIL

- [ ] **Step 3: 修复 dedup.py 查询路径**

```python
# backend/app/utils/dedup.py 完整替换
"""
文件名: app/utils/dedup.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 简历去重检查，通过 basic_info.phone_hash + basic_info.email_hash 查 MongoDB
入参: phone_hash, email_hash, MongoDB collection
出参: 命中的 resume_id 或 None
"""


class DedupChecker:
    """去重检查器"""

    def __init__(self, resumes_collection):
        self.coll = resumes_collection

    async def check(self, phone_hash: str, email_hash: str) -> str | None:
        """返回已存在 resume_id，无重复返回 None

        注意：phone_hash/email_hash 存储在 basic_info 子文档中，
        查询路径必须为 basic_info.phone_hash / basic_info.email_hash。
        """
        if not phone_hash and not email_hash:
            return None
        conditions = []
        if phone_hash:
            conditions.append({"basic_info.phone_hash": phone_hash})
        if email_hash:
            conditions.append({"basic_info.email_hash": email_hash})
        query = {"$or": conditions} if len(conditions) > 1 else conditions[0]
        doc = await self.coll.find_one(query, {"resume_id": 1, "_id": 0})
        return doc["resume_id"] if doc else None
```

- [ ] **Step 4: 运行 dedup 测试确认通过**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/utils/test_dedup.py -v`
Expected: PASS

- [ ] **Step 5: 写 overwrite 删除旧简历的失败测试**

```python
# backend/tests/services/test_resume_service.py 追加
@pytest.mark.asyncio
async def test_parse_overwrite_deletes_existing(svc):
    """overwrite=True 且检测到重复时，应删除旧简历（MinIO + MongoDB + Milvus）"""
    svc.minio.upload_bytes.return_value = "minio_new"
    svc.llm.chat = AsyncMock(return_value='{"name":"张三","phone":"13812341234","email":"a@b.com","skills":[],"work_experience":[],"education_detail":[],"projects":[]}')
    svc.dedup_checker = AsyncMock()
    svc.dedup_checker.check = AsyncMock(return_value="res_existing")
    # 旧简历文档查找返回 file_id
    svc.resumes_coll.find_one = AsyncMock(return_value={
        "resume_id": "res_existing",
        "file_info": {"file_id": "minio_old"}
    })
    await svc._parse_and_index("res_new", b"pdf", "minio_new", "test.pdf", overwrite=True)
    # 验证删除了旧简历的 MinIO 文件
    svc.minio.delete.assert_called_with("minio_old")
    # 验证删除了旧简历的 MongoDB 记录
    svc.resumes_coll.delete_one.assert_any_call({"resume_id": "res_existing"})
    # 验证删除了旧简历的 Milvus 向量
    svc.vector_store.delete_by_resume_id.assert_any_call("res_existing")
```

- [ ] **Step 6: 运行测试确认失败**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py::test_parse_overwrite_deletes_existing -v`
Expected: FAIL

- [ ] **Step 7: 修复 resume_service.py 去重 + overwrite 逻辑**

修改 `_parse_and_index` 方法的第 7 步去重分支（约 155-169 行）：

```python
            # 7. 去重
            phone_h = hash_phone(structured.get("phone", ""))
            email_h = hash_email(structured.get("email", ""))
            dedup_checker = self.dedup_checker or DedupChecker(self.resumes_coll)
            existing = await dedup_checker.check(phone_h, email_h)
            if existing:
                if overwrite:
                    # 覆盖模式：删除旧简历的 MinIO 文件 + MongoDB 记录 + Milvus 向量
                    try:
                        old_doc = await self.resumes_coll.find_one(
                            {"resume_id": existing}, {"file_info": 1}
                        )
                        if old_doc and old_doc.get("file_info", {}).get("file_id"):
                            self.minio.delete(old_doc["file_info"]["file_id"])
                        await self.resumes_coll.delete_one({"resume_id": existing})
                        await self.vector_store.delete_by_resume_id(existing)
                        logger.info(f"覆盖模式：已删除旧简历 {existing}")
                    except Exception as del_err:
                        logger.warning(f"覆盖删除旧简历 {existing} 失败: {del_err}")
                else:
                    # 非覆盖：标记当前简历为重复
                    await self.resumes_coll.update_one(
                        {"resume_id": resume_id},
                        update={"$set": {
                            "is_duplicate": True, "duplicate_with": existing,
                            "parse_info": {"parse_status": "completed", "parse_time": datetime.now(timezone.utc).isoformat()},
                        }},
                    )
                    logger.info(f"简历 {resume_id} 重复，关联 {existing}")
                    return
```

- [ ] **Step 8: 运行所有 resume_service 测试确认通过**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py -v`
Expected: PASS

- [ ] **Step 9: 提交**

```bash
cd backend
git add app/utils/dedup.py app/services/resume_service.py tests/utils/test_dedup.py tests/services/test_resume_service.py
git commit -m "fix: 修复去重查询路径(basic_info.phone_hash)和覆盖重复逻辑(删除旧简历)"
```

---

## Task 2: 修复导出 Excel 空表问题（后端）

**Files:**
- Modify: `backend/app/services/export_service.py:67-70`（查询条件）
- Modify: `backend/app/api/candidates.py:21`（参数名语义化）
- Test: `backend/tests/services/test_export_service.py`

**Interfaces:**
- Consumes: 前端传入的 resume_id 列表
- Produces: 正确查询 MongoDB 并导出非空 Excel

- [ ] **Step 1: 写 resume_id 查询的失败测试**

```python
# backend/tests/services/test_export_service.py 追加
@pytest.mark.asyncio
async def test_export_by_resume_ids(svc):
    """导出应按 resume_id 查询（前端传的是 resume_id 而非 candidate_id）"""
    svc.resumes_coll.find.return_value.to_list = AsyncMock(return_value=[
        {
            "resume_id": "res_001", "candidate_id": "c1",
            "basic_info": {"name": "张三", "gender": "男", "age": 28},
            "education": "本科", "work_years": 5,
            "skills": ["Java"], "expected_salary": {"min": 20, "max": 30},
            "tags": ["已面试"], "location": "北京"
        }
    ])
    excel_bytes = await svc.export_excel(
        candidate_ids=["res_001"],  # 前端实际传的是 resume_id
        columns=["name", "work_years"]
    )
    # 验证查询用的是 resume_id 而非 candidate_id
    call_args = svc.resumes_coll.find.call_args
    query = call_args.args[0]
    assert "resume_id" in query
    wb = load_workbook(io.BytesIO(excel_bytes))
    ws = wb.active
    assert ws.cell(2, 1).value == "张三"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/services/test_export_service.py::test_export_by_resume_ids -v`
Expected: FAIL

- [ ] **Step 3: 修复 export_service.py 查询条件**

```python
# backend/app/services/export_service.py 修改 export_excel 方法
# 将第 67-70 行：
#   if candidate_ids and self.resumes_coll is not None:
#       cursor = self.resumes_coll.find({"candidate_id": {"$in": candidate_ids}})
#       docs = await cursor.to_list(length=len(candidate_ids))
# 替换为：
        # 拉取数据：前端传的是 resume_id 列表（非 candidate_id）
        docs: list[dict] = []
        if candidate_ids and self.resumes_coll is not None:
            cursor = self.resumes_coll.find({"resume_id": {"$in": candidate_ids}})
            docs = await cursor.to_list(length=len(candidate_ids))
```

- [ ] **Step 4: 运行导出测试确认通过**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/services/test_export_service.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd backend
git add app/services/export_service.py tests/services/test_export_service.py
git commit -m "fix: 修复导出Excel空表(查询条件从candidate_id改为resume_id)"
```

---

## Task 3: 添加标签搜索支持（后端）

**Files:**
- Modify: `backend/app/services/resume_service.py:394-398`（keyword 查询）
- Test: `backend/tests/services/test_resume_service.py`

**Interfaces:**
- Consumes: keyword 查询参数
- Produces: 关键词可搜索 name/skills/tags

- [ ] **Step 1: 写标签搜索的失败测试**

```python
# backend/tests/services/test_resume_service.py 追加
@pytest.mark.asyncio
async def test_list_search_includes_tags(svc):
    """关键词搜索应包含 tags 字段"""
    svc.resumes_coll.count_documents = AsyncMock(return_value=1)
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value.limit.return_value.sort.return_value.to_list = AsyncMock(return_value=[])
    svc.resumes_coll.find = MagicMock(return_value=mock_cursor)
    await svc.list(keyword="急聘", page=1, page_size=20)
    call_args = svc.resumes_coll.find.call_args
    query = call_args.args[0]
    # $or 条件中应包含 tags 字段
    or_conditions = query.get("$or", [])
    assert any("tags" in cond for cond in or_conditions), f"关键词搜索应包含 tags 字段, 实际: {or_conditions}"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py::test_list_search_includes_tags -v`
Expected: FAIL

- [ ] **Step 3: 修改 resume_service.py list() keyword 查询**

```python
# backend/app/services/resume_service.py list() 方法中
# 将：
#   if keyword:
#       query["$or"] = [
#           {"basic_info.name": {"$regex": keyword}},
#           {"skills": {"$regex": keyword}},
#       ]
# 替换为：
        if keyword:
            query["$or"] = [
                {"basic_info.name": {"$regex": keyword, "$options": "i"}},
                {"skills": {"$regex": keyword, "$options": "i"}},
                {"tags": {"$regex": keyword, "$options": "i"}},
                {"summary": {"$regex": keyword, "$options": "i"}},
            ]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd backend
git add app/services/resume_service.py tests/services/test_resume_service.py
git commit -m "feat: 关键词搜索支持标签(tags)和摘要(summary)字段"
```

---

## Task 4: BGE-M3 模型预热 + 强化 projects 提取（后端）

**Files:**
- Modify: `backend/app/main.py:52-58`（lifespan 中预热 BGE-M3）
- Modify: `backend/app/agent/prompts.py:8-68`（强化 projects 提取）
- Modify: `backend/app/services/resume_service.py:524-601`（添加 projects 正则兜底）
- Test: `backend/tests/core/test_main.py`

**Interfaces:**
- Consumes: BGE-M3 模型路径配置
- Produces: 启动即加载模型，首次解析不再慢；projects 提取更准确

- [ ] **Step 1: 修改 main.py lifespan 预热 BGE-M3**

```python
# backend/app/main.py lifespan() 中，在 Milvus 预热之后、管理员初始化之前，追加：
    # 预热 BGE-M3 模型：避免首次上传简历时才加载导致解析很慢
    try:
        from app.core.embedding import embedding_model
        _ = embedding_model.model  # 触发懒加载
        logger.info("BGE-M3 模型已预热")
    except Exception as e:
        logger.warning(f"BGE-M3 预热失败，首次解析将较慢: {e}")
```

- [ ] **Step 2: 强化 prompts.py 中 projects 提取指令**

```python
# backend/app/agent/prompts.py 修改 RESUME_EXTRACT_PROMPT
# 在提取规则第 9 条后追加强调（约第 59 行）：
9. **【重要】projects字段必须提取所有项目经历**。简历中常见的项目经历段落标题包括"项目经历"、"项目经验"、"主要项目"、"项目作品"等。如果工作经历中的 description 包含具体项目名称、技术栈、职责描述，也应提取为独立的 project 条目。即使简历没有明确的项目段落，也要从工作经历中识别出参与的项目。
```

- [ ] **Step 3: 添加 projects 正则兜底提取**

在 `resume_service.py` 的 `_regex_extract_fallback` 函数中追加 projects 提取逻辑：

```python
# backend/app/services/resume_service.py _regex_extract_fallback() 函数中
# 在 result["skills"] = found_skills[:20] 之后追加：

    # 项目经历兜底提取：从文本中识别"项目名称:"/"项目经历"等模式
    projects = _extract_projects_from_text(raw_text)
    result["projects"] = projects

    return result


def _extract_projects_from_text(raw_text: str) -> list:
    """从简历文本中正则提取项目经历

    入参:
        raw_text: 简历原始文本
    出参:
        项目列表，每项含 name/role/description
    """
    if not raw_text:
        return []
    projects = []
    # 匹配 "项目名称：XXX" / "项目：XXX" / "项目经历：XXX" 等
    project_pattern = re.compile(
        r'(?:项目名称|项目|项目经历|项目经验)\s*[:：]\s*(.+?)(?=\n(?:项目|工作|教育|技能|自我|个人|证书|语言|兴趣爱好|$))',
        re.DOTALL
    )
    for m in project_pattern.finditer(raw_text):
        block = m.group(1).strip()
        if not block:
            continue
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        name = lines[0] if lines else ""
        description = "\n".join(lines[1:]) if len(lines) > 1 else ""
        projects.append({
            "name": name[:100],
            "role": "",
            "description": description[:500],
        })
    return projects[:10]  # 最多 10 个项目
```

同时修改 `_parse_and_index` 中的兜底逻辑，在 skills 补充后追加 projects 补充：

```python
# backend/app/services/resume_service.py _parse_and_index() 方法中
# 在 skills 正则补充之后、字段 None 兜底之前，追加：
            # projects 为空时用正则补充
            projects = structured.get("projects")
            if not isinstance(projects, list) or len(projects) == 0:
                structured["projects"] = regex_result.get("projects", [])
```

- [ ] **Step 4: 写 projects 正则提取测试**

```python
# backend/tests/services/test_resume_service.py 追加
def test_extract_projects_from_text():
    """正则兜底提取项目经历"""
    from app.services.resume_service import _extract_projects_from_text
    text = """
工作经历
公司A 高级开发工程师
项目名称：电商平台重构
技术栈：Java, Spring Cloud
负责微服务架构设计和核心模块开发

项目：数据中台建设
主导数据采集和处理链路
"""
    projects = _extract_projects_from_text(text)
    assert len(projects) >= 1
    assert "电商平台" in projects[0]["name"] or "数据中台" in projects[0]["name"]
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/services/test_resume_service.py::test_extract_projects_from_text -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
cd backend
git add app/main.py app/agent/prompts.py app/services/resume_service.py tests/services/test_resume_service.py
git commit -m "feat: BGE-M3模型预热+强化项目经历提取(prompt+正则兜底)"
```

---

## Task 5: 支持批量上传（前端）

**Files:**
- Modify: `frontend/src/components/resume/UploadDialog.vue`
- Modify: `frontend/src/api/resume.ts`
- Modify: `frontend/src/views/ResumeList.vue:81-85`（uploaded 事件处理）
- Test: `frontend/tests/components/test_upload_preview.test.ts`

**Interfaces:**
- Consumes: uploadResume API
- Produces: 支持多文件选择 + 逐个上传 + 进度反馈

- [ ] **Step 1: 写批量上传组件的失败测试**

```typescript
// frontend/tests/components/test_upload_preview.test.ts 追加
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import UploadDialog from '@/components/resume/UploadDialog.vue'

describe('UploadDialog 批量上传', () => {
  it('应支持选择多个文件', () => {
    const wrapper = mount(UploadDialog, {
      props: { visible: true },
      global: { stubs: ['el-dialog', 'el-upload', 'el-icon', 'el-checkbox', 'el-button'] }
    })
    const upload = wrapper.findComponent({ name: 'ElUpload' })
    // limit 不应为 1
    expect(upload.props('limit')).toBeUndefined()
  })

  it('上传按钮文本应反映批量上传', () => {
    const wrapper = mount(UploadDialog, {
      props: { visible: true },
      global: { stubs: ['el-dialog', 'el-upload', 'el-icon', 'el-checkbox', 'el-button'] }
    })
    const hint = wrapper.find('.upload-dialog__hint-sub')
    expect(hint.text()).toContain('批量')
    expect(hint.text()).toContain('PDF')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npm run test -- test_upload_preview.test.ts`
Expected: FAIL

- [ ] **Step 3: 修改 UploadDialog.vue 支持多文件**

```vue
<!-- frontend/src/components/resume/UploadDialog.vue 完整替换 -->
<!--
  文件名: components/resume/UploadDialog.vue
  创建时间: 2026-06-26
  作者: TalentSense Team
  功能描述: 简历上传对话框（支持批量）
    - el-dialog + 拖拽上传区（支持多文件）
    - 覆盖重复简历 checkbox
    - 文件列表展示 + 逐个上传 + 进度反馈
-->
<template>
  <el-dialog
    :model-value="visible"
    title="上传简历"
    width="560px"
    :close-on-click-modal="false"
    append-to-body
    class="upload-dialog"
    @update:model-value="handleVisibleChange"
    @close="handleClose"
  >
    <div class="upload-dialog__eyebrow eyebrow">RESUME UPLOAD</div>

    <el-upload
      ref="uploadRef"
      class="upload-dialog__uploader"
      drag
      multiple
      :auto-upload="false"
      :on-change="handleFileChange"
      :on-remove="handleFileRemove"
      :file-list="fileList"
      accept=".pdf,.docx,.png,.jpg,.jpeg"
    >
      <el-icon class="upload-dialog__icon"><UploadFilled /></el-icon>
      <div class="upload-dialog__hint-title">将文件拖到此处，或点击上传</div>
      <div class="upload-dialog__hint-sub">支持 PDF / DOCX / PNG / JPG，可批量选择多个文件</div>
    </el-upload>

    <div v-if="fileList.length > 0" class="upload-dialog__count">
      已选择 {{ fileList.length }} 个文件
    </div>

    <div class="upload-dialog__options">
      <el-checkbox v-model="overwrite">覆盖重复简历</el-checkbox>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-dialog__progress">
      <el-progress :percentage="uploadProgress" :format="() => `${uploadedCount}/${fileList.length}`" />
    </div>

    <template #footer>
      <el-button text @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="uploading" :disabled="!fileList.length" @click="handleUpload">
        上传（{{ fileList.length }} ）
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * UploadDialog 简历上传对话框（批量）
 * 选择多个文件后逐个调用 uploadResume 上传，全部完成后 emit uploaded
 */
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadFiles, UploadInstance } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadResume } from '@/api/resume'
import type { UploadResponse } from '@/types/resume'

interface UploadDialogProps {
  visible: boolean
}

const props = defineProps<UploadDialogProps>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'uploaded', data: UploadResponse[]): void
}>()

const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadFiles>([])
const overwrite = ref<boolean>(false)
const uploading = ref<boolean>(false)
const uploadedCount = ref<number>(0)

const uploadProgress = computed(() => {
  if (!fileList.value.length) return 0
  return Math.round((uploadedCount.value / fileList.value.length) * 100)
})

watch(
  () => props.visible,
  (val) => {
    if (!val) {
      fileList.value = []
      overwrite.value = false
      uploading.value = false
      uploadedCount.value = 0
    }
  },
)

/** 处理文件选择变化 */
function handleFileChange(file: UploadFile): void {
  if (file && file.raw) {
    // 多文件模式：追加到列表（el-upload multiple 已自动追加到 fileList）
    const exists = fileList.value.some(f => f.uid === file.uid)
    if (!exists) {
      fileList.value.push(file)
    }
  }
}

/** 处理文件移除 */
function handleFileRemove(file: UploadFile): void {
  fileList.value = fileList.value.filter(f => f.uid !== file.uid)
}

/** 批量上传：逐个上传 */
async function handleUpload(): Promise<void> {
  if (!fileList.value.length) {
    ElMessage.warning('请先选择简历文件')
    return
  }
  uploading.value = true
  uploadedCount.value = 0
  const results: UploadResponse[] = []
  const errors: string[] = []

  for (const file of fileList.value) {
    if (!file.raw) continue
    try {
      const data = await uploadResume(file.raw, overwrite.value)
      results.push(data)
    } catch (err) {
      const msg = err instanceof Error ? err.message : `${file.name} 上传失败`
      errors.push(msg)
    }
    uploadedCount.value++
  }

  uploading.value = false

  if (results.length > 0) {
    ElMessage.success(`成功上传 ${results.length} 份简历，正在后台解析，列表将自动刷新`)
    emit('uploaded', results)
  }
  if (errors.length > 0) {
    ElMessage.warning(`${errors.length} 份上传失败：${errors[0]}`)
  }
  if (results.length > 0) {
    emit('close')
  }
}

function handleCancel(): void {
  emit('close')
}

function handleClose(): void {
  emit('close')
}

function handleVisibleChange(val: boolean): void {
  if (!val) {
    emit('close')
  }
}
</script>

<style scoped lang="scss">
.upload-dialog {
  &__eyebrow {
    margin-bottom: var(--space-4);
  }

  &__uploader {
    :deep(.el-upload-dragger) {
      width: 100%;
      padding: var(--space-8) var(--space-6);
      background-color: var(--color-bg-overlay);
      border: 1.5px dashed var(--color-accent-soft);
      border-radius: var(--radius-lg);
      transition: border-color var(--duration-fast) var(--ease-out),
        background-color var(--duration-fast) var(--ease-out);

      &:hover {
        border-color: var(--color-accent);
        background-color: var(--color-primary-tint);
      }
    }
  }

  &__icon {
    font-size: 40px;
    color: var(--color-primary);
    margin-bottom: var(--space-3);
  }

  &__hint-title {
    font-family: var(--font-display);
    font-size: var(--text-md);
    color: var(--color-ink);
  }

  &__hint-sub {
    margin-top: 4px;
    font-size: var(--text-xs);
    color: var(--color-ink-mute);
    letter-spacing: 0.02em;
  }

  &__count {
    margin-top: var(--space-3);
    font-size: var(--text-sm);
    color: var(--color-accent-deep);
    font-weight: 500;
  }

  &__options {
    margin-top: var(--space-4);
  }

  &__progress {
    margin-top: var(--space-3);
  }
}
</style>
```

- [ ] **Step 4: 修改 ResumeList.vue 适配批量上传事件**

```typescript
// frontend/src/views/ResumeList.vue handleUploaded 方法修改为：
/**
 * 处理上传成功（批量）：刷新列表并启动轮询
 */
function handleUploaded(): void {
  page.value = 1
  void loadList().then(() => {
    startPolling()
  })
}
```

- [ ] **Step 5: 运行前端测试确认通过**

Run: `cd frontend && npm run test -- test_upload_preview.test.ts`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
cd frontend
git add src/components/resume/UploadDialog.vue src/views/ResumeList.vue tests/components/test_upload_preview.test.ts
git commit -m "feat: 简历上传支持批量多文件选择+逐个上传+进度反馈"
```

---

## Task 6: 修复重置和删除不自动刷新（前端）

**Files:**
- Modify: `frontend/src/components/resume/FilterBar.vue:90-96`（重置逻辑）
- Modify: `frontend/src/stores/resume.ts:40-42`（replaceFilters 方法）
- Modify: `frontend/src/views/ResumeList.vue:149-153,193-213`（handleSearch + handleDeleteResume）
- Test: `frontend/tests/views/test_resume_list.test.ts`
- Test: `frontend/tests/stores/test_resume_store.test.ts`

**Interfaces:**
- Consumes: resumeStore
- Produces: 重置完全清空筛选并刷新；删除后清理 selectedMap 并刷新

- [ ] **Step 1: 写 store replaceFilters 失败测试**

```typescript
// frontend/tests/stores/test_resume_store.test.ts 追加
import { describe, it, expect } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useResumeStore } from '@/stores/resume'

describe('resumeStore replaceFilters', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('replaceFilters 应完全替换而非合并', () => {
    const store = useResumeStore()
    store.setFilters({ keyword: 'Java', education_min: 2 })
    expect(store.filters.keyword).toBe('Java')
    store.replaceFilters({})
    expect(store.filters.keyword).toBeUndefined()
    expect(store.filters.education_min).toBeUndefined()
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npm run test -- test_resume_store.test.ts`
Expected: FAIL

- [ ] **Step 3: 添加 replaceFilters 方法到 store**

```typescript
// frontend/src/stores/resume.ts 在 setFilters 后追加：
  /**
   * 完全替换查询条件（用于重置场景）
   * @param f 新的筛选字段（空对象表示清空全部）
   */
  function replaceFilters(f: Partial<ResumeListQuery>): void {
    filters.value = { ...f }
  }
```

并在 return 中导出：
```typescript
  return {
    list,
    total,
    filters,
    setList,
    setTotal,
    setFilters,
    replaceFilters,
    resetFilters,
    updateFavorite,
    updateTags,
    updateOne,
  }
```

- [ ] **Step 4: 修改 FilterBar.vue 重置逻辑**

```typescript
// frontend/src/components/resume/FilterBar.vue 修改 emit 定义，新增 reset 事件：
const emit = defineEmits<{
  (e: 'search', filters: ResumeFilters): void
  (e: 'reset'): void
}>()

/** 重置所有筛选条件 */
function handleReset(): void {
  keyword.value = ''
  educationMin.value = undefined
  workYearsMin.value = undefined
  emit('reset')
}
```

- [ ] **Step 5: 修改 ResumeList.vue 处理 reset 事件**

```vue
<!-- frontend/src/views/ResumeList.vue 模板中 FilterBar 添加 @reset -->
      <FilterBar class="page-resume-list__filter" @search="handleSearch" @reset="handleReset" />
```

```typescript
// frontend/src/views/ResumeList.vue 追加 handleReset 方法：
/**
 * 处理重置：完全清空筛选条件并刷新列表
 */
function handleReset(): void {
  resumeStore.replaceFilters({})
  page.value = 1
  void loadList()
}
```

- [ ] **Step 6: 修改 handleDeleteResume 清理 selectedMap**

```typescript
// frontend/src/views/ResumeList.vue 修改 handleDeleteResume：
/**
 * 处理删除简历（硬删除，弹确认框）
 * @param resumeId 简历 ID
 */
async function handleDeleteResume(resumeId: string): Promise<void> {
  const item = resumeStore.list.find((r) => r.resume_id === resumeId)
  const name = item?.name || '该简历'
  try {
    await ElMessageBox.confirm(
      `确定要删除「${name}」吗？此操作不可恢复，将同时删除文件、解析数据和向量索引。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await deleteResume(resumeId)
    ElMessage.success('删除成功')
    // 清理选中状态
    delete selectedMap[resumeId]
    handleSelectionChange()
    // 如果当前页删完，回退到上一页
    if (resumeStore.list.length === 1 && page.value > 1) {
      page.value--
    }
    await loadList()
  } catch (err) {
    const msg = err instanceof Error ? err.message : '删除失败'
    ElMessage.error(msg)
  }
}
```

- [ ] **Step 7: 写重置刷新的集成测试**

```typescript
// frontend/tests/views/test_resume_list.test.ts 追加
import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ResumeList from '@/views/ResumeList.vue'

vi.mock('@/api/resume', () => ({
  getResumeList: vi.fn().mockResolvedValue({ list: [], total: 0 }),
  toggleFavorite: vi.fn(),
  deleteResume: vi.fn().mockResolvedValue(undefined),
}))
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

describe('ResumeList 重置刷新', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('点击重置应清空筛选并重新加载', async () => {
    const wrapper = mount(ResumeList, {
      global: {
        stubs: ['el-button', 'el-icon', 'el-pagination', 'el-row', 'el-col', 'el-checkbox',
          'FilterBar', 'ResumeCard', 'UploadDialog', 'EmptyState', 'LoadingOverlay', 'router-link']
      }
    })
    await flushPromises()
    const { getResumeList } = await import('@/api/resume')
    const mockFn = getResumeList as ReturnType<typeof vi.fn>
    const initialCalls = mockFn.mock.calls.length
    // 触发重置
    wrapper.findComponent({ name: 'FilterBar' }).vm.$emit('reset')
    await flushPromises()
    expect(mockFn.mock.calls.length).toBeGreaterThan(initialCalls)
  })
})
```

- [ ] **Step 8: 运行测试确认通过**

Run: `cd frontend && npm run test -- test_resume_list.test.ts test_resume_store.test.ts`
Expected: PASS

- [ ] **Step 9: 提交**

```bash
cd frontend
git add src/stores/resume.ts src/components/resume/FilterBar.vue src/views/ResumeList.vue tests/stores/test_resume_store.test.ts tests/views/test_resume_list.test.ts
git commit -m "fix: 重置完全清空筛选(replaceFilters)+删除后清理选中状态和回退页码"
```

---

## Task 7: 简历详情展示项目经历（前端）

**Files:**
- Modify: `frontend/src/types/resume.ts:51-68`（添加 projects 类型）
- Modify: `frontend/src/views/ResumeDetail.vue:56-76`（添加项目经历区块）
- Test: `frontend/tests/views/test_resume_detail.test.ts`

**Interfaces:**
- Consumes: ResumeDetail.projects
- Produces: 详情页展示项目经历时间线

- [ ] **Step 1: 添加 Project 类型到 resume.ts**

```typescript
// frontend/src/types/resume.ts 在 EducationDetail 后追加：
export interface ProjectItem {
  name: string
  role: string
  description: string
}
```

并在 ResumeDetail 接口中追加字段：
```typescript
export interface ResumeDetail extends ResumeListItem {
  basic_info: {
    name: string
    phone_masked: string
    email_masked?: string
    gender?: string
    age?: number
    location?: string
  }
  work_experience: WorkExperience[]
  education_detail: EducationDetail[]
  projects?: ProjectItem[]
  summary: string
  file_info: { file_name: string; file_type: string; file_size?: number }
  parse_info: { parse_status: string; parse_time?: string }
  notes: string
  interview_notes?: InterviewNoteItem[]
  updated_at?: string
}
```

- [ ] **Step 2: 在 ResumeDetail.vue 添加项目经历展示区块**

在"工作经历"区块之后、"教育经历"区块之前插入：

```vue
<!-- frontend/src/views/ResumeDetail.vue 在工作经历 </div> 之后、教育经历之前插入 -->
            <!-- 项目经历 -->
            <div v-if="detail.projects?.length" class="detail-card__section">
              <h3 class="detail-card__section-title decor-line">项目经历</h3>
              <el-timeline class="detail-card__timeline">
                <el-timeline-item
                  v-for="(proj, idx) in detail.projects"
                  :key="`proj-${idx}`"
                  placement="top"
                >
                  <div class="detail-card__work">
                    <div class="detail-card__work-head">
                      <span class="detail-card__work-company">{{ proj.name }}</span>
                      <span v-if="proj.role" class="detail-card__work-position">{{ proj.role }}</span>
                    </div>
                    <p v-if="proj.description" class="detail-card__work-desc">
                      {{ proj.description }}
                    </p>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>
```

- [ ] **Step 3: 写项目经历展示测试**

```typescript
// frontend/tests/views/test_resume_detail.test.ts 追加
import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ResumeDetail from '@/views/ResumeDetail.vue'

vi.mock('@/api/resume', () => ({
  getResumeDetail: vi.fn().mockResolvedValue({
    resume_id: 'r1',
    basic_info: { name: '张三' },
    work_experience: [],
    education_detail: [],
    projects: [
      { name: '电商平台', role: '后端负责人', description: '微服务架构设计' }
    ],
    summary: '',
    tags: [],
  }),
  getPreviewUrl: vi.fn().mockResolvedValue({ preview_url: '', file_type: 'pdf', expires_in: 3600 }),
  toggleFavorite: vi.fn(),
  updateNotes: vi.fn(),
  updateTags: vi.fn(),
}))
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: 'r1' } }),
  useRouter: () => ({ push: vi.fn() }),
}))

describe('ResumeDetail 项目经历', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('应展示项目经历区块', async () => {
    const wrapper = mount(ResumeDetail, {
      global: {
        stubs: ['el-page-header', 'el-row', 'el-col', 'el-timeline', 'el-timeline-item',
          'el-tag', 'el-input', 'el-button', 'el-icon', 'ResumePreview', 'TagInput',
          'EmptyState', 'LoadingOverlay', 'SendEmailDialog']
      }
    })
    await flushPromises()
    const html = wrapper.html()
    expect(html).toContain('项目经历')
    expect(html).toContain('电商平台')
    expect(html).toContain('微服务架构设计')
  })
})
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npm run test -- test_resume_detail.test.ts`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd frontend
git add src/types/resume.ts src/views/ResumeDetail.vue tests/views/test_resume_detail.test.ts
git commit -m "feat: 简历详情页展示项目经历区块(projects时间线)"
```

---

## Task 8: 简历卡片添加操作按钮（前端）

**Files:**
- Modify: `frontend/src/components/resume/ResumeCard.vue:77-84`（footer 添加操作按钮）
- Modify: `frontend/src/views/ResumeList.vue:55-60`（传递 email 事件 + 引入 SendEmailDialog）
- Test: `frontend/tests/components/test_resume_components.test.ts`

**Interfaces:**
- Consumes: ResumeCard resume prop
- Produces: 卡片右下角有"发送邮件"按钮，点击触发 send-email 事件

- [ ] **Step 1: 修改 ResumeCard.vue 添加操作按钮**

```vue
<!-- frontend/src/components/resume/ResumeCard.vue footer 部分替换 -->
    <!-- 底部：学历·地点 + 薪资 + 操作按钮 -->
    <footer class="resume-card__foot">
      <div class="resume-card__foot-left">
        <span class="resume-card__edu">{{ resume.education || '学历未知' }}</span>
        <span v-if="resume.location" class="resume-card__dot">·</span>
        <span v-if="resume.location" class="resume-card__loc">{{ resume.location }}</span>
      </div>
      <div class="resume-card__foot-right">
        <span class="resume-card__salary">{{ formatSalary(resume.expected_salary) }}</span>
        <button
          type="button"
          class="resume-card__action-btn"
          aria-label="发送邮件"
          title="发送邮件"
          @click.stop="handleSendEmail"
        >
          <el-icon><Promotion /></el-icon>
        </button>
      </div>
    </footer>
```

```typescript
// frontend/src/components/resume/ResumeCard.vue script 部分
// import 追加 Promotion 图标：
import { Star, StarFilled, Delete, Promotion } from '@element-plus/icons-vue'

// emit 追加 send-email 事件：
const emit = defineEmits<{
  (e: 'click', resumeId: string): void
  (e: 'toggle-favorite', resumeId: string): void
  (e: 'delete', resumeId: string): void
  (e: 'send-email', resumeId: string): void
}>()

/** 处理发送邮件 */
function handleSendEmail(): void {
  emit('send-email', props.resume.resume_id)
}
```

```scss
/* frontend/src/components/resume/ResumeCard.vue style 追加 */
  &__foot-right {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  &__action-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    padding: 0;
    border: 1px solid var(--color-line);
    background: var(--color-bg-card);
    cursor: pointer;
    color: var(--color-ink-mute);
    border-radius: var(--radius-sm);
    transition: color var(--duration-fast) var(--ease-out),
      border-color var(--duration-fast) var(--ease-out);

    &:hover {
      color: var(--color-accent);
      border-color: var(--color-accent-soft);
    }
    .el-icon {
      font-size: 14px;
    }
  }
```

- [ ] **Step 2: 修改 ResumeList.vue 处理 send-email 事件**

```vue
<!-- frontend/src/views/ResumeList.vue 模板中 ResumeCard 添加 @send-email -->
            <ResumeCard
              :resume="resume"
              @click="handleClickResume"
              @toggle-favorite="handleToggleFavorite"
              @delete="handleDeleteResume"
              @send-email="handleSendEmail"
            />
```

```typescript
// frontend/src/views/ResumeList.vue script 部分
// 引入 SendEmailDialog 和 ref：
import SendEmailDialog from '@/components/email/SendEmailDialog.vue'
import { getResumeDetail } from '@/api/resume'

const sendEmailDialogRef = ref<InstanceType<typeof SendEmailDialog>>()

// 追加 handleSendEmail 方法：
/**
 * 从卡片发送邮件：拉取详情后打开邮件对话框
 */
async function handleSendEmail(resumeId: string): Promise<void> {
  try {
    const detail = await getResumeDetail(resumeId)
    sendEmailDialogRef.value?.open({
      variables: {
        candidate_name: detail.basic_info?.name ?? detail.name ?? '',
        position: '',
        company: 'TalentSense',
        salary: `${detail.expected_salary?.min ?? ''}-${detail.expected_salary?.max ?? ''}K`,
        interview_time: '',
      },
    })
  } catch (err) {
    const msg = err instanceof Error ? err.message : '加载简历信息失败'
    ElMessage.error(msg)
  }
}
```

在模板底部 UploadDialog 后追加：
```vue
    <!-- 发送邮件对话框 -->
    <SendEmailDialog ref="sendEmailDialogRef" />
```

- [ ] **Step 3: 写卡片操作按钮测试**

```typescript
// frontend/tests/components/test_resume_components.test.ts 追加
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ResumeCard from '@/components/resume/ResumeCard.vue'

describe('ResumeCard 操作按钮', () => {
  it('应显示发送邮件按钮', () => {
    const wrapper = mount(ResumeCard, {
      props: {
        resume: {
          resume_id: 'r1', candidate_id: 'c1', name: '张三',
          education: '本科', skills: [], expected_salary: { min: 20, max: 30 },
          tags: [], is_favorite: false, parse_status: 'completed',
          education_level: 1, work_years: 5, created_at: ''
        }
      },
      global: { stubs: ['el-icon', 'el-tag'] }
    })
    const btn = wrapper.find('.resume-card__action-btn')
    expect(btn.exists()).toBe(true)
    expect(btn.attributes('aria-label')).toBe('发送邮件')
  })

  it('点击发送邮件按钮应 emit send-email', async () => {
    const wrapper = mount(ResumeCard, {
      props: {
        resume: {
          resume_id: 'r1', candidate_id: 'c1', name: '张三',
          education: '本科', skills: [], expected_salary: { min: 20, max: 30 },
          tags: [], is_favorite: false, parse_status: 'completed',
          education_level: 1, work_years: 5, created_at: ''
        }
      },
      global: { stubs: ['el-icon', 'el-tag'] }
    })
    await wrapper.find('.resume-card__action-btn').trigger('click')
    expect(wrapper.emitted('send-email')).toBeTruthy()
    expect(wrapper.emitted('send-email')![0]).toEqual(['r1'])
  })
})
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npm run test -- test_resume_components.test.ts`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd frontend
git add src/components/resume/ResumeCard.vue src/views/ResumeList.vue tests/components/test_resume_components.test.ts
git commit -m "feat: 简历卡片右下角添加发送邮件按钮(联动SendEmailDialog)"
```

---

## Task 9: 邮件变量占位符改为有含义的词（前端）

**Files:**
- Modify: `frontend/src/components/email/SendEmailDialog.vue:62-69,227-229`（变量标签 + placeholder）
- Modify: `frontend/src/views/EmailCenter.vue:72-78,278-281`（变量标签 + placeholder）
- Modify: `frontend/src/utils/constant.ts`（添加变量标签映射）
- Test: `frontend/tests/components/test_resume_components.test.ts`

**Interfaces:**
- Consumes: 模板变量名
- Produces: 中文标签 + 描述性 placeholder

- [ ] **Step 1: 添加变量标签映射到 constant.ts**

```typescript
// frontend/src/utils/constant.ts 追加：

/** 邮件模板变量 → 中文标签 + placeholder 映射 */
export const EMAIL_VAR_LABELS: Record<string, { label: string; placeholder: string }> = {
  candidate_name: { label: '候选人姓名', placeholder: '如：张三' },
  company: { label: '公司名称', placeholder: '如：TalentSense' },
  position: { label: '应聘职位', placeholder: '如：Java高级工程师' },
  salary: { label: '薪资范围', placeholder: '如：20-30K' },
  interview_time: { label: '面试时间', placeholder: '如：2026-07-01 14:00' },
  interviewer: { label: '面试官', placeholder: '如：李经理' },
  location: { label: '面试地点', placeholder: '如：线上面试/北京市朝阳区XX大厦' },
  date: { label: '日期', placeholder: '如：2026-07-01' },
  onboarding_date: { label: '入职日期', placeholder: '如：2026-08-01' },
  department: { label: '部门', placeholder: '如：技术部' },
  phone: { label: '联系电话', placeholder: '如：010-12345678' },
}
```

- [ ] **Step 2: 修改 SendEmailDialog.vue 变量标签和 placeholder**

```vue
<!-- frontend/src/components/email/SendEmailDialog.vue 变量填写区块替换 -->
        <el-form-item v-if="selectedTemplate && templateVariables.length" label="变量填写">
          <div class="send-dialog__vars">
            <div v-for="v in templateVariables" :key="v" class="send-dialog__var-item">
              <span class="send-dialog__var-label">{{ getVarLabel(v) }}</span>
              <el-input v-model="form.variables[v]" :placeholder="getVarPlaceholder(v)" />
            </div>
          </div>
        </el-form-item>
```

```typescript
// frontend/src/components/email/SendEmailDialog.vue script 部分
// import 追加：
import { EMAIL_VAR_LABELS } from '@/utils/constant'

// 替换 formatVarLabel 函数为：
/** 获取变量中文标签 */
function getVarLabel(v: string): string {
  return EMAIL_VAR_LABELS[v]?.label ?? v
}

/** 获取变量 placeholder */
function getVarPlaceholder(v: string): string {
  return EMAIL_VAR_LABELS[v]?.placeholder ?? '请输入变量值'
}
```

- [ ] **Step 3: 修改 EmailCenter.vue 变量标签和 placeholder**

```vue
<!-- frontend/src/views/EmailCenter.vue 变量填写区块替换 -->
              <el-form-item v-if="selectedTemplate && templateVariables.length" label="变量填写">
                <div class="send-card__vars">
                  <div v-for="v in templateVariables" :key="v" class="send-card__var-item">
                    <span class="send-card__var-label">{{ getVarLabel(v) }}</span>
                    <el-input v-model="sendForm.variables[v]" :placeholder="getVarPlaceholder(v)" />
                  </div>
                  <EmptyState v-if="templateVariables.length === 0" text="此模板无需变量" />
                </div>
              </el-form-item>
```

```typescript
// frontend/src/views/EmailCenter.vue script 部分
// import 追加：
import { EMAIL_VAR_LABELS } from '@/utils/constant'

// 替换 formatVarLabel 函数为：
/** 获取变量中文标签 */
function getVarLabel(v: string): string {
  return EMAIL_VAR_LABELS[v]?.label ?? v
}

/** 获取变量 placeholder */
function getVarPlaceholder(v: string): string {
  return EMAIL_VAR_LABELS[v]?.placeholder ?? '请输入变量值'
}
```

- [ ] **Step 4: 写变量标签映射测试**

```typescript
// frontend/tests/components/test_resume_components.test.ts 追加
import { EMAIL_VAR_LABELS } from '@/utils/constant'

describe('邮件变量标签映射', () => {
  it('常见变量应有中文标签', () => {
    expect(EMAIL_VAR_LABELS.candidate_name.label).toBe('候选人姓名')
    expect(EMAIL_VAR_LABELS.company.label).toBe('公司名称')
    expect(EMAIL_VAR_LABELS.position.label).toBe('应聘职位')
    expect(EMAIL_VAR_LABELS.salary.label).toBe('薪资范围')
    expect(EMAIL_VAR_LABELS.interview_time.label).toBe('面试时间')
  })

  it('常见变量应有描述性 placeholder', () => {
    expect(EMAIL_VAR_LABELS.candidate_name.placeholder).toContain('张三')
    expect(EMAIL_VAR_LABELS.position.placeholder).toContain('Java')
    expect(EMAIL_VAR_LABELS.salary.placeholder).toContain('K')
    expect(EMAIL_VAR_LABELS.interview_time.placeholder).toContain('2026')
  })
})
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd frontend && npm run test -- test_resume_components.test.ts`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
cd frontend
git add src/utils/constant.ts src/components/email/SendEmailDialog.vue src/views/EmailCenter.vue tests/components/test_resume_components.test.ts
git commit -m "feat: 邮件变量占位符改为中文标签+描述性placeholder"
```

---

## Task 10: 全量测试验证 + 最终提交

**Files:**
- 无新文件，仅运行全量测试

- [ ] **Step 1: 运行后端全量测试**

Run: `cd backend && .venv\Scripts\python.exe -m pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 2: 运行前端全量测试**

Run: `cd frontend && npm run test`
Expected: 全部 PASS

- [ ] **Step 3: 启动后端验证集成**

Run: `cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload`
Expected: 启动日志包含 "BGE-M3 模型已预热"

- [ ] **Step 4: 手动验证清单**

- [ ] 上传多个简历文件（批量上传）
- [ ] 上传同一简历勾选"覆盖重复"（旧简历被删除）
- [ ] 在搜索框输入标签关键词（能搜到结果）
- [ ] 点击"重置"按钮（列表刷新为全部）
- [ ] 删除简历（列表自动刷新，选中状态清除）
- [ ] 导出选中简历（xlsx 有内容）
- [ ] 打开简历详情（能看到"项目经历"区块）
- [ ] 简历卡片右下角（有发送邮件按钮，点击弹出对话框）
- [ ] 发送邮件对话框变量填写（标签为中文，placeholder 有示例）

- [ ] **Step 5: 最终提交（如有遗留改动）**

```bash
git add -A
git commit -m "test: 全量测试通过(后端+前端)"
```

---

## 自检清单

| 规格要求 | 对应 Task |
|---------|----------|
| 批量上传 | Task 5 |
| 解析速度优化（BGE-M3 预热） | Task 4 |
| 标签搜索支持 | Task 3 |
| 重置自动刷新 | Task 6 |
| 删除自动刷新 | Task 6 |
| 导出 xlsx 有内容 | Task 2 |
| 覆盖重复简历生效 | Task 1 |
| 项目经历提取展示 | Task 4 + Task 7 |
| 卡片发送邮件按钮 | Task 8 |
| 邮件变量占位符有含义 | Task 9 |
