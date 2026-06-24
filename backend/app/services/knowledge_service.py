"""知识库文档处理服务."""

import logging
import os
import re
import zipfile
from typing import List, Optional

from app.core.database import AsyncSessionLocal
from app.models.knowledge import KnowledgeChunk, KnowledgeDoc
from app.vectorstore.base import Document
from app.vectorstore.factory import get_vector_store

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "kb")


def _ensure_upload_dir() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def _sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", filename)


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """按字符长度切分文本."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def _extract_docx_text(file_path: str) -> str:
    """使用标准库解析 DOCX 文本（无需 python-docx）."""
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        # 简单去除 XML 标签
        text = re.sub(r"<[^>]+>", "", xml)
        return re.sub(r"\s+", " ", text).strip()
    except Exception as e:
        logger.warning(f"解析 DOCX 失败: {e}")
        return ""


def _extract_pdf_text(file_path: str) -> str:
    """PDF 解析占位：优先尝试 pypdf，否则返回提示信息."""
    try:
        import pypdf

        reader = pypdf.PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        logger.warning("pypdf 未安装，PDF 文本提取不可用")
        return "[PDF 解析需要安装 pypdf]"
    except Exception as e:
        logger.warning(f"解析 PDF 失败: {e}")
        return ""


def extract_text(file_path: str, doc_type: str) -> str:
    """根据文档类型提取文本."""
    if doc_type == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if doc_type == "docx":
        return _extract_docx_text(file_path)
    if doc_type == "pdf":
        return _extract_pdf_text(file_path)
    return ""


def detect_doc_type(filename: str) -> str:
    ext = filename.lower().split(".")[-1]
    if ext in ("pdf",):
        return "pdf"
    if ext in ("docx",):
        return "docx"
    if ext in ("txt", "md", "json"):
        return "txt"
    return "txt"


async def save_upload(
    filename: str, content: bytes, station_id: Optional[int] = None
) -> KnowledgeDoc:
    """保存上传文件并提取文本."""
    _ensure_upload_dir()
    doc_type = detect_doc_type(filename)
    safe_name = _sanitize_filename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as f:
        f.write(content)

    text = extract_text(file_path, doc_type)

    async with AsyncSessionLocal() as session:
        doc = KnowledgeDoc(
            station_id=station_id,
            filename=filename,
            doc_type=doc_type,
            content_text=text,
            chunk_count=0,
            status="active",
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return doc


async def create_chunks(
    doc_id: int, text: str, chunk_size: int = 800, station_id: Optional[int] = None
) -> List[KnowledgeChunk]:
    """为文档创建文本块并入库，同时写入向量库."""
    chunks = _chunk_text(text, chunk_size)
    if not chunks:
        async with AsyncSessionLocal() as session:
            doc = await session.get(KnowledgeDoc, doc_id)
            if doc:
                doc.chunk_count = 0
                await session.commit()
        return []

    async with AsyncSessionLocal() as session:
        db_chunks = []
        for idx, content in enumerate(chunks):
            chunk = KnowledgeChunk(
                doc_id=doc_id,
                content=content,
                chunk_index=idx,
            )
            session.add(chunk)
            db_chunks.append(chunk)
        await session.commit()
        for chunk in db_chunks:
            await session.refresh(chunk)

        # 写入向量库
        doc = await session.get(KnowledgeDoc, doc_id)
        store = await get_vector_store()
        vector_ids = [f"doc_{doc_id}_chunk_{chunk.chunk_index}" for chunk in db_chunks]
        documents = [
            Document(
                page_content=chunk.content,
                metadata={
                    "doc_id": doc_id,
                    "chunk_index": chunk.chunk_index,
                    "station_id": station_id,
                    "filename": doc.filename if doc else "",
                },
            )
            for chunk in db_chunks
        ]
        try:
            await store.add_documents(documents, ids=vector_ids)
            for chunk, vid in zip(db_chunks, vector_ids):
                chunk.vector_id = vid
            await session.commit()
        except Exception as e:
            logger.error(f"写入向量库失败: {e}")

        # 更新文档块数
        doc = await session.get(KnowledgeDoc, doc_id)
        if doc:
            doc.chunk_count = len(chunks)
            await session.commit()
        return db_chunks


async def list_documents(station_id: Optional[int] = None) -> List[KnowledgeDoc]:
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        query = select(KnowledgeDoc).where(KnowledgeDoc.status == "active")
        if station_id:
            query = query.where(KnowledgeDoc.station_id == station_id)
        query = query.order_by(KnowledgeDoc.id.desc())
        result = await session.execute(query)
        return result.scalars().all()


async def get_document(doc_id: int) -> Optional[KnowledgeDoc]:
    async with AsyncSessionLocal() as session:
        return await session.get(KnowledgeDoc, doc_id)


async def delete_document(doc_id: int) -> bool:
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        doc = await session.get(KnowledgeDoc, doc_id)
        if not doc:
            return False

        # 同步删除向量库中的文本块
        result = await session.execute(
            select(KnowledgeChunk.vector_id).where(
                KnowledgeChunk.doc_id == doc_id,
                KnowledgeChunk.vector_id.isnot(None),
            )
        )
        vector_ids = [row[0] for row in result.all() if row[0]]
        if vector_ids:
            try:
                store = await get_vector_store()
                await store.delete(vector_ids)
            except Exception as e:
                logger.error(f"删除向量库文档失败: {e}")

        doc.status = "deleted"
        await session.commit()
        return True


async def save_case_document(title: str, content: str, station_id: Optional[int] = None) -> KnowledgeDoc:
    """将工单案例沉淀为知识库文档."""
    async with AsyncSessionLocal() as session:
        doc = KnowledgeDoc(
            station_id=station_id,
            filename=title,
            doc_type="case",
            content_text=content,
            chunk_count=0,
            status="active",
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

    await create_chunks(doc.id, content, station_id=station_id)
    return doc
