"""知识库文档处理服务.

文档解析策略：
- PDF：优先 pdfplumber（保留表格）→ pypdf（纯文本）→ 降级提示
- DOCX：用标准库 zipfile + XML 解析，保留段落换行（不再粗暴去 \\s+）
- TXT/MD：直接读取，按行合并空行

文本分块策略：
- 优先按段落（\n\n）切分，段落内按句号 / 句末标点切分
- 块大小 ~800 字符（中文），相邻块保留 100 字符重叠
- 跳过空块，过短块（<50 字符）合并到前一块
"""

import logging
import os
import re
import zipfile

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


# ─── 文本分块 ─────────────────────────────────────────────


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """按段落 → 句子 → 字符三层切分."""
    if not text or not text.strip():
        return []

    # 1. 按空行切段
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        # 单段太长：按句号/问号/感叹号切
        if len(para) > chunk_size * 1.5:
            sentences = re.split(r"(?<=[。！？.!?\?])\s*", para)
            for sent in sentences:
                if not sent.strip():
                    continue
                if not current:
                    current = sent
                elif len(current) + len(sent) <= chunk_size:
                    current += sent
                else:
                    chunks.append(current.strip())
                    # 重叠：把 current 末尾 overlap 字符接到下一块开头
                    current = current[-overlap:] + sent if overlap < len(current) else sent
            continue

        # 段长度 + 当前块 ≤ 阈值
        if not current:
            current = para
        elif len(current) + len(para) + 2 <= chunk_size:
            current = current + "\n\n" + para
        else:
            chunks.append(current.strip())
            current = current[-overlap:] + "\n\n" + para if overlap < len(current) else para

    if current.strip():
        # 合并过短的尾部
        if chunks and len(current.strip()) < 50:
            chunks[-1] = chunks[-1] + "\n\n" + current.strip()
        else:
            chunks.append(current.strip())

    return [c for c in chunks if c.strip()]


# ─── DOCX 解析（保留段落） ─────────────────────────────────


def _extract_docx_text(file_path: str) -> str:
    """用标准库 zipfile 解析 DOCX，按段落换行（不再粗暴合并）."""
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        # 把段落标签 </w:p> 替换为双换行（保持段落边界）
        xml = re.sub(r"</w:p>", "\n\n", xml)
        xml = re.sub(r"<w:br[^>]*/?>", "\n", xml)
        # 表格行 → 单换行
        xml = re.sub(r"</w:tr>", "\n", xml)
        xml = re.sub(r"</w:tc>", " | ", xml)
        # 去除所有其他标签
        text = re.sub(r"<[^>]+>", "", xml)
        # 实体解码
        text = (
            text.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
        )
        # 清理多余空白（保留段落换行）
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except Exception as e:
        logger.warning(f"解析 DOCX 失败: {e}")
        return ""


# ─── PDF 解析（pdfplumber 优先） ────────────────────────────


def _extract_pdf_text(file_path: str) -> str:
    """PDF 解析：优先 pdfplumber（保留表格）→ pypdf → 提示."""
    # 1. pdfplumber：表格保留
    try:
        import pdfplumber

        parts: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    parts.append(page_text)

                # 表格作为单独段落保留（"col | col" 格式）
                tables = page.extract_tables()
                for tbl in tables:
                    if not tbl:
                        continue
                    rows = [" | ".join(str(c or "").strip() for c in row) for row in tbl]
                    parts.append("\n".join(rows))
        if parts:
            return "\n\n".join(parts)
    except ImportError:
        logger.debug("pdfplumber 未安装，回退 pypdf")
    except Exception as e:
        logger.warning(f"pdfplumber 解析失败: {e}")

    # 2. pypdf fallback
    try:
        import pypdf

        reader = pypdf.PdfReader(file_path)
        return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)
    except ImportError:
        logger.warning("pypdf 未安装，PDF 文本提取不可用")
        return "[PDF 解析需要安装 pdfplumber 或 pypdf]"
    except Exception as e:
        logger.warning(f"解析 PDF 失败: {e}")
        return ""


def extract_text(file_path: str, doc_type: str) -> str:
    """根据文档类型提取文本."""
    if doc_type == "txt":
        with open(file_path, encoding="utf-8", errors="ignore") as f:
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


async def save_upload(filename: str, content: bytes, station_id: int | None = None) -> KnowledgeDoc:
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
    doc_id: int, text: str, chunk_size: int = 800, station_id: int | None = None
) -> list[KnowledgeChunk]:
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
            for chunk, vid in zip(db_chunks, vector_ids, strict=False):
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


async def list_documents(station_id: int | None = None) -> list[KnowledgeDoc]:
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        query = select(KnowledgeDoc).where(KnowledgeDoc.status == "active")
        if station_id:
            query = query.where(KnowledgeDoc.station_id == station_id)
        query = query.order_by(KnowledgeDoc.id.desc())
        result = await session.execute(query)
        return result.scalars().all()


async def get_document(doc_id: int) -> KnowledgeDoc | None:
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


async def save_case_document(
    title: str, content: str, station_id: int | None = None
) -> KnowledgeDoc:
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

    await create_chunks(int(doc.id), content, station_id=station_id)
    return doc


# mypy: disable-error-code="arg-type,assignment"
