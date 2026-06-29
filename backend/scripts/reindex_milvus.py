"""
文件名: scripts/reindex_milvus.py
创建时间: 2026-06-28
作者: TalentSense Team
功能描述: 对 MongoDB 中已有简历重新索引 Milvus 向量（修复 scalar 字段硬编码问题）
使用方式: cd backend && .venv/Scripts/python.exe -m scripts.reindex_milvus
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import MongoDB, RedisClient
from app.core.milvus_client import milvus_client
from app.core.vector_store import vector_store
from app.core.embedding import embedding_model
from app.core.logger import logger
from app.utils.chunker import split_parent_child


def _doc_to_text(doc: dict) -> str:
    """将 MongoDB resume 文档拼接为用于向量索引的全文文本

    入参:
        doc: MongoDB resumes 集合文档
    出参:
        拼接后的纯文本
    """
    parts = []
    basic = doc.get("basic_info", {}) or {}
    name = basic.get("name", "") or doc.get("name", "")
    if name:
        parts.append(f"姓名：{name}")
    edu = doc.get("education", "")
    if edu:
        parts.append(f"学历：{edu}")
    wy = doc.get("work_years", 0)
    parts.append(f"工作年限：{wy}年")
    skills = doc.get("skills", []) or []
    if skills:
        parts.append(f"技能：{'、'.join(skills)}")
    summary = doc.get("summary", "") or ""
    if summary:
        parts.append(f"个人总结：{summary}")

    # 工作经历
    for w in doc.get("work_experience", []) or []:
        co = w.get("company", "")
        pos = w.get("position", "")
        desc = w.get("description", "")
        parts.append(f"工作经历：{co} {pos} {desc}")

    # 项目经历
    for p in doc.get("projects", []) or []:
        pname = p.get("name", "")
        pdesc = p.get("description", "") or ""
        prole = p.get("role", "")
        parts.append(f"项目经历：{pname} {prole} {pdesc}")

    # 教育经历
    for e in doc.get("education_detail", []) or []:
        school = e.get("school", "")
        major = e.get("major", "")
        degree = e.get("degree", "")
        parts.append(f"教育经历：{school} {major} {degree}")

    return "\n".join(parts)


async def reindex_all():
    """重新索引所有简历到 Milvus"""
    # 1. 连接 MongoDB
    await MongoDB.connect()
    if MongoDB.db is None:
        logger.error("MongoDB 连接失败")
        return

    # 2. 确保 Milvus collection 存在
    milvus_client.ensure_collection()

    coll = MongoDB.db.resumes
    cursor = coll.find({"parse_info.parse_status": "completed"})
    docs = await cursor.to_list(length=1000)
    logger.info(f"待重新索引简历数: {len(docs)}")

    success = 0
    for doc in docs:
        rid = doc.get("resume_id", "")
        if not rid:
            continue
        try:
            # 拼接文本
            text = _doc_to_text(doc)
            if not text.strip():
                logger.warning(f"简历 {rid} 文本为空，跳过")
                continue

            # 删除旧向量
            try:
                await vector_store.delete_by_resume_id(rid)
            except Exception as del_err:
                logger.warning(f"删除旧向量失败（可忽略）: {rid}, {del_err}")

            # 切分
            children, parents = split_parent_child(text)

            # 编码
            dense, sparse = embedding_model.encode([c.content for c in children])

            # 元数据
            work_years = int(doc.get("work_years", 0) or 0)
            education_level = int(doc.get("education_level", 1) or 1)
            salary = doc.get("expected_salary", {}) or {}
            salary_min = int(salary.get("min", 0) or 0)
            salary_max = int(salary.get("max", 0) or 0)
            skills = doc.get("skills", []) or []
            skills_text = " ".join(skills)

            # 插入
            await vector_store.insert(
                children, dense, sparse, parents, rid,
                work_years=work_years,
                education_level=education_level,
                salary_min=salary_min,
                salary_max=salary_max,
                skills_text=skills_text,
            )
            logger.info(f"重新索引完成: {rid} ({doc.get('basic_info', {}).get('name', '')}), "
                        f"chunks={len(children)}, wy={work_years}, edu={education_level}, "
                        f"sal={salary_min}-{salary_max}K")
            success += 1
        except Exception as e:
            logger.error(f"重新索引失败: {rid}, {e}", exc_info=True)

    logger.info(f"重新索引完成: 成功 {success}/{len(docs)}")
    await MongoDB.disconnect()


if __name__ == "__main__":
    asyncio.run(reindex_all())
