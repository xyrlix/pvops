"""Agent 工具注册中心.

按业务域组织：metrics / alarms / knowledge / stations / diagnosis。
新增工具只需在对应模块实现 async 函数后在此处 ``register(...)``。
"""

from __future__ import annotations

from collections.abc import Callable  # noqa: F401
from typing import Any

from app.agents.base import Tool

# 工具注册表：name -> Tool
_registry: dict[str, Tool] = {}


def register(tool: Tool) -> None:
    """注册一个工具。重复名覆盖。"""
    _registry[tool.name] = tool


def get(name: str) -> Tool | None:
    return _registry.get(name)


def all_tools() -> list[Tool]:
    return list(_registry.values())


def all_by_names(names: list[str]) -> list[Tool]:
    return [t for t in _registry.values() if t.name in set(names)]


def clear_for_testing() -> None:
    _registry.clear()


# ─── 内置工具 ────────────────────────────────────────────────


# 注意：内置工具必须在此文件 __init__ 阶段就注册，
# 因此对应的工具函数定义放在本文件底部以避免循环 import。
async def _tool_get_station_metrics(station_id: int) -> dict[str, Any]:
    """获取电站最新实时指标（功率、发电量、PR、健康度）."""
    from app.services import metrics_service

    return await metrics_service.get_latest_station_metrics(station_id)


async def _tool_get_recent_alarms(station_id: int, limit: int = 5) -> list[dict[str, Any]]:
    """获取电站最近 N 条告警."""
    from sqlalchemy import desc, select

    from app.core.database import AsyncSessionLocal
    from app.models.alarm import Alarm
    from app.services import alarm_service  # noqa: F401

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Alarm)
            .where(Alarm.station_id == station_id)
            .order_by(desc(Alarm.created_at))
            .limit(limit)
        )
        alarms = result.scalars().all()
        return [
            {
                "id": a.id,
                "level": a.level,
                "title": a.title,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alarms
        ]


async def _tool_search_knowledge(
    query: str, station_id: int | None = None, top_k: int = 3
) -> list[dict[str, Any]]:
    """从知识库检索与 query 相关的文档片段."""
    from app.vectorstore.factory import get_vector_store

    store = await get_vector_store()
    filt = {"station_id": station_id} if station_id else None
    docs = await store.similarity_search(query, k=top_k, filter=filt)
    return [{"content": d.page_content, "metadata": d.metadata} for d in docs]


async def _tool_diagnose_station(station_id: int) -> dict[str, Any]:
    """对电站执行诊断分析，返回结构化 finding 列表."""
    from app.services import diagnosis_service

    return await diagnosis_service.diagnose_station(station_id)


# 注册
register(
    Tool(
        name="get_station_metrics",
        description="获取电站最新实时指标（功率、发电量、PR、健康度）",
        func=_tool_get_station_metrics,
        parameters={
            "type": "object",
            "properties": {
                "station_id": {"type": "integer", "description": "电站 ID"},
            },
            "required": ["station_id"],
        },
    )
)

register(
    Tool(
        name="get_recent_alarms",
        description="获取电站最近 N 条告警",
        func=_tool_get_recent_alarms,
        parameters={
            "type": "object",
            "properties": {
                "station_id": {"type": "integer"},
                "limit": {"type": "integer", "description": "返回数量，默认 5"},
            },
            "required": ["station_id"],
        },
    )
)

register(
    Tool(
        name="search_knowledge",
        description="从知识库检索与 query 相关的运维文档片段",
        func=_tool_search_knowledge,
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "station_id": {"type": "integer"},
                "top_k": {"type": "integer"},
            },
            "required": ["query"],
        },
    )
)

register(
    Tool(
        name="diagnose_station",
        description="对电站执行规则引擎诊断，返回结构化 finding 列表",
        func=_tool_diagnose_station,
        parameters={
            "type": "object",
            "properties": {
                "station_id": {"type": "integer"},
            },
            "required": ["station_id"],
        },
    )
)


__all__ = ["register", "get", "all_tools", "all_by_names", "clear_for_testing"]
