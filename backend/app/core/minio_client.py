"""
文件名: app/core/minio_client.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: MinIO 文件操作封装
入参: settings
出参: file_id / presigned_url
"""
import io
import uuid
from datetime import timedelta
from minio import Minio
from app.core.config import settings
from app.core.logger import logger


class MinioClient:
    """MinIO 文件操作"""

    def __init__(self):
        self._client = None

    @property
    def client(self) -> Minio:
        """延迟初始化 MinIO 客户端，确保 bucket 存在"""
        if self._client is None:
            self._client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            if not self._client.bucket_exists(settings.MINIO_BUCKET):
                self._client.make_bucket(settings.MINIO_BUCKET)
                logger.info(f"创建 bucket: {settings.MINIO_BUCKET}")
        return self._client

    @client.setter
    def client(self, value):
        """测试注入用"""
        self._client = value

    def upload_bytes(self, data: bytes, file_name: str, content_type: str = "application/octet-stream") -> str:
        """上传字节流，返回 file_id"""
        file_id = f"minio_{uuid.uuid4().hex[:16]}"
        self.client.put_object(
            settings.MINIO_BUCKET, file_id, io.BytesIO(data), len(data), content_type
        )
        logger.info(f"上传文件: {file_name} → {file_id}")
        return file_id

    def presigned_url(self, file_id: str, expires: int = 3600) -> str:
        """生成预签名 URL"""
        return self.client.presigned_get_object(
            settings.MINIO_BUCKET, file_id, expires=timedelta(seconds=expires)
        )

    def delete(self, file_id: str) -> None:
        """删除文件"""
        self.client.remove_object(settings.MINIO_BUCKET, file_id)
        logger.info(f"删除文件: {file_id}")

    def download(self, file_id: str) -> bytes:
        """下载文件字节"""
        response = self.client.get_object(settings.MINIO_BUCKET, file_id)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


minio_client = MinioClient()
