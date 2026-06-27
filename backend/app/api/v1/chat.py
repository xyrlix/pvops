"""AI Copilot 对话接口."""

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.agents import chat_service
from app.core.deps import get_current_user
from app.core.limiter import limiter

router = APIRouter(dependencies=[Depends(get_current_user)])


class ChatRequest:
    message: str
    session_id: str | None = None
    context: dict[str, Any] | None = None


@router.post("")
@limiter.limit("30/minute")  # LLM 调用配额与防滥用：每用户每分钟 30 次
async def chat(request: Request, payload: dict[str, Any]):
    """AI 对话."""
    message = payload.get("message", "")
    session_id = payload.get("session_id")
    context = payload.get("context")
    return await chat_service.chat(message, session_id=session_id, context=context)


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str):
    """获取会话历史."""
    return {"session_id": session_id, "history": chat_service.get_session_history(session_id)}
