"""知识库 Schema."""

from typing import List, Optional

from pydantic import BaseModel


class KnowledgeDocBase(BaseModel):
    station_id: Optional[int] = None
    filename: str
    doc_type: str
    status: Optional[str] = "active"


class KnowledgeDocCreate(KnowledgeDocBase):
    content_text: Optional[str] = None


class KnowledgeDocResponse(KnowledgeDocBase):
    id: int
    chunk_count: int
    content_text: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        orm_mode = True


class KnowledgeAskRequest(BaseModel):
    question: str
    station_id: Optional[int] = None
    top_k: Optional[int] = 3


class KnowledgeAskResponse(BaseModel):
    answer: str
    sources: List[dict]
