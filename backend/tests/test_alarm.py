"""alarm_service 单元测试.

- 纯函数 _level_to_priority 全分支覆盖
- check_alarms 规则引擎：注入 mock Session + InverterData，断言告警生成。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import alarm_service
from app.services.alarm_service import (
    _level_to_priority,
    check_alarms,
)

# ─── _level_to_priority ──────────────────────────────────────


def test_level_to_priority_known_levels() -> None:
    assert _level_to_priority("critical") == "urgent"
    assert _level_to_priority("warning") == "high"
    assert _level_to_priority("info") == "medium"


def test_level_to_priority_unknown_falls_back_to_medium() -> None:
    assert _level_to_priority("debug") == "medium"
    assert _level_to_priority("") == "medium"
    assert _level_to_priority("RANDOM") == "medium"


# ─── check_alarms 规则引擎 ──────────────────────────────────


def _mock_session_with_recent(recent: list[Any]) -> Any:
    """构造 AsyncSession，最近数据查询返回 recent 列表."""
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)

    result = MagicMock()
    result.scalars.return_value.all.return_value = recent

    # 让 session.execute() 在第一个调用返回 result，第二个起返回 None
    # （check_alarms 内部多次 execute；这里只需要第一条）
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.mark.asyncio
async def test_check_alarms_no_data_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _mock_session_with_recent([])
    monkeypatch.setattr(alarm_service, "AsyncSessionLocal", lambda: session)
    result = await check_alarms(1)
    assert result == []


@pytest.mark.asyncio
async def test_check_alarms_triggers_power_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """白天辐照但功率为 0 → critical 告警 'power_zero_when_sunny'."""
    rec = SimpleNamespace(
        inverter_id="INV001",
        active_power_kw=0.0,
        irradiance_w_m2=600.0,
        fault_code=0,
    )
    session = _mock_session_with_recent([rec])
    monkeypatch.setattr(alarm_service, "AsyncSessionLocal", lambda: session)

    created: list = []

    async def fake_create(
        session, station_id, inverter_id, level, title, desc, code, tenant_id=None
    ):
        alarm = SimpleNamespace(
            station_id=station_id,
            inverter_id=inverter_id,
            level=level,
            title=title,
            description=desc,
            code=code,
        )
        created.append(alarm)
        return alarm

    monkeypatch.setattr(alarm_service, "_create_or_update_alarm", fake_create)

    await check_alarms(1)
    codes = [a.code for a in created]
    assert "power_zero_when_sunny" in codes
    assert any(a.level == "critical" for a in created)


@pytest.mark.asyncio
async def test_check_alarms_triggers_fault_code(monkeypatch: pytest.MonkeyPatch) -> None:
    rec = SimpleNamespace(
        inverter_id="INV002",
        active_power_kw=100.0,
        irradiance_w_m2=600.0,
        fault_code=42,
    )
    session = _mock_session_with_recent([rec])
    monkeypatch.setattr(alarm_service, "AsyncSessionLocal", lambda: session)

    created: list = []

    async def fake_create(
        session, station_id, inverter_id, level, title, desc, code, tenant_id=None
    ):
        a = SimpleNamespace(code=code, level=level)
        created.append(a)
        return a

    monkeypatch.setattr(alarm_service, "_create_or_update_alarm", fake_create)

    await check_alarms(1)
    assert "fault_code" in [a.code for a in created]


@pytest.mark.asyncio
async def test_check_alarms_triggers_low_pr(monkeypatch: pytest.MonkeyPatch) -> None:
    """辐照 > 500 且 PR < 50% → warning."""
    rec = SimpleNamespace(
        inverter_id="INV003",
        # theoretical = 800/1000*1000 = 800, pr = 100/800 = 0.125 < 0.5
        active_power_kw=100.0,
        irradiance_w_m2=800.0,
        fault_code=0,
    )
    session = _mock_session_with_recent([rec])
    monkeypatch.setattr(alarm_service, "AsyncSessionLocal", lambda: session)

    created: list = []

    async def fake_create(
        session, station_id, inverter_id, level, title, desc, code, tenant_id=None
    ):
        a = SimpleNamespace(code=code, level=level)
        created.append(a)
        return a

    monkeypatch.setattr(alarm_service, "_create_or_update_alarm", fake_create)

    await check_alarms(1)
    codes = [a.code for a in created]
    # 应该至少有 PR 偏低告警；若有 power_zero（功率 100 不触发）；fault=0 不触发
    assert any("pr" in c.lower() or "PR" in c for c in codes) or any(
        a.level == "warning" for a in created
    )


@pytest.mark.asyncio
async def test_check_alarms_clean_state_no_alerts(monkeypatch: pytest.MonkeyPatch) -> None:
    """正常工况（白天高功率、无故障码、PR 健康）→ 不产生告警."""
    rec = SimpleNamespace(
        inverter_id="INV004",
        # theoretical=800, pr=700/800=0.875 > 0.5
        active_power_kw=700.0,
        irradiance_w_m2=800.0,
        fault_code=0,
    )
    session = _mock_session_with_recent([rec])
    monkeypatch.setattr(alarm_service, "AsyncSessionLocal", lambda: session)

    created: list = []

    async def fake_create(
        session, station_id, inverter_id, level, title, desc, code, tenant_id=None
    ):
        created.append(SimpleNamespace(code=code, level=level))
        return SimpleNamespace(code=code, level=level)

    monkeypatch.setattr(alarm_service, "_create_or_update_alarm", fake_create)

    result = await check_alarms(1)
    assert result == []
