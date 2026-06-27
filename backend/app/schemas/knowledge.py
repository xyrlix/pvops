"""知识库 Schema."""

from pydantic import BaseModel


class KnowledgeDocBase(BaseModel):
    station_id: int | None = None
    filename: str
    doc_type: str
    status: str | None = "active"


class KnowledgeDocCreate(KnowledgeDocBase):
    content_text: str | None = None


class KnowledgeDocResponse(KnowledgeDocBase):
    id: int
    chunk_count: int
    content_text: str | None = None
    created_at: str | None = None

    class Config:
        orm_mode = True


class KnowledgeAskRequest(BaseModel):
    question: str
    station_id: int | None = None
    top_k: int | None = 3


class KnowledgeAskResponse(BaseModel):
    answer: str
    sources: list[dict]
