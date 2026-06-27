"""RAG 问答 Agent —— ReAct 循环 + 工具增强.

工具组合：
- search_knowledge：知识库检索
- get_station_metrics：补充实时数据上下文
- get_recent_alarms：补充告警上下文

向后兼容：保留旧 ``ask()`` 函数接口（RAG + 单轮对话）。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.agents.base import ReactAgent, Tool
from app.agents import tools as tool_registry
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


class RAGAgent(ReactAgent):
    """RAG 问答 Agent."""

    @property
    def name(self) -> str:
        return "RAGAgent"

    def _build_tools(self) -> List[Tool]:
        return tool_registry.all_by_names([
            "search_knowledge",
            "get_station_metrics",
            "get_recent_alarms",
        ])

    async def ask(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """兼容旧接口：直接走 RAG 链路，单轮对话，不走 ReAct."""
        llm = get_chat_llm()
        store = await get_vector_store()

        docs: List[Document] = []
        try:
            filter_dict: Dict[str, Any] = {}
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

        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
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

    async def ask_with_tools(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """走 ReAct 循环：让 LLM 决定是否调 search_knowledge / get_station_metrics 等."""
        full_query = question
        if context:
            full_query = f"{_format_context(context)}\n\n问题：{question}"
        return await self.run(full_query)


__all__ = ["RAGAgent", "_format_context"]


# 保留旧模块级 ask 函数（向后兼容 chat_service 调用）
async def ask(
    question: str,
    context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 4,
) -> Dict[str, Any]:
    """向后兼容的 RAG 问答入口."""
    agent = RAGAgent()
    return await agent.ask(question, context=context, history=history, top_k=top_k)