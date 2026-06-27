"""Agent 智能体路由.

- GET  /api/v1/agent/briefing  → 每日巡检简报（DailyBriefingAgent）
- POST /api/v1/agent/diagnose-and-act  → 诊断并一键创建工单
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends

from app.agents.daily_briefing import generate_briefing
from app.agents.diagnosis_agent import DiagnosisAgent
from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.services import work_order_service

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/briefing")
async def get_daily_briefing() -> dict[str, Any]:
    """生成每日巡检简报.

    返回结构::

        {
            "items": [
                {
                    "level": "critical" | "warning" | "info",
                    "category": "alarm" | "health" | "workorder" | "knowledge" | "summary",
                    "title": str,
                    "detail": str,
                    "action": str,
                    "ref": {"type": ..., "id": ...}
                }
            ],
            "generated_at": "2026-06-27T14:32:00",
            "agent": "DailyBriefingAgent",
            "raw_summary": {...}
        }
    """
    return await generate_briefing()


@router.post("/diagnose-and-act/{station_id}")
async def diagnose_and_create_work_order(
    station_id: int,
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    """诊断电站并自动创建工单（Agent 闭环行动）.

    1. 调 DiagnosisAgent 跑诊断
    2. 提取 critical / warning 级 finding
    3. 为每个 finding 创建对应工单
    4. 返回工单 ID 列表

    返回结构::

        {
            "diagnosis_id": int,
            "station_id": int,
            "findings_count": int,
            "workorders_created": [{"id": int, "title": str, "priority": str}],
            "summary": "由 Agent 自动创建 N 个工单"
        }
    """
    agent = DiagnosisAgent()
    diagnosis = await agent.diagnose_station(station_id)
    findings = diagnosis.get("findings", []) or []

    workorders = []
    for f in findings:
        severity = f.get("severity", "info")
        # 只有 critical / warning 自动建工单；info 让用户决定
        if severity not in ("critical", "warning"):
            continue
        priority = "urgent" if severity == "critical" else "high"
        async with AsyncSessionLocal() as session:
            wo = await work_order_service.create_work_order(
                session,
                title=f"[自动] {f.get('title', '诊断异常')}",
                description=(
                    f"由 AI 智能体自动创建（基于诊断报告）\n\n"
                    f"类别：{f.get('category', '未知')}\n"
                    f"证据：{f.get('evidence', '-')}\n"
                    f"根因：{f.get('root_cause', '-')}\n"
                    f"建议：{', '.join(f.get('suggestions', []))}"
                ),
                priority=priority,
                assignee=None,
                created_by=f"AI-Agent ({current_user.username})",
                station_id=station_id,
                tenant_id=None,
            )
        workorders.append({
            "id": wo.id,
            "title": wo.title,
            "priority": wo.priority,
        })

    return {
        "diagnosis_id": None,  # 暂时不存盘诊断报告
        "station_id": station_id,
        "findings_count": len(findings),
        "workorders_created": workorders,
        "summary": f"AI 智能体基于诊断报告自动创建 {len(workorders)} 个工单" if workorders else "无 critical/warning 级发现，无需建工单",
    }


__all__ = ["router"]
