"""
文件名: app/services/auth_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 认证服务，JWT 生成/校验 + Redis Token 黑名单
入参: username/password/token
出参: TokenResponse / UserInfo
对应 Business-Requirements F01
"""
from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings
from app.core.exceptions import AuthError
from app.core.logger import logger
from app.models.auth import TokenResponse, UserInfo


class AuthService:
    """认证服务"""

    def __init__(self):
        pass

    @property
    def users_coll(self):
        """延迟获取 MongoDB users collection（避免模块导入时 MongoDB 未连接）"""
        if hasattr(self, "_users_coll"):
            return self._users_coll
        from app.core.database import MongoDB
        return MongoDB.db.users if MongoDB.db is not None else None

    @users_coll.setter
    def users_coll(self, value):
        """测试注入用"""
        self._users_coll = value

    @property
    def redis(self):
        """延迟获取 Redis client（避免模块导入时 Redis 未连接）"""
        if hasattr(self, "_redis"):
            return self._redis
        from app.core.database import RedisClient
        return RedisClient.get_client() if RedisClient.pool is not None else None

    @redis.setter
    def redis(self, value):
        """测试注入用"""
        self._redis = value

    @staticmethod
    def hash_password(password: str) -> str:
        """密码 bcrypt 哈希"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """校验密码与哈希"""
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except ValueError:
            return False

    @staticmethod
    def create_access_token(payload: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode({**payload, "exp": expire, "type": "access"}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(payload: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return jwt.encode({**payload, "exp": expire, "type": "refresh"}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    async def login(self, username: str, password: str) -> TokenResponse:
        """AC1.1/AC1.2"""
        user_doc = await self.users_coll.find_one({"username": username})
        if not user_doc or not self.verify_password(password, user_doc["password_hash"]):
            raise AuthError("用户名或密码错误")
        payload = {"user_id": user_doc["user_id"], "username": user_doc["username"], "role": user_doc.get("role", "hr")}
        access = self.create_access_token(payload)
        refresh = self.create_refresh_token(payload)
        return TokenResponse(
            access_token=access, refresh_token=refresh, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserInfo(user_id=user_doc["user_id"], username=user_doc["username"], role=user_doc.get("role", "hr"), email=user_doc.get("email"))
        )

    async def verify_token(self, token: str) -> dict:
        """AC1.3/AC1.4/AC1.6 校验 token，返回 user payload"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except JWTError:
            raise AuthError("Token 已过期，请重新登录")
        if await self.redis.exists(f"token:blacklist:{token}"):
            raise AuthError("Token 已失效")
        return {"user_id": payload["user_id"], "username": payload["username"], "role": payload.get("role", "hr")}

    async def logout(self, token: str) -> None:
        """AC1.6 加入黑名单"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            ttl = int(payload["exp"] - datetime.now(timezone.utc).timestamp())
            if ttl > 0:
                await self.redis.setex(f"token:blacklist:{token}", ttl, "1")
        except JWTError:
            pass

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """AC1.5"""
        try:
            payload = jwt.decode(refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except JWTError:
            raise AuthError("refresh_token 无效")
        if payload.get("type") != "refresh":
            raise AuthError("refresh_token 类型错误")
        if await self.redis.exists(f"token:blacklist:{refresh_token}"):
            raise AuthError("refresh_token 已失效")
        new_payload = {"user_id": payload["user_id"], "username": payload["username"], "role": payload.get("role", "hr")}
        access = self.create_access_token(new_payload)
        new_refresh = self.create_refresh_token(new_payload)
        return TokenResponse(
            access_token=access, refresh_token=new_refresh, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserInfo(user_id=new_payload["user_id"], username=new_payload["username"], role=new_payload["role"])
        )
