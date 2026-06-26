"""
文件名: tests/utils/test_chunker.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 测试父子块切分
"""
from app.utils.chunker import split_parent_child


def test_split_basic():
    text = "A" * 1500
    children, parents = split_parent_child(text, child_size=300, parent_size=1200)
    assert len(children) >= 1
    assert all(len(c.content) <= 300 for c in children)
    assert all(len(p.content) <= 1200 for p in parents)


def test_short_text():
    text = "短文本"
    children, parents = split_parent_child(text)
    assert len(children) == 1
    assert children[0].content == "短文本"


def test_parent_child_link():
    text = "A" * 700
    children, parents = split_parent_child(text, child_size=300, parent_size=1200)
    # 每个子块必须有 parent_id 指向某个父块
    for c in children:
        assert c.parent_id is not None
        assert any(p.parent_id == c.parent_id for p in parents)
