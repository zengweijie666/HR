"""
文件名: app/services/user_service.py
创建时间: 2026-06-27
作者: TalentSense Team
功能描述: 用户管理业务逻辑（列表/创建/审批/启用禁用/重置密码/删除）
入参: user_id / username / password / status / role
出参: 用户列表 / 用户详情 / 操作结果
对应 Business-Requirements F01 扩展
"""
import uuid
from datetime import datetime, timezone
from app.core.database import MongoDB
from app.core.exceptions import BizError, AuthError, NotFoundError, ConflictError
from app.core.logger import logger
from app.services.auth_service import AuthService


class UserService:
    """用户管理服务"""

    def __init__(self):
        pass

    @property
    def users_coll(self):
        """延迟获取 MongoDB users collection"""
        if hasattr(self, "_users_coll"):
            return self._users_coll
        return MongoDB.db.users if MongoDB.db is not None else None

    @users_coll.setter
    def users_coll(self, value):
        """测试注入用"""
        self._users_coll = value

    async def list_users(self, page: int = 1, page_size: int = 20,
                         status: str | None = None, role: str | None = None,
                         keyword: str | None = None) -> dict:
        """分页列表查询

        入参:
            page: 页码
            page_size: 每页数量
            status: 状态筛选
            role: 角色筛选
            keyword: 用户名/姓名关键词
        出参:
            {list, total, page, page_size, total_pages}
        """
        query: dict = {}
        if status:
            query["status"] = status
        if role:
            query["role"] = role
        if keyword:
            query["$or"] = [
                {"username": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}},
            ]
        cursor = self.users_coll.find(query, {"password_hash": 0, "_id": 0})
        list_data = await cursor.skip((page - 1) * page_size).limit(page_size).to_list(length=page_size)
        total = await self.users_coll.count_documents(query)
        return {
            "list": list_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    async def create_user(self, username: str, password: str, role: str = "hr",
                          email: str | None = None, name: str | None = None) -> dict:
        """管理员直接开号（status=approved）

        入参:
            username: 用户名
            password: 明文密码
            role: 角色 admin/hr
            email: 邮箱
            name: 显示名
        出参:
            用户信息
        异常:
            ConflictError: 用户名已存在
        """
        existing = await self.users_coll.find_one({"username": username})
        if existing:
            raise ConflictError("用户名已存在")
        user_id = f"u_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "user_id": user_id,
            "username": username,
            "password_hash": AuthService.hash_password(password),
            "email": email,
            "name": name or username,
            "role": role,
            "status": "approved",
            "created_at": now,
            "updated_at": now,
        }
        await self.users_coll.insert_one(doc)
        logger.info(f"管理员创建用户: {username} ({role})")
        doc.pop("password_hash", None)
        doc.pop("_id", None)
        return doc

    async def _get_or_404(self, user_id: str) -> dict:
        """获取用户，不存在抛 NotFoundError"""
        doc = await self.users_coll.find_one({"user_id": user_id}, {"password_hash": 0, "_id": 0})
        if not doc:
            raise NotFoundError("用户不存在")
        return doc

    async def get_user(self, user_id: str) -> dict:
        """获取用户详情"""
        return await self._get_or_404(user_id)

    async def approve(self, user_id: str) -> None:
        """审批通过（pending → approved）"""
        await self._get_or_404(user_id)
        await self.users_coll.update_one(
            {"user_id": user_id},
            {"$set": {"status": "approved", "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        logger.info(f"用户 {user_id} 审批通过")

    async def reject(self, user_id: str) -> None:
        """拒绝申请（直接删除记录）"""
        await self._get_or_404(user_id)
        await self.users_coll.delete_one({"user_id": user_id})
        logger.info(f"用户 {user_id} 申请被拒绝（已删除）")

    async def update_status(self, user_id: str, status: str) -> None:
        """启用/禁用账号

        入参:
            user_id: 用户 ID
            status: approved / disabled
        """
        await self._get_or_404(user_id)
        await self.users_coll.update_one(
            {"user_id": user_id},
            {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        logger.info(f"用户 {user_id} 状态变更为 {status}")

    async def reset_password(self, user_id: str, new_password: str) -> None:
        """管理员重置密码"""
        await self._get_or_404(user_id)
        await self.users_coll.update_one(
            {"user_id": user_id},
            {"$set": {"password_hash": AuthService.hash_password(new_password),
                      "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        logger.info(f"用户 {user_id} 密码已重置")

    async def delete(self, user_id: str, current_user_id: str | None = None) -> None:
        """删除账号（硬删除）

        入参:
            user_id: 待删除用户 ID
            current_user_id: 当前操作者 ID（防止自删）
        异常:
            AuthError: 试图删除自己
        """
        if current_user_id and user_id == current_user_id:
            raise AuthError("不能删除自己")
        await self._get_or_404(user_id)
        await self.users_coll.delete_one({"user_id": user_id})
        logger.info(f"用户 {user_id} 已删除")


user_service = UserService()
