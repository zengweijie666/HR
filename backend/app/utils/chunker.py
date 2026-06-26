"""
文件名: app/utils/chunker.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 父子块分层切分（复用 EduRAG document_processor 思路）
入参: text, child_size=300, parent_size=1200
出参: (child_chunks, parent_chunks)
"""
import uuid
from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: str
    content: str
    parent_id: str


def split_parent_child(text: str, child_size: int = 300, parent_size: int = 1200) -> tuple[list[Chunk], list[Chunk]]:
    """先切父块，再在每个父块内切子块"""
    parents: list[Chunk] = []
    children: list[Chunk] = []
    # 按字符切父块
    for i in range(0, len(text), parent_size):
        parent_content = text[i:i + parent_size]
        parent_id = f"p_{uuid.uuid4().hex[:12]}"
        parents.append(Chunk(chunk_id=parent_id, content=parent_content, parent_id=parent_id))
        # 在父块内切子块
        for j in range(0, len(parent_content), child_size):
            child_content = parent_content[j:j + child_size]
            if not child_content.strip():
                continue
            child_id = f"c_{uuid.uuid4().hex[:12]}"
            children.append(Chunk(chunk_id=child_id, content=child_content, parent_id=parent_id))
    return children, parents
