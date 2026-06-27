"""RealDataProvider —— 真实数据从时序仓库（TDengine / SQLite）+ 业务库聚合.

当 settings.use_mock_data=False 时使用本实现；空数据时返回零值或空列表，
不再做 mock fallback（与 MockDataProvider 行为差异由调用方显式处理）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.demo.provider import DataProvider
from app.repositories import get_repository


class RealDataProvider(DataProvider):
    """读时序仓库 + 业务库的组合实现.

    注意：metrics_service 层仍保留空值时的兜底（向后兼容），但本 provider
    不再内置 mock；下游若仍需演示数据，应当显式注入 MockDataProvider。
    """

    async def get_latest_station_metrics(
        self, station_id: int, capacity_kw: float = 1000.0
    ) -> Dict[str, Any]:
        repo = get_repository()
        metrics = await repo.get_latest_station_metrics(station_id)
        metrics.setdefault("capacity_kw", capacity_kw)
        return metrics

    async def get_metric_history(
        self,
        station_id: int,
        metric: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        points: int = 144,
    ) -> List[Dict[str, Any]]:
        repo = get_repository()
        return await repo.get_metric_history(station_id, metric, start, end)

    async def get_station_overview(
        self, stations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # 真实模式下：仅返回基础字段，由 dashboard_service 自己做实际计算。
        return [
            {
                "station_id": s["id"],
                "name": s.get("name") or f"电站 {s['id']}",
                "capacity_kw": s.get("capacity_kw") or 0,
                "status": s.get("status") or "active",
            }
            for s in stations
        ]

    async def get_efficiency(
        self, station_id: int, capacity_kw: float = 1000.0
    ) -> Dict[str, Any]:
        # TODO: 接入 PR 计算服务；当前返回 0 占位避免业务代码崩。
        return {
            "station_id": station_id,
            "capacity_kw": capacity_kw,
            "daily_energy_kwh": 0.0,
            "equivalent_hours": 0.0,
            "pr": 0.0,
            "system_efficiency": 0.0,
        }

    async def get_loss_breakdown(
        self, station_id: int, capacity_kw: float = 1000.0
    ) -> Dict[str, Any]:
        # TODO: 接入损失分解服务
        return {
            "station_id": station_id,
            "theoretical_kwh": 0.0,
            "actual_kwh": 0.0,
            "total_loss_kwh": 0.0,
            "total_loss_cny": 0.0,
            "breakdown": [],
        }

    async def get_health_trend(
        self, station_id: int, days: int = 30
    ) -> List[Dict[str, Any]]:
        # TODO: 接入 health_score 历史；当前返回空，前端会显示 PvEmpty
        return []

    async def get_inverter_comparison(
        self, station_id: int, inverters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # TODO: 接入逆变器效率对比；当前返回入参透传
        return [
            {
                "inverter_id": inv.get("inverter_id", f"INV{i:03d}"),
                "name": inv.get("name") or f"逆变器 {i+1}",
                "capacity_kw": inv.get("capacity_kw") or 0,
                "active_power_kw": 0.0,
                "daily_energy_kwh": 0.0,
                "utilization_rate": 0.0,
                "status": inv.get("status") or "online",
            }
            for i, inv in enumerate(inverters)
        ]

    async def get_string_dispersion(
        self, station_id: int, strings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # TODO: 接入组串电流离散率计算
        return [
            {
                "string_id": s.get("string_id", f"STR{i:03d}"),
                "name": s.get("name") or f"组串 {i+1}",
                "inverter_id": s.get("inverter_id") or "INV001",
                "current_a": 0.0,
                "capacity_kw": s.get("capacity_kw") or 0,
                "avg_current_a": 0.0,
                "dispersion_rate": 0.0,
            }
            for i, s in enumerate(strings)
        ]