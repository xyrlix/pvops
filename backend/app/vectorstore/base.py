"""向量存储抽象接口."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    """简易文档对象."""

    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """向量存储抽象."""

    @abstractmethod
    async def is_available(self) -> bool:
        """是否可用."""
        ...

    @abstractmethod
    async def add_documents(
        self, documents: List[Document], ids: Optional[List[str]] = None
    ) -> List[str]:
        """添加文档，返回文档 IDs."""
        ...

    @abstractmethod
    async def similarity_search(
        self, query: str, k: int = 4, filter: Optional[dict] = None
    ) -> List[Document]:
        """相似度检索."""
        ...

    @abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        """删除文档."""
        ...
