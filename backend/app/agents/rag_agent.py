"""RAG 问答 Agent."""

import logging
from typing import Any, Dict, List, Optional

from app.llm.factory import get_chat_llm
from app.vectorstore.base import Document
from app.vectorstore.factory import get_vector_store

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一名资深光伏运维专家，熟悉逆变器、组串、气象站、关口表等设备。
请基于以下原则回答用户问题：
1. 优先使用【知识库片段】和【上下文】中的信息。
2. 如果信息不足，明确说明，不要编造。
3. 回答简洁、专业，必要时列出操作步骤或建议。
"""


def _format_context(context: Optional[Dict[str, Any]]) -> str:
    if not context:
        return "无额外上下文。"
    lines = []
    ctype = context.get("type")
    if ctype == "device":
        lines.append(f"当前设备：{context.get('device_code')}（电站 {context.get('station_id')}）")
    elif ctype == "alarm":
        lines.append(f"当前告警：{context.get('alarm_title')}（电站 {context.get('station_id')}）")
    elif ctype == "diagnosis":
        lines.append(f"当前诊断报告 ID：{context.get('diagnosis_report_id')}")
    else:
        for k, v in context.items():
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


async def ask(
    question: str,
    context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 4,
) -> Dict[str, Any]:
    """执行一次 RAG 问答."""
    llm = get_chat_llm()
    store = await get_vector_store()

    # 检索相关知识库片段
    docs: List[Document] = []
    try:
        filter_dict = {}
        station_id = context.get("station_id") if context else None
        if station_id:
            filter_dict["station_id"] = station_id
        docs = await store.similarity_search(
            question, k=top_k, filter=filter_dict or None
        )
    except Exception as e:
        logger.warning(f"知识库检索失败: {e}")

    knowledge = "\n---\n".join(d.page_content for d in docs) or "无相关知识库内容。"

    user_prompt = f"""【上下文】
{_format_context(context)}

【知识库片段】
{knowledge}

【用户问题】
{question}
"""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    if not llm:
        return {
            "answer": "当前未配置 LLM API Key，无法调用大模型。请先在 .env 中配置 LLM_API_KEY。",
            "sources": [{"content": d.page_content, "metadata": d.metadata} for d in docs],
        }

    try:
        answer = await llm.chat(messages)
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        return {
            "answer": f"大模型调用失败：{e}",
            "sources": [{"content": d.page_content, "metadata": d.metadata} for d in docs],
        }

    return {
        "answer": answer,
        "sources": [{"content": d.page_content, "metadata": d.metadata} for d in docs],
    }
