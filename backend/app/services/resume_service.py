"""
文件名: app/services/resume_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 简历服务，对应 API-Design.md 二、Resumes
入参: 文件字节 / resume_id / 查询条件
出参: UploadResponse / ResumeDetail / PageResult
对应 Business-Requirements F02-F06
"""
import json
import uuid
from datetime import datetime, timezone
from app.core.config import settings
from app.core.exceptions import NotFoundError, ResumeParseError
from app.core.logger import logger
from app.core.minio_client import minio_client
from app.core.ocr import ocr_engine
from app.core.llm_client import llm_client
from app.core.database import MongoDB
from app.utils.pii import mask_phone, mask_email, hash_phone, hash_email
from app.utils.dedup import DedupChecker
from app.utils.chunker import split_parent_child
from app.utils.salary import parse_salary


class ResumeService:
    """简历服务"""

    def __init__(self):
        self.resumes_coll = MongoDB.db.resumes if MongoDB.db else None
        self.minio = minio_client
        self.ocr = ocr_engine
        self.llm = llm_client
        # embedding/reranker/vector_store 后续注入
        from app.core.embedding import embedding_model
        from app.core.vector_store import vector_store
        self.embedding = embedding_model
        self.vector_store = vector_store
        self.dedup_checker = None  # 默认在 _parse_and_index 内按需创建

    async def upload(self, file_bytes: bytes, file_name: str, content_type: str, overwrite: bool = False) -> dict:
        """AC2.1: 上传文件 → MinIO → 异步解析

        入参:
            file_bytes: 文件字节
            file_name: 文件名
            content_type: MIME 类型
            overwrite: 重复时是否覆盖
        出参:
            {"resume_id", "candidate_id", "file_name", "parse_status", "is_duplicate", "duplicate_with"}
        """
        file_id = self.minio.upload_bytes(file_bytes, file_name, content_type)
        resume_id = f"res_{uuid.uuid4().hex[:12]}"
        candidate_id = f"cand_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        await self.resumes_coll.insert_one({
            "resume_id": resume_id, "candidate_id": candidate_id,
            "file_info": {"file_id": file_id, "file_name": file_name, "file_type": file_name.split(".")[-1]},
            "parse_info": {"parse_status": "parsing", "parse_time": None},
            "tags": [], "is_favorite": False, "notes": "",
            "created_at": now, "updated_at": now,
        })
        # 后台触发解析（此处简化为同步调用，生产用 BackgroundTasks）
        await self._parse_and_index(resume_id, file_bytes, file_id, file_name, overwrite)
        return {
            "resume_id": resume_id, "candidate_id": candidate_id, "file_name": file_name,
            "parse_status": "parsing", "is_duplicate": False, "duplicate_with": None,
        }

    async def _parse_and_index(self, resume_id: str, file_bytes: bytes, file_id: str, file_name: str, overwrite: bool):
        """解析全链路：提取文本 → LLM 结构化 → 去重 → 脱敏 → 父子块 → 入库

        异常会被捕获并标记 parse_status=failed，不会向上抛出。
        """
        try:
            # 1. 文本提取（两级降级）
            text = self._extract_text(file_bytes, file_name)
            # 2. LLM 结构化提取
            structured = await self._llm_extract(text)
            # 3. 去重
            phone_h = hash_phone(structured.get("phone", ""))
            email_h = hash_email(structured.get("email", ""))
            dedup_checker = self.dedup_checker or DedupChecker(self.resumes_coll)
            existing = await dedup_checker.check(phone_h, email_h)
            if existing and not overwrite:
                await self.resumes_coll.update_one(
                    {"resume_id": resume_id},
                    update={"$set": {
                        "is_duplicate": True, "duplicate_with": existing,
                        "parse_info": {"parse_status": "completed", "parse_time": datetime.now(timezone.utc).isoformat()},
                    }},
                )
                logger.info(f"简历 {resume_id} 重复，关联 {existing}")
                return
            # 4. 父子块切分
            children, parents = split_parent_child(text)
            # 5. BGE-M3 编码
            dense, sparse = self.embedding.encode([c.content for c in children])
            # 6. 写入 Milvus
            await self.vector_store.insert(children, dense, sparse, parents, resume_id)
            # 7. 更新 MongoDB 元数据
            salary = parse_salary(structured.get("salary", "")) or {"min": 0, "max": 0}
            now = datetime.now(timezone.utc).isoformat()
            await self.resumes_coll.update_one(
                {"resume_id": resume_id},
                update={"$set": {
                    "basic_info": {
                        "name": structured.get("name", ""),
                        "phone_masked": mask_phone(structured.get("phone", "")),
                        "email_masked": mask_email(structured.get("email", "")),
                        "phone_hash": phone_h, "email_hash": email_h,
                        "gender": structured.get("gender"), "age": structured.get("age"),
                        "location": structured.get("location"),
                    },
                    "education": structured.get("education", ""), "education_level": structured.get("education_level", 1),
                    "work_years": structured.get("work_years", 0), "skills": structured.get("skills", []),
                    "work_experience": structured.get("work_experience", []),
                    "education_detail": structured.get("education_detail", []),
                    "summary": structured.get("summary", ""),
                    "expected_salary": salary,
                    "parse_info": {"parse_status": "completed", "parse_time": now},
                    "updated_at": now,
                }},
            )
            logger.info(f"简历 {resume_id} 解析完成")
        except Exception as e:
            logger.exception(f"简历 {resume_id} 解析失败: {e}")
            await self.resumes_coll.update_one(
                {"resume_id": resume_id},
                update={"$set": {"parse_info": {"parse_status": "failed", "parse_time": datetime.now(timezone.utc).isoformat()}}},
            )

    def _extract_text(self, file_bytes: bytes, file_name: str) -> str:
        """两级降级：PyMuPDF/python-docx → RapidOCR

        入参:
            file_bytes: 文件字节
            file_name: 文件名（用于判断扩展名）
        出参:
            提取的文本
        异常:
            ResumeParseError: 不支持的文件格式
        """
        ext = file_name.split(".")[-1].lower()
        if ext == "pdf":
            try:
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                return "\n".join(page.get_text() for page in doc)
            except Exception:
                return self.ocr.extract_text(file_bytes)
        elif ext == "docx":
            try:
                import io
                from docx import Document
                doc = Document(io.BytesIO(file_bytes))
                return "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                return self.ocr.extract_text(file_bytes)
        elif ext in ("png", "jpg", "jpeg"):
            return self.ocr.extract_text(file_bytes)
        raise ResumeParseError(f"不支持的文件格式: {ext}")

    async def _llm_extract(self, text: str) -> dict:
        """LLM 结构化提取

        入参:
            text: 简历文本
        出参:
            结构化字典，失败返回 {}
        """
        from app.agent.prompts import RESUME_EXTRACT_PROMPT
        prompt = RESUME_EXTRACT_PROMPT.format(text=str(text)[:4000])
        result = await self.llm.chat([
            {"role": "system", "content": "你是简历解析助手，必须返回 JSON"},
            {"role": "user", "content": prompt},
        ])
        try:
            return json.loads(result)
        except Exception:
            logger.error(f"LLM 返回非 JSON: {str(result)[:200]}")
            return {}

    async def get_detail(self, resume_id: str) -> dict:
        """AC4.1-4.4: 获取简历详情

        入参:
            resume_id: 简历 ID
        出参:
            简历详情字典
        异常:
            NotFoundError: 简历不存在
        """
        doc = await self.resumes_coll.find_one({"resume_id": resume_id})
        if not doc:
            raise NotFoundError("简历不存在")
        return doc

    async def list(self, page: int = 1, page_size: int = 20, keyword: str = None, tag: str = None,
                   is_favorite: bool = None, education_min: int = None, work_years_min: int = None,
                   salary_min: int = None, salary_max: int = None, status: str = None) -> dict:
        """AC3.1-3.8: 分页列表查询

        入参:
            page: 页码（从 1 开始）
            page_size: 每页条数
            keyword: 姓名/技能关键词
            tag: 标签过滤
            is_favorite: 收藏过滤
            education_min: 最低学历
            work_years_min: 最低工作年限
            salary_min / salary_max: 薪资区间
            status: 解析状态过滤
        出参:
            {"list", "total", "page", "page_size", "total_pages"}
        """
        query = {}
        if keyword:
            query["$or"] = [
                {"basic_info.name": {"$regex": keyword}},
                {"skills": {"$regex": keyword}},
            ]
        if tag:
            query["tags"] = tag
        if is_favorite is not None:
            query["is_favorite"] = is_favorite
        if education_min is not None:
            query["education_level"] = {"$gte": education_min}
        if work_years_min is not None:
            query["work_years"] = {"$gte": work_years_min}
        if salary_max is not None:
            query["expected_salary.min"] = {"$lte": salary_max}
        if status:
            query["parse_info.parse_status"] = status
        total = await self.resumes_coll.count_documents(query)
        skip = (page - 1) * page_size
        cursor = self.resumes_coll.find(query).skip(skip).limit(page_size).sort("created_at", -1)
        items = await cursor.to_list(length=page_size)
        return {
            "list": items, "total": total, "page": page, "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def delete(self, resume_id: str) -> None:
        """AC6.1-6.4: 清理 MinIO/MongoDB/Milvus

        入参:
            resume_id: 简历 ID
        """
        doc = await self.resumes_coll.find_one({"resume_id": resume_id}, {"file_info": 1})
        if doc and doc.get("file_info", {}).get("file_id"):
            self.minio.delete(doc["file_info"]["file_id"])
        await self.resumes_coll.delete_one({"resume_id": resume_id})
        await self.vector_store.delete_by_resume_id(resume_id)

    async def get_preview_url(self, resume_id: str) -> dict:
        """AC5.1-5.2: 生成文件预签名 URL

        入参:
            resume_id: 简历 ID
        出参:
            {"preview_url", "file_type", "expires_in"}
        异常:
            NotFoundError: 简历不存在
        """
        doc = await self.resumes_coll.find_one({"resume_id": resume_id}, {"file_info": 1})
        if not doc:
            raise NotFoundError("简历不存在")
        url = self.minio.presigned_url(doc["file_info"]["file_id"])
        return {"preview_url": url, "file_type": doc["file_info"]["file_type"], "expires_in": 3600}
