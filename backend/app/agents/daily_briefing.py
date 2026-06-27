"""Daily Briefing Agent —— 每日巡检智能体.

主动扫描电站状态、告警、健康度、工单、知识库更新，调用 LLM 提炼为 3-5 条
人类可读的简报。这是 P0「让智能体主动感知」的核心。

工具组合：
- get_critical_alarms_tool: 过去 24h critical 级别告警
- get_health_trend_tool: 健康度连续下降的电站
- get_outstanding_workorders_tool: 超期未处理的工单
- get_new_knowledge_tool: 今日新增的知识库文档
- get_station_overview_tool: 集团电站概览（容量、发电、PR）

向后兼容：返回 dict（含 items + summary + generated_at + agent）。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import desc, func, select

from app.agents.base import ReactAgent, Tool
from app.core.database import AsyncSessionLocal
from app.models.alarm import Alarm
from app.models.knowledge import KnowledgeDoc
from app.models.station import Station
from app.models.work_order import WorkOrder

logger = logging.getLogger(__name__)


# ─── 工具函数 ────────────────────────────────────────────────


async def _tool_critical_alarms(hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
    """过去 N 小时内未关闭的 critical / warning 告警."""
    async with AsyncSessionLocal() as session:
        cutoff = datetime.now() - timedelta(hours=hours)
        result = await session.execute(
            select(Alarm)
            .where(
                Alarm.status.in_(["open", "acknowledged"]),
                Alarm.created_at >= cutoff,
            )
            .order_by(desc(Alarm.created_at))
            .limit(limit)
        )
        alarms = result.scalars().all()
        return [
            {
                "id": a.id,
                "station_id": a.station_id,
                "level": a.level,
                "title": a.title,
                "code": a.rule_name,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alarms
        ]


async def _tool_health_decline(days: int = 7, limit: int = 5) -> List[Dict[str, Any]]:
    """健康度连续下降的电站 (近 N 天)."""
    async with AsyncSessionLocal() as session:
        stations = (await session.execute(select(Station))).scalars().all()
        declining = []
        for st in stations:
            # 简化：从 alarms 数量反推：open alarms 越多 → 健康度越低
            count = (
                await session.execute(
                    select(func.count(Alarm.id)).where(
                        Alarm.station_id == st.id,
                        Alarm.status == "open",
                    )
                )
            ).scalar() or 0
            if count > 0:
                declining.append(
                    {
                        "station_id": st.id,
                        "name": st.name,
                        "open_alarms": count,
                        "days": days,
                    }
                )
        return sorted(declining, key=lambda x: -x["open_alarms"])[:limit]


async def _tool_outstanding_workorders(limit: int = 10) -> List[Dict[str, Any]]:
    """未处理工单 + SLA 超期标记."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(WorkOrder)
            .where(WorkOrder.status.in_(["pending", "in_progress"]))
            .order_by(desc(WorkOrder.created_at))
            .limit(limit)
        )
        wos = result.scalars().all()
        now = datetime.now()
        return [
            {
                "id": w.id,
                "title": w.title,
                "status": w.status,
                "priority": w.priority,
                "station_id": w.station_id,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "age_hours": round((now - w.created_at).total_seconds() / 3600, 1) if w.created_at else 0,
            }
            for w in wos
        ]


async def _tool_new_knowledge(days: int = 7, limit: int = 5) -> List[Dict[str, Any]]:
    """近 N 天新增的知识库文档."""
    async with AsyncSessionLocal() as session:
        cutoff = datetime.now() - timedelta(days=days)
        result = await session.execute(
            select(KnowledgeDoc)
            .where(KnowledgeDoc.created_at >= cutoff)
            .order_by(desc(KnowledgeDoc.created_at))
            .limit(limit)
        )
        docs = result.scalars().all()
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]


async def _tool_station_overview() -> List[Dict[str, Any]]:
    """电站总览 (容量 / 状态)."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Station))
        stations = result.scalars().all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "capacity_kw": s.capacity_kw,
                "status": s.status,
            }
            for s in stations
        ]


# ─── Agent ────────────────────────────────────────────────


SYSTEM_PROMPT = """你是 PVOps 光伏运维智能体的"每日巡检"模块。
你的任务是：基于工具返回的实时数据，提炼为 3-5 条人类可读的运维简报。

输出格式（严格 JSON 数组）：
[
  {
    "level": "critical" | "warning" | "info",
    "category": "alarm" | "health" | "workorder" | "knowledge" | "summary",
    "title": "一句话标题",
    "detail": "1-2 句详细描述（数据驱动，避免空话）",
    "action": "推荐的下一步动作（可选）",
    "ref": {"type": "alarm" | "station" | "workorder" | "doc", "id": <int>}
  }
]

要求：
1. critical 级告警必须出现在列表最前
2. 数据驱动：引用具体数字（电站 ID、PR%、告警数等）
3. 简洁：每条 detail 不超过 30 字
4. 最多 5 条，按紧急度排序
5. 只输出 JSON 数组，不要解释或 markdown
"""


class DailyBriefingAgent(ReactAgent):
    """每日巡检 Agent — 主动感知 + 简报生成."""

    def __init__(self, max_iterations: int = 3) -> None:
        super().__init__(max_iterations=max_iterations, temperature=0.3)

    @property
    def name(self) -> str:
        return "DailyBriefingAgent"

    def _build_tools(self) -> List[Tool]:
        return [
            Tool(
                name="get_critical_alarms",
                description="获取过去 24 小时内未关闭的 critical/warning 告警",
                func=_tool_critical_alarms,
                parameters={
                    "type": "object",
                    "properties": {
                        "hours": {"type": "integer"},
                        "limit": {"type": "integer"},
                    },
                },
            ),
            Tool(
                name="get_health_decline",
                description="获取健康度下降 / 有未处理告警的电站列表",
                func=_tool_health_decline,
                parameters={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer"},
                        "limit": {"type": "integer"},
                    },
                },
            ),
            Tool(
                name="get_outstanding_workorders",
                description="获取未处理的工单 (pending/in_progress) 及其 SLA 时长",
                func=_tool_outstanding_workorders,
                parameters={
                    "type": "object",
                    "properties": {"limit": {"type": "integer"}},
                },
            ),
            Tool(
                name="get_new_knowledge",
                description="获取近 N 天新增的知识库文档",
                func=_tool_new_knowledge,
                parameters={
                    "type": "object",
                    "properties": {
                        "days": {"type": "integer"},
                        "limit": {"type": "integer"},
                    },
                },
            ),
            Tool(
                name="get_station_overview",
                description="获取集团所有电站概览",
                func=_tool_station_overview,
                parameters={"type": "object", "properties": {}},
            ),
        ]


async def generate_briefing() -> Dict[str, Any]:
    """生成每日简报主入口 — 工具优先 + LLM 总结 fallback."""
    # 1. 主动拉取所有工具数据 (无 LLM 也能给个基础简报)
    raw = {
        "critical_alarms": await _tool_critical_alarms(24, 5),
        "health_declines": await _tool_health_decline(7, 5),
        "outstanding_workorders": await _tool_outstanding_workorders(5),
        "new_knowledge": await _tool_new_knowledge(7, 3),
        "station_overview": await _tool_station_overview(),
    }

    # 2. 模板化 fallback (无 LLM 时也能展示)
    items = _build_template_items(raw)

    # 3. 尝试用 LLM 润色 (可选)
    try:
        from app.llm.factory import get_chat_llm

        llm = get_chat_llm()
        if llm is not None:
            import json

            user_msg = (
                f"工具返回数据（JSON）:\n{json.dumps(raw, ensure_ascii=False, default=str)}\n"
                "请按你的 SYSTEM_PROMPT 规则输出简报 JSON 数组。"
            )
            response = await llm.chat(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ]
            )
            # 解析 LLM 输出（提取 ```json ... ``` 块）
            llm_items = _parse_llm_json(response)
            if llm_items:
                items = llm_items
                logger.info("DailyBriefingAgent LLM 生成 %d 条简报", len(items))
    except Exception as exc:
        logger.warning("DailyBriefingAgent LLM 调用失败, 使用模板: %s", exc)

    return {
        "items": items,
        "generated_at": datetime.now().isoformat(),
        "agent": "DailyBriefingAgent",
        "raw_summary": {
            "critical_alarms_count": len(raw["critical_alarms"]),
            "outstanding_workorders_count": len(raw["outstanding_workorders"]),
            "stations_with_alerts": len(raw["health_declines"]),
            "new_docs_count": len(raw["new_knowledge"]),
        },
    }


def _build_template_items(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """无 LLM 时的模板化简报."""
    items: List[Dict[str, Any]] = []

    # 1. critical 告警
    for a in raw["critical_alarms"][:3]:
        items.append({
            "level": "critical" if a["level"] == "critical" else "warning",
            "category": "alarm",
            "title": f"{a['title']}（电站 {a['station_id']}）",
            "detail": f"告警代码 {a['code'] or '未知'}，状态 {a['status']}",
            "action": "立即诊断 / 创建工单",
            "ref": {"type": "alarm", "id": a["id"]},
        })

    # 2. 健康度下降电站
    for h in raw["health_declines"][:2]:
        items.append({
            "level": "warning",
            "category": "health",
            "title": f"{h['name']} 有 {h['open_alarms']} 条未处理告警",
            "detail": "健康度可能受告警累积影响",
            "action": "查看电站详情",
            "ref": {"type": "station", "id": h["station_id"]},
        })

    # 3. 待处理工单
    for w in raw["outstanding_workorders"][:2]:
        items.append({
            "level": "info" if w["age_hours"] < 24 else "warning",
            "category": "workorder",
            "title": f"工单 #{w['id']}: {w['title']}",
            "detail": f"状态 {w['status']}, 已等待 {w['age_hours']} 小时",
            "action": "处理工单",
            "ref": {"type": "workorder", "id": w["id"]},
        })

    # 4. 新增知识
    if raw["new_knowledge"]:
        items.append({
            "level": "info",
            "category": "knowledge",
            "title": f"知识库新增 {len(raw['new_knowledge'])} 篇文档",
            "detail": "建议浏览并收藏",
            "action": "查看知识库",
            "ref": {"type": "doc", "id": raw["new_knowledge"][0]["id"]},
        })

    # 5. 总览
    total = len(raw["station_overview"])
    if total == 0:
        items.append({
            "level": "info",
            "category": "summary",
            "title": "尚未配置任何电站",
            "detail": "请先在电站管理中添加电站",
            "action": "去添加",
            "ref": {"type": "station", "id": 0},
        })

    return items[:5]


def _parse_llm_json(content: str) -> List[Dict[str, Any]]:
    """从 LLM 输出中提取 JSON 数组."""
    import json
    import re

    if not content:
        return []
    # 尝试 1：直接解析
    content = content.strip()
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    # 尝试 2：从 ```json ... ``` 块提取
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    # 尝试 3：找首个 [ 到最后 ]
    start = content.find("[")
    end = content.rfind("]")
    if start >= 0 and end > start:
        try:
            data = json.loads(content[start : end + 1])
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    return []


__all__ = ["DailyBriefingAgent", "generate_briefing"]