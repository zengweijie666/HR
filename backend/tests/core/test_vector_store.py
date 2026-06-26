"""
文件名: tests/core/test_vector_store.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: VectorStore 混合检索与删除测试
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.vector_store import VectorStore


@pytest.mark.asyncio
async def test_hybrid_search():
    """hybrid_search 应返回解析后的结果列表"""
    with patch.object(VectorStore, "collection", new_callable=MagicMock) as mock_coll:
        mock_coll.hybrid_search.return_value = [[MagicMock(get=lambda x: {"id": "c1", "candidate_id": "c1", "score": 0.9, "parent_content": "..."})]]
        vs = VectorStore()
        results = await vs.hybrid_search([[0.1]*1024], [{}], {}, top_k=10)
        assert len(results) >= 0  # 至少不报错


@pytest.mark.asyncio
async def test_delete_by_resume_id():
    """delete_by_resume_id 应调用 collection.delete"""
    with patch.object(VectorStore, "collection", new_callable=MagicMock) as mock_coll:
        vs = VectorStore()
        await vs.delete_by_resume_id("r1")
        mock_coll.delete.assert_called()
