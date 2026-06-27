"""诊断 Agent —— ReAct 循环：诊断 → 检索知识 → LLM 润色 → 输出.

工具组合：
- diagnose_station：规则引擎结果
- search_knowledge：相关运维知识库片段
- get_recent_alarms：补充上下文

向后兼容：保留 ``diagnose_station()`` 简单接口（无 LLM 时退化）。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.agents.base import ReactAgent, Tool
from app.agents import tools as tool_registry

logger = logging.getLogger(__name__)


class DiagnosisAgent(ReactAgent):
    """电站/设备诊断 Agent."""

    @property
    def name(self) -> str:
        return "DiagnosisAgent"

    def _build_tools(self) -> List[Tool]:
        return tool_registry.all_by_names([
            "diagnose_station",
            "search_knowledge",
            "get_recent_alarms",
        ])

    async def diagnose_station(self, station_id: int) -> Dict[str, Any]:
        """诊断电站：兼容旧接口（直接调规则引擎，不走 ReAct）.

        适用于需要快速返回结构化 finding、不需要 LLM 润色的场景。
        """
        from app.services import diagnosis_service

        return await diagnosis_service.diagnose_station(station_id)

    async def diagnose_device(
        self,
        station_id: int,
        device_id: str,
    ) -> Dict[str, Any]:
        """设备级诊断（兼容旧接口）."""
        result = await self.diagnose_station(station_id)
        device_findings = [
            f for f in result.get("findings", [])
            if device_id in f.get("title", "")
        ]
        result["findings"] = device_findings
        result["summary"] = f"设备 {device_id} 诊断完成，发现 {len(device_findings)} 项异常。"
        return result

    async def diagnose_with_rag(self, station_id: int) -> Dict[str, Any]:
        """诊断 + RAG 增强：先调规则引擎，再让 LLM 检索知识 + 润色.

        返回 ``{"answer": str, "tool_calls": [...], "iterations": int, "agent": "DiagnosisAgent"}``.
        """
        query = f"对电站 {station_id} 进行全面诊断分析，包括根因和运维建议。"
        return await self.run(query, station_id=station_id)


__all__ = ["DiagnosisAgent"]