"""向量存储抽象接口."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """简易文档对象."""

    page_content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """向量存储抽象."""

    @abstractmethod
    async def is_available(self) -> bool:
        """是否可用."""
        ...

    @abstractmethod
    async def add_documents(
        self, documents: list[Document], ids: list[str] | None = None
    ) -> list[str]:
        """添加文档，返回文档 IDs."""
        ...

    @abstractmethod
    async def similarity_search(
        self, query: str, k: int = 4, filter: dict | None = None
    ) -> list[Document]:
        """相似度检索."""
        ...

    @abstractmethod
    async def delete(self, ids: list[str]) -> bool:
        """删除文档."""
        ...
