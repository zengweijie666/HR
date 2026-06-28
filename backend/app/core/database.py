"""
文件名: app/core/database.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: MongoDB + Redis 连接管理，对应 Backend-Design.md 3.2
入参: settings
出参: MongoDB.db / RedisClient.get_client()
"""
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from app.core.config import settings
from app.core.logger import logger


class MongoDB:
    """MongoDB 异步连接管理"""
    client: AsyncIOMotorClient | None = None
    db = None

    @classmethod
    async def connect(cls):
        """建立连接并创建索引"""
        cls.client = AsyncIOMotorClient(settings.MONGO_URI)
        cls.db = cls.client[settings.MONGO_DB]
        # 创建索引（对应 Backend-Design.md 3.2）
        await cls.db.resumes.create_index("resume_id", unique=True)
        await cls.db.resumes.create_index("candidate_id")
        await cls.db.resumes.create_index("phone_hash")
        await cls.db.resumes.create_index("email_hash")
        await cls.db.resumes.create_index("tags")
        await cls.db.resumes.create_index("is_favorite")
        await cls.db.chat_sessions.create_index("session_id", unique=True)
        await cls.db.chat_sessions.create_index([("user_id", 1), ("updated_at", -1)])
        await cls.db.interview_notes.create_index("note_id", unique=True)
        await cls.db.interview_notes.create_index("resume_id")
        await cls.db.email_config.create_index("config_id", unique=True)
        # users 表索引
        await cls.db.users.create_index("username", unique=True)
        await cls.db.users.create_index("email", unique=True)
        await cls.db.users.create_index([("role", 1), ("status", 1)])
        # email_templates 表索引
        await cls.db.email_templates.create_index("template_id", unique=True)
        await cls.db.email_templates.create_index("name")
        logger.info("MongoDB 已连接", extra={})

    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()
            logger.info("MongoDB 已断开")


class RedisClient:
    """Redis 异步连接管理"""
    pool: redis.ConnectionPool | None = None

    @classmethod
    async def connect(cls):
        """建立连接池并执行ping预热实际连接"""
        cls.pool = redis.ConnectionPool.from_url(settings.REDIS_URL)
        # 执行 PING 命令强制建立 TCP 连接，避免首次请求时连接延迟
        try:
            client = redis.Redis(connection_pool=cls.pool)
            await client.ping()
            logger.info("Redis 已连接")
        except Exception as e:
            logger.warning(f"Redis 连接失败: {e}")

    @classmethod
    def get_client(cls) -> redis.Redis:
        return redis.Redis(connection_pool=cls.pool)
