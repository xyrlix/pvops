"""AI Copilot 对话接口."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from app.agents import chat_service

router = APIRouter()


class ChatRequest:
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@router.post("")
async def chat(request: Dict[str, Any]):
    """AI 对话."""
    message = request.get("message", "")
    session_id = request.get("session_id")
    context = request.get("context")
    return await chat_service.chat(message, session_id=session_id, context=context)


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str):
    """获取会话历史."""
    return {"session_id": session_id, "history": chat_service.get_session_history(session_id)}
