"""
文件名: app/core/config.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 基于 pydantic-settings 的配置管理，从 .env 读取所有配置项
入参: 环境变量 / .env 文件
出参: settings 单例
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 服务
    APP_NAME: str = "TalentSense HR"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "talentsense"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "resumes"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "resumes"
    MINIO_SECURE: bool = False

    # LLM
    LLM_API_KEY: str
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-plus"

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 模型路径
    BGE_M3_PATH: str = "./models/bge-m3"
    BGE_RERANKER_PATH: str = "./models/bge-reranker-v2-m3"

    # 检索参数
    HYBRID_DENSE_WEIGHT: float = 1.0
    HYBRID_SPARSE_WEIGHT: float = 0.7
    RETRIEVE_TOP_K: int = 20
    RERANK_TOP_K: int = 10

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
