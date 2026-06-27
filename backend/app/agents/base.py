"""Agent 抽象层.

定义 ``Agent`` Protocol 与 ``Tool`` Protocol，并提供简单的 ReAct 循环：
1. 把用户问题 + 工具列表发给 LLM
2. LLM 决定调哪个工具（function calling 风格）
3. 工具返回结果追加到消息
4. 重复直到 LLM 不再调用工具或达到最大步数

不依赖 LangGraph / LangChain 等大框架，保持轻量。LLM 必须支持
OpenAI 风格 function calling；非 OpenAI 协议 provider 应在
``LLMProvider.chat()`` 内做适配（待 #5 后续任务）。
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from app.llm.factory import get_chat_llm

logger = logging.getLogger(__name__)


# ─── Tool 抽象 ───────────────────────────────────────────────


@dataclass
class Tool:
    """可被 agent 调用的工具."""

    name: str
    description: str
    func: Callable[..., Awaitable[Any]]
    # JSON Schema 形式的参数定义
    parameters: dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})


# ─── Agent 抽象 ─────────────────────────────────────────────


@runtime_checkable
class Agent(Protocol):
    """Agent 通用接口."""

    @property
    def name(self) -> str: ...

    async def run(self, query: str, **kwargs: Any) -> dict[str, Any]: ...


# ─── ReAct 循环 ─────────────────────────────────────────────


# 工具调用指令的 JSON 模板（OpenAI 风格）。当 provider 不支持 function calling
# 时，可以让 LLM 直接输出 JSON 来"模拟"工具选择。
TOOL_CALL_PROMPT_TEMPLATE = """你是一名光伏运维智能体，可以使用以下工具：

{tool_descriptions}

当需要使用工具时，**严格**输出以下 JSON（不要任何额外文字，不要 markdown）：
{{"action": "<tool_name>", "action_input": {{<args>}}}}

如果你已有足够信息回答用户，直接以自然语言回答，不需要 JSON。
"""


@dataclass
class AgentRunResult:
    """agent 执行结果."""

    final_answer: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0


class ReactAgent(ABC):
    """ReAct 风格 agent 抽象基类.

    子类实现 ``_build_tools()`` 注册可用工具；``run()`` 调用 LLM 直到收敛。
    """

    def __init__(self, max_iterations: int = 5, temperature: float = 0.2) -> None:
        self.max_iterations = max_iterations
        self.temperature = temperature
        self._tools: dict[str, Tool] = {}

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def _build_tools(self) -> list[Tool]: ...

    def _register_tools(self, tools: list[Tool]) -> None:
        self._tools = {t.name: t for t in tools}

    def _format_tool_descriptions(self) -> str:
        lines = []
        for t in self._build_tools():
            lines.append(f"- {t.name}: {t.description}")
            if t.parameters.get("properties"):
                params = ", ".join(t.parameters["properties"].keys())
                lines.append(f"  参数: {params}")
        return "\n".join(lines) or "（无可用工具）"

    async def _maybe_call_tool(self, content: str) -> dict[str, Any] | None:
        """从 LLM 输出中解析 tool call JSON."""
        content = content.strip()
        if not content.startswith("{"):
            return None
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        if "action" in data and "action_input" in data:
            return {"action": data["action"], "action_input": data["action_input"]}
        return None

    async def run(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """执行 ReAct 循环."""
        self._register_tools(self._build_tools())

        llm = get_chat_llm()
        tool_calls: list[dict[str, Any]] = []
        iterations = 0

        if llm is None:
            # 无 LLM：直接退化为规则引擎路径
            return {
                "answer": "当前未配置 LLM API Key，无法调用大模型。请先在 .env 中配置 LLM_API_KEY。",
                "tool_calls": [],
                "iterations": 0,
                "agent": self.name,
            }

        system_prompt = TOOL_CALL_PROMPT_TEMPLATE.format(
            tool_descriptions=self._format_tool_descriptions()
        )
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        for i in range(self.max_iterations):
            iterations = i + 1
            content = await llm.chat(messages, temperature=self.temperature)
            call = await self._maybe_call_tool(content)

            if call is None:
                # 自然语言回答 → 终止
                return {
                    "answer": content,
                    "tool_calls": tool_calls,
                    "iterations": iterations,
                    "agent": self.name,
                }

            # 执行工具
            tool = self._tools.get(call["action"])
            if tool is None:
                logger.warning("Agent %s 调用了未注册工具: %s", self.name, call["action"])
                messages.append({"role": "user", "content": f"错误：未注册的工具 {call['action']}"})
                continue

            tool_record = {
                "tool": call["action"],
                "input": call["action_input"],
                "output": None,
                "error": None,
            }
            try:
                tool_record["output"] = await tool.func(**call["action_input"])
            except Exception as exc:
                logger.exception("Agent %s 工具 %s 执行失败", self.name, tool.name)
                tool_record["error"] = str(exc)
            tool_calls.append(tool_record)

            messages.append({"role": "assistant", "content": content})
            messages.append(
                {
                    "role": "user",
                    "content": f"工具 {call['action']} 返回: {tool_record['output']!r}\n请基于此继续回答用户问题，或继续调用其他工具。",
                }
            )

        return {
            "answer": f"达到最大迭代次数 {self.max_iterations}，未能收敛。已执行的工具调用：{tool_calls}",
            "tool_calls": tool_calls,
            "iterations": iterations,
            "agent": self.name,
        }


__all__ = ["Agent", "ReactAgent", "Tool", "AgentRunResult"]
