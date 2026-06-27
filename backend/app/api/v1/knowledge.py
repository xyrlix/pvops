"""知识库接口."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.models.knowledge import KnowledgeFeedback
from app.schemas.knowledge import KnowledgeAskRequest, KnowledgeAskResponse, KnowledgeDocResponse
from app.services import knowledge_service
from app.vectorstore import get_vector_store

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/documents", response_model=list[KnowledgeDocResponse])
async def list_documents(station_id: int | None = None):
    """列出知识库文档."""
    docs = await knowledge_service.list_documents(station_id)
    return docs


@router.post("/documents", response_model=KnowledgeDocResponse)
@limiter.limit("20/minute")  # 上传成本高（含分块 + embedding），收紧
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    station_id: int | None = Form(None),
):
    """上传知识库文档并建立索引."""
    content = await file.read()
    doc = await knowledge_service.save_upload(file.filename, content, station_id)

    # 创建文本块并写入向量库（metadata 中携带 station_id）
    await knowledge_service.create_chunks(doc.id, doc.content_text or "", station_id=station_id)

    return doc


@router.delete("/documents/{doc_id}")
@limiter.limit("30/minute")
async def delete_document(request: Request, doc_id: int):
    """删除知识库文档."""
    success = await knowledge_service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"success": True}


@router.post("/ask", response_model=KnowledgeAskResponse)
@limiter.limit("30/minute")  # 检索 + LLM，限速
async def ask_knowledge(request: Request, payload: KnowledgeAskRequest):
    """独立的知识库问答接口."""
    store = await get_vector_store()
    filter_dict = {}
    if payload.station_id:
        filter_dict["station_id"] = payload.station_id

    docs = await store.similarity_search(
        payload.question, k=payload.top_k or 4, filter=filter_dict or None
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


@router.post("/feedback")
@limiter.limit("60/minute")
async def submit_feedback(request: Request, payload: dict) -> dict:
    """接收 AI 回答的 👍/👎 反馈（用于改进 prompt）。"""
    async with AsyncSessionLocal() as session:
        fb = KnowledgeFeedback(
            question=payload.get("question", ""),
            answer=payload.get("answer", ""),
            rating=payload.get("rating", "good"),
        )
        session.add(fb)
        await session.commit()
    return {"success": True}
