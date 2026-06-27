"""agents 单测.

聚焦 ReactAgent 框架本身（不依赖真实 LLM）：
- tool call JSON 解析
- 自然语言回答直接返回
- 多次工具调用循环
- 未注册工具的容错
- 无 LLM 时的 graceful 返回
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents import base as agent_base
from app.agents.base import ReactAgent, Tool
from app.agents.diagnosis_agent import DiagnosisAgent
from app.agents.rag_agent import RAGAgent
from app.agents import tools as tool_registry


# ─── helpers ────────────────────────────────────────────────


def _mk_llm_mock(responses: List[str]) -> Any:
    """模拟 LLMClient，按顺序返回预设字符串."""
    llm = MagicMock()
    llm.chat = AsyncMock(side_effect=responses)
    return llm


def _json_call(name: str, **kwargs: Any) -> str:
    return json.dumps({"action": name, "action_input": kwargs}, ensure_ascii=False)


# ─── Tool call JSON 解析 ────────────────────────────────────


class _EmptyAgent(ReactAgent):
    """无工具的 agent，便于测试框架逻辑."""

    @property
    def name(self) -> str:
        return "EmptyAgent"

    def _build_tools(self) -> List[Tool]:
        return []


class _EchoAgent(ReactAgent):
    """测试用 agent，工具为 echo."""

    @property
    def name(self) -> str:
        return "EchoAgent"

    def _build_tools(self) -> List[Tool]:
        return [
            Tool(
                name="echo",
                description="回显输入",
                func=self._echo,
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            )
        ]

    async def _echo(self, text: str) -> str:
        return f"echo:{text}"


@pytest.mark.asyncio
async def test_parse_tool_call_valid() -> None:
    a = _EmptyAgent()
    out = await a._maybe_call_tool(_json_call("foo", x=1))
    assert out == {"action": "foo", "action_input": {"x": 1}}


@pytest.mark.asyncio
async def test_parse_tool_call_non_json() -> None:
    a = _EmptyAgent()
    assert await a._maybe_call_tool("just plain text") is None


@pytest.mark.asyncio
async def test_parse_tool_call_invalid_json() -> None:
    a = _EmptyAgent()
    assert await a._maybe_call_tool("{invalid json") is None


@pytest.mark.asyncio
async def test_parse_tool_call_missing_keys() -> None:
    a = _EmptyAgent()
    # 缺 action_input
    assert await a._maybe_call_tool(json.dumps({"action": "x"})) is None
    # 缺 action
    assert await a._maybe_call_tool(json.dumps({"action_input": {}})) is None


# ─── ReAct 循环 ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_returns_natural_language_without_tools() -> None:
    a = _EmptyAgent()
    with patch.object(agent_base, "get_chat_llm", return_value=_mk_llm_mock(["你好，有什么可以帮你？"])):
        out = await a.run("hi")
    assert out["answer"] == "你好，有什么可以帮你？"
    assert out["tool_calls"] == []
    assert out["iterations"] == 1
    assert out["agent"] == "EmptyAgent"


@pytest.mark.asyncio
async def test_run_returns_graceful_when_llm_missing() -> None:
    a = _EmptyAgent()
    with patch.object(agent_base, "get_chat_llm", return_value=None):
        out = await a.run("hi")
    assert "未配置 LLM" in out["answer"]
    assert out["tool_calls"] == []


@pytest.mark.asyncio
async def test_run_executes_tool_then_answers() -> None:
    """第一次返回 tool call JSON，第二次返回自然语言."""
    a = _EchoAgent()
    responses = [
        _json_call("echo", text="hello"),
        "已收到：echo:hello",
    ]
    with patch.object(agent_base, "get_chat_llm", return_value=_mk_llm_mock(responses)):
        out = await a.run("请 echo hello")

    assert out["answer"] == "已收到：echo:hello"
    assert len(out["tool_calls"]) == 1
    assert out["tool_calls"][0]["tool"] == "echo"
    assert out["tool_calls"][0]["output"] == "echo:hello"
    assert out["iterations"] == 2


@pytest.mark.asyncio
async def test_run_max_iterations_caps() -> None:
    """LLM 一直返回 tool call，达到 max_iterations 后强行收敛."""
    a = _EchoAgent()
    responses = [_json_call("echo", text=f"call{i}") for i in range(10)]
    a.max_iterations = 3

    with patch.object(agent_base, "get_chat_llm", return_value=_mk_llm_mock(responses)):
        out = await a.run("stuck")

    assert out["iterations"] == 3
    assert len(out["tool_calls"]) == 3
    assert "达到最大迭代次数" in out["answer"]


@pytest.mark.asyncio
async def test_run_unknown_tool_records_error() -> None:
    """调用了未注册的工具：messages 中追加错误，不抛异常."""
    a = _EchoAgent()  # 只注册了 echo
    responses = [
        _json_call("ghost_tool", x=1),  # 不存在
        "无法完成",  # 二次回退
    ]
    with patch.object(agent_base, "get_chat_llm", return_value=_mk_llm_mock(responses)):
        out = await a.run("test")

    # 第二次调用应该返回自然语言
    assert out["answer"] == "无法完成"
    # tool_calls 应该没有记录（未注册工具）
    assert out["tool_calls"] == []
    assert out["iterations"] == 2


@pytest.mark.asyncio
async def test_run_tool_exception_captured_in_record() -> None:
    """工具抛异常时，error 字段被填充，循环继续."""
    class _BoomAgent(ReactAgent):
        @property
        def name(self) -> str:
            return "BoomAgent"

        def _build_tools(self) -> List[Tool]:
            async def boom() -> str:
                raise RuntimeError("kaboom")

            return [Tool(name="boom", description="炸", func=boom, parameters={})]

    a = _BoomAgent()
    responses = [
        _json_call("boom"),
        "降级回答",
    ]
    with patch.object(agent_base, "get_chat_llm", return_value=_mk_llm_mock(responses)):
        out = await a.run("test")

    assert len(out["tool_calls"]) == 1
    assert out["tool_calls"][0]["error"] == "kaboom"
    assert out["answer"] == "降级回答"


# ─── 工具注册表 ─────────────────────────────────────────────


def test_tools_registry_has_builtin() -> None:
    names = {t.name for t in tool_registry.all_tools()}
    for expected in ("get_station_metrics", "get_recent_alarms", "search_knowledge", "diagnose_station"):
        assert expected in names


def test_tools_registry_register_and_get() -> None:
    class _Dummy:
        async def __call__(self) -> str:
            return "x"

    tool_registry.register(Tool(name="_test_dummy", description="测试", func=_Dummy()))
    t = tool_registry.get("_test_dummy")
    assert t is not None
    assert t.description == "测试"


def test_tools_registry_filter_by_names() -> None:
    selected = tool_registry.all_by_names(["search_knowledge", "diagnose_station"])
    assert {t.name for t in selected} == {"search_knowledge", "diagnose_station"}


# ─── DiagnosisAgent 兼容接口 ────────────────────────────────


@pytest.mark.asyncio
async def test_diagnosis_agent_compat_method_passes_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """兼容旧 diagnose_station() 接口：直接走 diagnosis_service."""
    from app.services import diagnosis_service

    monkeypatch.setattr(
        diagnosis_service,
        "diagnose_station",
        AsyncMock(return_value={"station_id": 1, "findings": [], "summary": "ok"}),
    )
    agent = DiagnosisAgent()
    out = await agent.diagnose_station(1)
    assert out == {"station_id": 1, "findings": [], "summary": "ok"}


def test_diagnosis_agent_has_expected_tools() -> None:
    a = DiagnosisAgent()
    tools = a._build_tools()
    names = {t.name for t in tools}
    assert "diagnose_station" in names
    assert "search_knowledge" in names
    assert "get_recent_alarms" in names


def test_rag_agent_has_expected_tools() -> None:
    a = RAGAgent()
    tools = a._build_tools()
    names = {t.name for t in tools}
    assert "search_knowledge" in names
    assert "get_station_metrics" in names
    assert "get_recent_alarms" in names