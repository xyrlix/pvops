"""向量存储抽象."""

from app.vectorstore.base import Document, VectorStore
from app.vectorstore.factory import close_all_vector_stores, get_vector_store, reset_vector_store

__all__ = [
    "Document",
    "VectorStore",
    "get_vector_store",
    "close_all_vector_stores",
    "reset_vector_store",
]
