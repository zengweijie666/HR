"""
文件名: app/services/export_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: Excel 导出服务，使用 openpyxl
入参: candidate_ids / columns
出参: Excel 字节流
对应 Business-Requirements F14
"""
import io
from openpyxl import Workbook
from app.core.database import MongoDB
from app.core.logger import logger


COLUMN_MAP = {
    "name": "姓名",
    "gender": "性别",
    "age": "年龄",
    "education": "学历",
    "work_years": "工作年限",
    "skills": "技能",
    "expected_salary": "期望薪资(K)",
    "tags": "标签",
    "phone_masked": "手机号(脱敏)",
    "email_masked": "邮箱(脱敏)",
    "location": "所在地",
}


class ExportService:
    """Excel 导出服务"""

    def __init__(self):
        pass

    @property
    def resumes_coll(self):
        """延迟获取 MongoDB resumes collection（避免模块导入时 MongoDB 未连接）"""
        if hasattr(self, "_resumes_coll"):
            return self._resumes_coll
        return MongoDB.db.resumes if MongoDB.db is not None else None

    @resumes_coll.setter
    def resumes_coll(self, value):
        """测试注入用"""
        self._resumes_coll = value

    async def export_excel(self, resume_ids: list[str], columns: list[str]) -> bytes:
        """AC14.1-14.3: 导出 Excel

        入参:
            resume_ids: 简历 ID 列表（对应 resumes 集合的 resume_id 字段）
            columns: 导出列名（英文键）
        出参:
            Excel 文件字节流
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "候选人列表"

        # 写表头
        headers = [COLUMN_MAP.get(c, c) for c in columns]
        ws.append(headers)

        # 拉取数据
        docs: list[dict] = []
        if resume_ids and self.resumes_coll is not None:
            cursor = self.resumes_coll.find({"resume_id": {"$in": resume_ids}})
            docs = await cursor.to_list(length=len(resume_ids))

        for doc in docs:
            # basic_info 下的字段扁平化读取（name/gender/age/location/phone_masked/email_masked）
            basic = doc.get("basic_info") or {}
            row = []
            for col in columns:
                if col in ("name", "gender", "age", "location", "phone_masked", "email_masked"):
                    val = basic.get(col, "") or doc.get(col, "")
                else:
                    val = doc.get(col, "")
                if col in ("skills", "tags") and isinstance(val, list):
                    val = "、".join(val)
                elif col == "expected_salary" and isinstance(val, dict):
                    val = f"{val.get('min', 0)}-{val.get('max', 0)}"
                row.append(val)
            ws.append(row)

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        logger.info(f"导出 Excel: {len(docs)} 条记录, 列={columns}")
        return buf.getvalue()


export_service = ExportService()
