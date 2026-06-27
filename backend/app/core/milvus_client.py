"""
文件名: app/core/milvus_client.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: Milvus 连接与 Collection 初始化
入参: settings
出参: Collection 单例
"""
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from app.core.config import settings
from app.core.logger import logger


class MilvusClient:
    """Milvus 客户端"""

    def __init__(self):
        self._collection = None
        self._connected = False

    def connect(self):
        """建立 Milvus 连接"""
        if not self._connected:
            connections.connect(host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)
            self._connected = True
            logger.info("Milvus 已连接")

    def ensure_collection(self):
        """确保 Collection 存在且 schema 匹配，不存在或 schema 不匹配则（重建）创建

        Collection schema 对应 Backend-Design.md 3.4：
        - id: 子块主键
        - candidate_id: 简历 ID（用于删除）
        - dense_vector: BGE-M3 稠密向量 (1024 维)
        - sparse_vector: BGE-M3 稀疏向量
        - salary_min/salary_max/education_level/work_years: 标量过滤字段
        - skills_text/parent_id/parent_content: 父子块回溯
        """
        self.connect()
        required_fields = {
            "id", "candidate_id", "dense_vector", "sparse_vector",
            "salary_min", "salary_max", "education_level", "work_years",
            "skills_text", "parent_id", "parent_content",
        }
        if utility.has_collection(settings.MILVUS_COLLECTION):
            self._collection = Collection(settings.MILVUS_COLLECTION)
            # 检查现有 schema 是否包含所有必需字段，不匹配则删除重建
            existing_fields = {f.name for f in self._collection.schema.fields}
            if not required_fields.issubset(existing_fields):
                logger.warning(
                    f"Milvus Collection schema 不匹配（现有 {len(existing_fields)} 字段，"
                    f"缺少 {required_fields - existing_fields}），删除重建"
                )
                utility.drop_collection(settings.MILVUS_COLLECTION)
                self._collection = None
            else:
                logger.info(f"Milvus Collection 已就绪（schema 匹配）")
                self._collection.load()
                return

        if self._collection is None:
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                FieldSchema(name="candidate_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=1024),
                FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
                FieldSchema(name="salary_min", dtype=DataType.INT64),
                FieldSchema(name="salary_max", dtype=DataType.INT64),
                FieldSchema(name="education_level", dtype=DataType.INT8),
                FieldSchema(name="work_years", dtype=DataType.INT64),
                FieldSchema(name="skills_text", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="parent_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="parent_content", dtype=DataType.VARCHAR, max_length=4000),
            ]
            schema = CollectionSchema(fields, description="HR resumes hybrid index")
            self._collection = Collection(settings.MILVUS_COLLECTION, schema)
            self._collection.create_index(
                "dense_vector",
                {"index_type": "IVF_FLAT", "metric_type": "IP", "params": {"nlist": 1024}},
            )
            self._collection.create_index(
                "sparse_vector",
                {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"},
            )
            logger.info(f"创建 Milvus Collection: {settings.MILVUS_COLLECTION}")
        self._collection.load()

    @property
    def collection(self) -> Collection:
        """延迟初始化并返回 Collection"""
        if self._collection is None:
            self.ensure_collection()
        return self._collection

    @collection.setter
    def collection(self, value):
        """测试注入用"""
        self._collection = value


milvus_client = MilvusClient()
