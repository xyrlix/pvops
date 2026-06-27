"""知识库模型."""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class KnowledgeDoc(Base):
    """知识库文档."""

    __tablename__ = "knowledge_docs"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=True, index=True)
    filename = Column(String(255), nullable=False, comment="原始文件名")
    doc_type = Column(String(32), nullable=False, comment="文档类型: pdf/docx/txt")
    content_text = Column(Text, nullable=True, comment="提取的全文")
    chunk_count = Column(Integer, default=0, comment="切分块数")
    status = Column(String(20), default="active", comment="状态")
    created_at = Column(String(50), server_default=func.now())


class KnowledgeFeedback(Base):
    """AI 回答反馈."""

    __tablename__ = "knowledge_feedback"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=True, comment="用户问题")
    answer = Column(Text, nullable=True, comment="AI 回答")
    rating = Column(String(20), nullable=False, comment="good / bad")
    created_at = Column(String(50), server_default=func.now())


class KnowledgeChunk(Base):
    """知识库文本块（用于本地 fallback，PGVector 场景可选）."""

    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("knowledge_docs.id"), nullable=False, index=True)
    vector_id = Column(String(64), nullable=True, index=True, comment="向量库中的唯一 ID")
    content = Column(Text, nullable=False, comment="文本块内容")
    chunk_index = Column(Integer, default=0, comment="块序号")
    created_at = Column(String(50), server_default=func.now())
