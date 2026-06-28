"""知识库处理测试."""

import os
import tempfile

from app.services.knowledge_service import (
    _chunk_text,
    detect_doc_type,
    extract_text,
)


def test_detect_doc_type():
    assert detect_doc_type("manual.pdf") == "pdf"
    assert detect_doc_type("sop.docx") == "docx"
    assert detect_doc_type("readme.txt") == "txt"


def test_chunk_text():
    text = "\n\n".join(["a" * 250 for _ in range(4)])
    chunks = _chunk_text(text, chunk_size=300, overlap=50)
    assert len(chunks) >= 4
    assert len(chunks[0]) == 300


def test_extract_txt():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("光伏电站运维手册")
        path = f.name
    try:
        assert "光伏电站运维手册" in extract_text(path, "txt")
    finally:
        os.unlink(path)


def test_extract_docx():
    """用最小 DOCX 文件测试标准库解析."""
    # 构造一个最小 docx（zip，内含 word/document.xml）
    import zipfile

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        path = f.name
    try:
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr(
                "word/document.xml",
                '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p><w:r><w:t>逆变器故障处理</w:t></w:r></w:p></w:body></w:document>",
            )
        text = extract_text(path, "docx")
        assert "逆变器故障处理" in text
    finally:
        os.unlink(path)
