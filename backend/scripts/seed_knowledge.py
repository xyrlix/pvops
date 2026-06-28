#!/usr/bin/env python3
"""种子知识库导入脚本.

读取 ``seed/`` 目录下的 markdown 文档，逐篇上传到知识库，
经过分块 + 向量化后可供 RAG 检索。

用法::

    PYTHONPATH=backend:. python3 backend/scripts/seed_knowledge.py

可以重复执行（同文档名会创建副本，不会覆盖已有文档；由前台去重）。
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# 确保能找到 backend 包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import AsyncSessionLocal
from app.models.knowledge import KnowledgeDoc
from app.services import knowledge_service
from app.services.knowledge_service import (
    detect_doc_type,
    extract_text,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("seed_knowledge")

SEED_DIR = os.path.join(os.path.dirname(__file__), "..", "seed")


async def seed_file(file_path: str) -> None:
    """导入单篇文档到知识库."""
    filename = os.path.basename(file_path)
    doc_type = detect_doc_type(filename)

    with open(file_path, "rb") as f:
        content = f.read()

    # 1. 先检查是否已存在同名文档（避免重复导入）
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(KnowledgeDoc).where(KnowledgeDoc.filename == filename)
        )
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("跳过已有文档: %s (id=%s)", filename, existing.id)
            return

    # 2. 使用 knowledge_service 保存（含文本提取）
    doc = await knowledge_service.save_upload(filename, content)
    logger.info("已保存: %s (id=%s)", filename, doc.id)

    # 3. 提取文本
    text = extract_text(file_path, doc_type)
    if not text.strip():
        logger.warning("文档 %s 无有效文本，跳过", filename)
        return

    # 4. 更新 content_text
    async with AsyncSessionLocal() as session:
        doc_db = await session.get(KnowledgeDoc, doc.id)
        if doc_db:
            doc_db.content_text = text
            await session.commit()

    # 5. 分块 + 向量写入
    chunks = await knowledge_service.create_chunks(doc.id, text)
    logger.info("  已写入 %d 个文本块", len(chunks))


async def main() -> None:
    """扫描 seed 目录，导入所有文档."""
    if not os.path.isdir(SEED_DIR):
        logger.warning("seed 目录不存在: %s", SEED_DIR)
        return

    files = sorted(f for f in os.listdir(SEED_DIR) if f.endswith((".md", ".txt", ".pdf", ".docx")))
    if not files:
        logger.warning("seed 目录无可用文档")
        return

    logger.info("找到 %d 篇待导入文档", len(files))
    for fname in files:
        fpath = os.path.join(SEED_DIR, fname)
        try:
            await seed_file(fpath)
        except Exception as exc:
            logger.error("导入失败: %s — %s", fname, exc)

    logger.info("知识库种子导入完成")


if __name__ == "__main__":
    asyncio.run(main())
