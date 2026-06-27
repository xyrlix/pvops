"""对话服务（简单内存历史）."""

import logging
import uuid

from app.agents.diagnosis_agent import DiagnosisAgent
from app.agents.rag_agent import ask

logger = logging.getLogger(__name__)

# 内存会话历史：{session_id: [messages]}
_sessions: dict[str, list[dict[str, str]]] = {}
MAX_HISTORY = 10


def get_session_history(session_id: str) -> list[dict[str, str]]:
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


def _is_diagnosis_request(message: str, context: dict | None) -> bool:
    """判断当前请求是否需要触发诊断."""
    if context and context.get("type") in ("station", "device", "alarm"):
        return True
    diagnose_keywords = ["诊断", "分析", "什么问题", "怎么回事", "为什么", "故障", "告警原因"]
    return any(k in message for k in diagnose_keywords)


def _format_diagnosis(result: dict) -> str:
    """把诊断结果格式化为自然语言回答."""
    lines = []
    lines.append(f"## {result.get('station_name', '电站')} 诊断结果")
    lines.append(f"- 综合健康度：{result.get('overall_health', 0)} 分")
    lines.append(f"- 总结：{result.get('summary', '')}")

    findings = result.get("findings") or []
    if findings:
        lines.append("\n### 发现异常")
        for idx, item in enumerate(findings, 1):
            severity = "🔴" if item.get("severity") == "critical" else "🟡"
            lines.append(f"{severity} {idx}. {item.get('title', '未命名')}")
            lines.append(f"   描述：{item.get('description', '-')}")
            lines.append(f"   根因：{item.get('root_cause', '-')}")
            suggestions = item.get("suggestions") or []
            if suggestions:
                lines.append(f"   建议：{'；'.join(suggestions)}")

    suggestions = result.get("suggestions") or []
    if suggestions and not findings:
        lines.append("\n### 建议\n- " + "\n- ".join(suggestions))

    return "\n".join(lines)


async def _run_diagnosis(context: dict | None) -> dict | None:
    """根据上下文执行诊断."""
    if not context:
        return None

    agent = DiagnosisAgent()
    ctype = context.get("type")
    station_id = context.get("station_id")
    if not station_id:
        return None

    try:
        if ctype == "device":
            device_id = context.get("device_code") or context.get("device_id")
            if device_id:
                return await agent.diagnose_device(int(station_id), device_id)
        return await agent.diagnose_station(int(station_id))
    except Exception as e:
        logger.error(f"诊断执行失败: {e}")
        return None


async def chat(
    message: str,
    session_id: str | None = None,
    context: dict | None = None,
) -> dict:
    """处理一次对话."""
    if not session_id or session_id not in _sessions:
        session_id = create_session()

    # 诊断意图：优先调用诊断 Agent 并把结果加入上下文
    diagnosis_result = None
    if _is_diagnosis_request(message, context):
        diagnosis_result = await _run_diagnosis(context)

    if diagnosis_result:
        answer = _format_diagnosis(diagnosis_result)
        # 同时把诊断结果作为上下文交给 RAG，便于 LLM 基于知识库进一步润色/补充
        rag_context = dict(context or {})
        rag_context["diagnosis_result"] = diagnosis_result
        rag_result = await ask(
            message, context=rag_context, history=get_session_history(session_id)
        )
        # 如果 LLM 返回了有效润色内容且不是配置错误提示，则优先使用 LLM 回答
        llm_answer = rag_result.get("answer", "")
        if llm_answer and "未配置 LLM API Key" not in llm_answer and "调用失败" not in llm_answer:
            answer = llm_answer

        append_message(session_id, "user", message)
        append_message(session_id, "assistant", answer)
        return {
            "session_id": session_id,
            "answer": answer,
            "sources": rag_result.get("sources", []),
        }

    history = get_session_history(session_id)
    result = await ask(message, context=context, history=history)

    append_message(session_id, "user", message)
    append_message(session_id, "assistant", result["answer"])

    return {
        "session_id": session_id,
        "answer": result["answer"],
        "sources": result.get("sources", []),
    }
