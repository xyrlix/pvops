"""对话服务（简单内存历史）."""

import logging
import uuid
from typing import Dict, List, Optional

from app.agents.rag_agent import ask

logger = logging.getLogger(__name__)

# 内存会话历史：{session_id: [messages]}
_sessions: Dict[str, List[Dict[str, str]]] = {}
MAX_HISTORY = 10


def get_session_history(session_id: str) -> List[Dict[str, str]]:
    return _sessions.get(session_id, [])


def create_session() -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = []
    return session_id


def append_message(session_id: str, role: str, content: str) -> None:
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"role": role, "content": content})
    # 保留最近 N 轮
    if len(_sessions[session_id]) > MAX_HISTORY * 2:
        _sessions[session_id] = _sessions[session_id][-(MAX_HISTORY * 2) :]


async def chat(
    message: str,
    session_id: Optional[str] = None,
    context: Optional[Dict] = None,
) -> Dict:
    """处理一次对话."""
    if not session_id or session_id not in _sessions:
        session_id = create_session()

    history = get_session_history(session_id)
    result = await ask(message, context=context, history=history)

    append_message(session_id, "user", message)
    append_message(session_id, "assistant", result["answer"])

    return {
        "session_id": session_id,
        "answer": result["answer"],
        "sources": result.get("sources", []),
    }
