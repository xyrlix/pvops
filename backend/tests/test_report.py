"""report_service 单元测试.

聚焦 _calculate_stats / _calculate_avg_pr 的统计聚合逻辑，
通过 mock AsyncSession 注入数据行，验证汇总正确性。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import report_service
from app.services.report_service import _calculate_avg_pr, _calculate_stats

# ─── helpers ────────────────────────────────────────────────


def _row(day: str, daily_energy: float | None, avg_power: float | None) -> Any:
    return SimpleNamespace(day=day, daily_energy=daily_energy, avg_power=avg_power)


def _pr_row(avg_pr: float | None, active_power: float | None, irradiance: float | None) -> Any:
    return SimpleNamespace(avg_pr=avg_pr, active_power=active_power, irradiance=irradiance)


# ─── _calculate_stats ────────────────────────────────────────


@pytest.mark.asyncio
async def test_calculate_stats_sums_and_returns_daily_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    rows = [
        _row("2024-06-01", 1000.0, 80.0),
        _row("2024-06-02", 1500.0, 100.0),
        _row("2024-06-03", None, 90.0),  # None 应被 0 替代
    ]
    result = MagicMock()
    result.all.return_value = rows
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    # 第一次 execute 返回 daily rows，第二次（_calculate_avg_pr）返回空
    pr_result = MagicMock()
    pr_result.all.return_value = []
    session.execute = AsyncMock(side_effect=[result, pr_result])

    monkeypatch.setattr(report_service, "AsyncSessionLocal", lambda: session)

    start = datetime(2024, 6, 1)
    end = datetime(2024, 6, 4)
    stats = await _calculate_stats(None, start, end)

    assert stats["total_energy_kwh"] == 2500.0
    assert stats["avg_pr"] is None  # 无 PR 行
    assert stats["avg_health_score"] is None
    assert len(stats["daily_details"]) == 3
    assert stats["daily_details"][0] == {
        "date": "2024-06-01",
        "daily_energy_kwh": 1000.0,
        "avg_power_kw": 80.0,
    }
    # None 兜底为 0
    assert stats["daily_details"][2]["daily_energy_kwh"] == 0.0


@pytest.mark.asyncio
async def test_calculate_stats_empty_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = []
    pr_result = MagicMock()
    pr_result.all.return_value = []
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.execute = AsyncMock(side_effect=[result, pr_result])

    monkeypatch.setattr(report_service, "AsyncSessionLocal", lambda: session)

    stats = await _calculate_stats(None, datetime.now() - timedelta(days=1), datetime.now())
    assert stats["total_energy_kwh"] == 0
    assert stats["daily_details"] == []


# ─── _calculate_avg_pr ──────────────────────────────────────


@pytest.mark.asyncio
async def test_calculate_avg_pr_ignores_low_irradiance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """仅对辐照 > 200 的数据点计算平均 PR."""
    session = MagicMock()
    rows = [
        # (pr_val, active_power, irradiance) — 直接给计算后的 PR
        _pr_row(avg_pr=None, active_power=200.0, irradiance=400.0),  # 计入 → 0.5
        _pr_row(avg_pr=None, active_power=300.0, irradiance=600.0),  # 计入 → 0.5
        _pr_row(avg_pr=None, active_power=50.0, irradiance=100.0),  # 忽略
    ]
    result = MagicMock()
    result.all.return_value = rows
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.execute = AsyncMock(return_value=result)

    monkeypatch.setattr(report_service, "AsyncSessionLocal", lambda: session)

    avg_pr = await _calculate_avg_pr(None, datetime.now() - timedelta(days=1), datetime.now())
    # 0.5 和 0.5 平均 = 0.5
    assert avg_pr is not None
    assert abs(avg_pr - 0.5) < 0.001


@pytest.mark.asyncio
async def test_calculate_avg_pr_uses_avg_pr_column_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """若行里已有 avg_pr 字段，优先使用."""
    session = MagicMock()
    rows = [
        _pr_row(avg_pr=0.8, active_power=None, irradiance=400.0),
        _pr_row(avg_pr=0.85, active_power=None, irradiance=500.0),
    ]
    result = MagicMock()
    result.all.return_value = rows
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.execute = AsyncMock(return_value=result)

    monkeypatch.setattr(report_service, "AsyncSessionLocal", lambda: session)

    avg_pr = await _calculate_avg_pr(None, datetime.now() - timedelta(days=1), datetime.now())
    assert avg_pr is not None
    assert abs(avg_pr - 0.825) < 0.001


@pytest.mark.asyncio
async def test_calculate_avg_pr_returns_none_when_no_high_irradiance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    rows = [_pr_row(avg_pr=None, active_power=10.0, irradiance=50.0)]  # 全部低辐照
    result = MagicMock()
    result.all.return_value = rows
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.execute = AsyncMock(return_value=result)

    monkeypatch.setattr(report_service, "AsyncSessionLocal", lambda: session)

    avg_pr = await _calculate_avg_pr(None, datetime.now() - timedelta(days=1), datetime.now())
    assert avg_pr is None
