"""知识库接口."""

from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.knowledge import KnowledgeAskRequest, KnowledgeAskResponse, KnowledgeDocResponse
from app.services import knowledge_service

router = APIRouter()


@router.get("/documents", response_model=List[KnowledgeDocResponse])
async def list_documents(station_id: Optional[int] = None):
    """列出知识库文档."""
    docs = await knowledge_service.list_documents(station_id)
    return docs


@router.post("/documents", response_model=KnowledgeDocResponse)
async def upload_document(
    file: UploadFile = File(...),
    station_id: Optional[int] = Form(None),
):
    """上传知识库文档并建立索引."""
    content = await file.read()
    doc = await knowledge_service.save_upload(file.filename, content, station_id)

    # 创建文本块并写入向量库（metadata 中携带 station_id）
    await knowledge_service.create_chunks(doc.id, doc.content_text or "", station_id=station_id)

    return doc


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    """删除知识库文档."""
    success = await knowledge_service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"success": True}


@router.post("/ask", response_model=KnowledgeAskResponse)
async def ask_knowledge(request: KnowledgeAskRequest):
    """独立的知识库问答接口."""
    store = await get_vector_store()
    filter_dict = {}
    if request.station_id:
        filter_dict["station_id"] = request.station_id

    docs = await store.similarity_search(
        request.question, k=request.top_k or 4, filter=filter_dict or None
    )

    answer = ""
    if docs:
        answer = "根据知识库内容：\n\n" + "\n---\n".join(d.page_content for d in docs)
    else:
        answer = "未在知识库中找到相关内容。"

    return KnowledgeAskResponse(
        answer=answer,
        sources=[{"content": d.page_content, "metadata": d.metadata} for d in docs],
    )
