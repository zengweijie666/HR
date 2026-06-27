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
