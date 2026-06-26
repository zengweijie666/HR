"""
文件名: tests/core/test_minio_client.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: MinIO 客户端单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from app.core.minio_client import MinioClient


def test_upload_returns_file_id():
    """上传字节流应返回以 minio_ 开头的 file_id"""
    with patch("app.core.minio_client.Minio") as MockMinio:
        instance = MockMinio.return_value
        instance.bucket_exists.return_value = False
        client = MinioClient()
        client.client = instance
        file_id = client.upload_bytes(b"pdf-bytes", "test.pdf", "application/pdf")
        assert file_id.startswith("minio_")
        instance.put_object.assert_called_once()


def test_presigned_url():
    """生成预签名 URL 应透传 minio 客户端返回值"""
    with patch("app.core.minio_client.Minio") as MockMinio:
        instance = MockMinio.return_value
        instance.bucket_exists.return_value = True
        instance.presigned_get_object.return_value = "http://signed.url/x"
        client = MinioClient()
        client.client = instance
        url = client.presigned_url("file_id", expires=3600)
        assert url == "http://signed.url/x"


def test_delete():
    """删除文件应调用 remove_object(bucket, file_id)"""
    with patch("app.core.minio_client.Minio") as MockMinio:
        instance = MockMinio.return_value
        client = MinioClient()
        client.client = instance
        client.delete("file_id")
        instance.remove_object.assert_called_once_with("resumes", "file_id")
