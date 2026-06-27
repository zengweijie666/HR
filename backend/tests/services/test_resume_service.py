"""
文件名: tests/services/test_resume_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: ResumeService 单元测试，覆盖上传/解析/去重/脱敏/CRUD
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.resume_service import ResumeService


@pytest.fixture
def svc():
    """构造所有依赖均被 mock 的 ResumeService"""
    s = ResumeService()
    s.resumes_coll = AsyncMock()
    s.minio = MagicMock()
    s.ocr = MagicMock()
    s.llm = AsyncMock()
    s.embedding = MagicMock()
    s.vector_store = AsyncMock()
    return s


@pytest.mark.asyncio
async def test_upload_returns_parsing_status(svc):
    """AC2.1: 上传 PDF 返回 parsing"""
    svc.minio.upload_bytes.return_value = "minio_xxx"
    result = await svc.upload(b"pdf-bytes", "test.pdf", "application/pdf")
    assert result["parse_status"] == "parsing"
    assert result["resume_id"].startswith("res_")
    svc.minio.upload_bytes.assert_called_once()


@pytest.mark.asyncio
async def test_parse_duplicate_detected(svc):
    """AC2.3: 重复简历返回 is_duplicate=true"""
    svc.minio.upload_bytes.return_value = "minio_xxx"
    svc.llm.chat = AsyncMock(return_value='{"name":"张三","phone":"13812341234","email":"a@b.com"}')
    svc.dedup_checker = AsyncMock()
    svc.dedup_checker.check = AsyncMock(return_value="res_existing")
    # 直接调内部解析方法
    await svc._parse_and_index("res_new", b"pdf", "minio_xxx", "test.pdf", overwrite=False)
    svc.resumes_coll.update_one.assert_called()
    args = svc.resumes_coll.update_one.call_args
    assert args.kwargs["update"]["$set"]["is_duplicate"] is True


@pytest.mark.asyncio
async def test_get_detail_not_found(svc):
    """AC4.4: 不存在返回 1004"""
    svc.resumes_coll.find_one = AsyncMock(return_value=None)
    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        await svc.get_detail("res_xxx")


@pytest.mark.asyncio
async def test_get_detail_masks_phone(svc):
    """AC4.2: 手机号脱敏"""
    svc.resumes_coll.find_one = AsyncMock(return_value={
        "resume_id": "r1", "candidate_id": "c1", "basic_info": {"name": "x", "phone_masked": "138****1234", "email_masked": "a***@b.com"},
        "education": "本科", "education_level": 1, "work_years": 5, "skills": [],
        "expected_salary": {"min": 20, "max": 30}, "tags": [], "is_favorite": False,
        "parse_status": "completed", "created_at": "x", "interview_notes": []
    })
    detail = await svc.get_detail("r1")
    assert detail["basic_info"]["phone_masked"] == "138****1234"


@pytest.mark.asyncio
async def test_delete_cleans_all(svc):
    """AC6.1-6.4: 删除清理三处"""
    svc.resumes_coll.find_one = AsyncMock(return_value={"file_info": {"file_id": "minio_xxx"}})
    await svc.delete("r1")
    svc.minio.delete.assert_called_once_with("minio_xxx")
    svc.resumes_coll.delete_one.assert_called_once()
    svc.vector_store.delete_by_resume_id.assert_called_once_with("r1")


@pytest.mark.asyncio
async def test_list_with_filters(svc):
    """AC3.2-3.6"""
    svc.resumes_coll.count_documents = AsyncMock(return_value=1)
    # motor 的 find() 是同步返回 cursor，需用 MagicMock 而非 AsyncMock
    svc.resumes_coll.find = MagicMock()
    # mock 链: find().skip().limit().sort().to_list()
    svc.resumes_coll.find.return_value.skip.return_value.limit.return_value.sort.return_value.to_list = AsyncMock(return_value=[{
        "resume_id": "r1", "candidate_id": "c1", "name": "张三", "education": "本科",
        "education_level": 1, "work_years": 5, "skills": ["Java"],
        "expected_salary": {"min": 20, "max": 30}, "tags": [], "is_favorite": False,
        "parse_status": "completed", "created_at": "x"
    }])
    result = await svc.list(keyword="Java", page=1, page_size=20)
    assert result["total"] == 1
    assert len(result["list"]) == 1


@pytest.mark.asyncio
async def test_preview_url(svc):
    """AC5.1"""
    svc.resumes_coll.find_one = AsyncMock(return_value={"file_info": {"file_id": "minio_xxx", "file_type": "pdf"}})
    svc.minio.presigned_url.return_value = "http://signed"
    result = await svc.get_preview_url("r1")
    assert result["preview_url"] == "http://signed"
    assert result["file_type"] == "pdf"


@pytest.mark.asyncio
async def test_parse_overwrite_deletes_existing(svc):
    """overwrite=True 且检测到重复时，应删除旧简历（MinIO + MongoDB + Milvus）"""
    # mock _extract_text 返回有效文本（避免 fitz 解析 b"pdf" 报错）
    svc._extract_text = MagicMock(return_value="张三 13812341234 a@b.com")
    svc.llm.chat = AsyncMock(return_value='{"name":"张三","phone":"13812341234","email":"a@b.com","skills":[],"work_experience":[],"education_detail":[],"projects":[]}')
    svc.dedup_checker = AsyncMock()
    svc.dedup_checker.check = AsyncMock(return_value="res_existing")
    # 旧简历文档查找返回 file_id
    svc.resumes_coll.find_one = AsyncMock(return_value={
        "resume_id": "res_existing",
        "file_info": {"file_id": "minio_old"}
    })
    # mock embedding.encode 返回 (dense, sparse) 二元组
    svc.embedding.encode = MagicMock(return_value=([[0.1]], [[0.2]]))
    await svc._parse_and_index("res_new", b"pdf", "minio_new", "test.pdf", overwrite=True)
    # 验证删除了旧简历的 MinIO 文件
    svc.minio.delete.assert_called_with("minio_old")
    # 验证删除了旧简历的 MongoDB 记录
    svc.resumes_coll.delete_one.assert_any_call({"resume_id": "res_existing"})
    # 验证删除了旧简历的 Milvus 向量
    svc.vector_store.delete_by_resume_id.assert_any_call("res_existing")


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
