"""diagnosis_service 单元测试.

覆盖 DiagnosisResult 构造、6 个检测规则、综合健康度评分、汇总逻辑。
内部 `_check_*` 函数通过显式 records 列表单测，无需数据库。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from app.services.diagnosis_service import (
    DiagnosisResult,
    _check_communication_gap,
    _check_fault_codes,
    _check_high_module_temperature,
    _check_irradiance_power_mismatch,
    _check_night_power_consumption,
    _check_power_generation,
    _check_pr_performance,
    _check_repeated_fault,
    _check_sudden_power_drop,
    _check_voltage_current,
    _check_voltage_imbalance,
    _check_weather_data_gap,
)

# ─── helpers ────────────────────────────────────────────────


def _rec(
    *,
    timestamp: datetime | None = None,
    active_power_kw: float = 0.0,
    irradiance_w_m2: float = 0.0,
    dc_voltage_v: float = 0.0,
    dc_current_a: float = 0.0,
    fault_code: int = 0,
    inverter_id: str = "INV001",
    station_id: int = 1,
) -> Any:
    """构造简化版 InverterData 占位（避免 SQLAlchemy ORM 初始化）."""
    return SimpleNamespace(
        timestamp=timestamp or datetime.now(),
        active_power_kw=active_power_kw,
        irradiance_w_m2=irradiance_w_m2,
        dc_voltage_v=dc_voltage_v,
        dc_current_a=dc_current_a,
        fault_code=fault_code,
        inverter_id=inverter_id,
        station_id=station_id,
    )


def _result() -> DiagnosisResult:
    return DiagnosisResult(station_id=1, station_name="测试电站", diagnosis_time=datetime.now())


# ─── DiagnosisResult ─────────────────────────────────────────


def test_diagnosis_result_to_dict_shape() -> None:
    r = _result()
    r.overall_health = 87.5
    r.summary = "ok"
    r.findings = [{"title": "f1"}]
    r.suggestions = ["s1"]
    out = r.to_dict()
    assert out["station_id"] == 1
    assert out["station_name"] == "测试电站"
    assert out["overall_health"] == 87.5
    assert out["summary"] == "ok"
    assert out["findings"] == [{"title": "f1"}]
    assert out["suggestions"] == ["s1"]
    assert isinstance(out["diagnosis_time"], str)


# ─── _check_power_generation ─────────────────────────────────


@pytest.mark.asyncio
async def test_check_power_generation_triggers_on_daytime_zero_power() -> None:
    """白天高辐照但功率为 0 → critical 告警."""
    r = _result()
    records = [
        _rec(
            timestamp=datetime.now(),
            active_power_kw=0.0,
            irradiance_w_m2=600.0,
            dc_voltage_v=620.0,
            dc_current_a=12.0,
        ),
    ]
    await _check_power_generation(r, "INV001", records)
    assert len(r.findings) == 1
    f = r.findings[0]
    assert f["severity"] == "critical"
    assert f["category"] == "发电异常"
    assert "白天无功率" in f["title"]
    assert len(f["evidence"]) >= 3
    assert len(f["suggestions"]) == 3


@pytest.mark.asyncio
async def test_check_power_generation_ignores_nighttime() -> None:
    """夜间（辐照度低）零功率不应触发告警."""
    r = _result()
    records = [_rec(active_power_kw=0.0, irradiance_w_m2=50.0)]
    await _check_power_generation(r, "INV001", records)
    assert r.findings == []


@pytest.mark.asyncio
async def test_check_power_generation_ignores_normal_operation() -> None:
    """白天有功率 → 不触发."""
    r = _result()
    records = [_rec(active_power_kw=200.0, irradiance_w_m2=600.0)]
    await _check_power_generation(r, "INV001", records)
    assert r.findings == []


# ─── _check_pr_performance ──────────────────────────────────


@pytest.mark.asyncio
async def test_check_pr_performance_warns_when_pr_below_threshold() -> None:
    """>=3 条记录 PR<70% → warning."""
    r = _result()
    now = datetime.now()
    records = [
        _rec(
            timestamp=now - timedelta(minutes=i * 10),
            active_power_kw=400.0,  # theoretical=irradiance_w_m2/1000*1000=900
            irradiance_w_m2=900.0,
        )
        for i in range(5)
    ]
    await _check_pr_performance(r, "INV001", records)
    assert len(r.findings) == 1
    assert r.findings[0]["severity"] == "warning"
    assert "PR 偏低" in r.findings[0]["title"]


@pytest.mark.asyncio
async def test_check_pr_performance_skips_when_irradiance_low() -> None:
    """无高辐照记录 → 直接返回."""
    r = _result()
    records = [_rec(active_power_kw=0.0, irradiance_w_m2=100.0)]
    await _check_pr_performance(r, "INV001", records)
    assert r.findings == []


@pytest.mark.asyncio
async def test_check_pr_performance_no_warning_for_few_low_pr_records() -> None:
    """少于 3 条低 PR 记录 → 不告警."""
    r = _result()
    records = [
        _rec(active_power_kw=400.0, irradiance_w_m2=900.0),
        _rec(active_power_kw=500.0, irradiance_w_m2=900.0),
    ]
    await _check_pr_performance(r, "INV001", records)
    assert r.findings == []


# ─── _check_communication_gap ───────────────────────────────


@pytest.mark.asyncio
async def test_check_communication_gap_detects_4h_silence() -> None:
    """通讯中断 > 4h → warning."""
    r = _result()
    now = datetime.now()
    records = [
        _rec(timestamp=now),
        _rec(timestamp=now - timedelta(hours=2)),
        _rec(timestamp=now - timedelta(hours=5)),  # 与上一条间隔 3h → 累计 5h
    ]
    await _check_communication_gap(r, "INV001", records)
    assert len(r.findings) == 1
    assert r.findings[0]["severity"] == "warning"


@pytest.mark.asyncio
async def test_check_communication_gap_fine_with_frequent_data() -> None:
    """1h 内密集采集 → 不触发."""
    r = _result()
    now = datetime.now()
    records = [_rec(timestamp=now - timedelta(minutes=i * 10)) for i in range(10)]
    await _check_communication_gap(r, "INV001", records)
    assert r.findings == []


# ─── _check_fault_codes ─────────────────────────────────────


@pytest.mark.asyncio
async def test_check_fault_codes_detects_critical_fault() -> None:
    """fault_code > 0 → critical."""
    r = _result()
    records = [_rec(fault_code=12)]
    await _check_fault_codes(r, "INV001", records)
    assert len(r.findings) == 1
    assert r.findings[0]["severity"] == "critical"
    assert "fault_code=12" in r.findings[0]["evidence"][0] or "12" in str(r.findings[0])


@pytest.mark.asyncio
async def test_check_fault_codes_no_alert_when_clean() -> None:
    """fault_code=0 → 不触发."""
    r = _result()
    records = [_rec(fault_code=0)]
    await _check_fault_codes(r, "INV001", records)
    assert r.findings == []


# ─── _check_voltage_current ─────────────────────────────────


@pytest.mark.asyncio
async def test_check_voltage_current_detects_zero_voltage() -> None:
    """白天辐照充足但直流电压为 0 → critical."""
    r = _result()
    records = [_rec(irradiance_w_m2=600.0, dc_voltage_v=0.0, dc_current_a=10.0)]
    await _check_voltage_current(r, "INV001", records)
    assert any(f["severity"] == "critical" for f in r.findings)


@pytest.mark.asyncio
async def test_check_voltage_current_detects_string_imbalance() -> None:
    """电流差异 > 50% → warning."""
    r = _result()
    records = [
        _rec(dc_current_a=10.0, dc_voltage_v=620.0),
        _rec(dc_current_a=2.0, dc_voltage_v=600.0),  # 显著低于第一条
    ]
    await _check_voltage_current(r, "INV001", records)
    assert any("不平衡" in f["title"] for f in r.findings)


@pytest.mark.asyncio
async def test_check_voltage_current_no_alert_balanced() -> None:
    """电流相近 → 不触发."""
    r = _result()
    records = [
        _rec(dc_current_a=10.0, dc_voltage_v=620.0),
        _rec(dc_current_a=10.5, dc_voltage_v=625.0),
    ]
    await _check_voltage_current(r, "INV001", records)
    assert r.findings == []


# ─── 综合健康度评分 ────────────────────────────────────────


@pytest.mark.asyncio
async def test_combined_health_score_penalizes_critical() -> None:
    """critical 数影响 overall_health."""
    # 触发 critical（白天 0 功率）+ warning（PR 偏低）
    r = _result()
    now = datetime.now()
    records = [
        _rec(
            timestamp=now - timedelta(minutes=i),
            active_power_kw=0.0,
            irradiance_w_m2=600.0,
            dc_voltage_v=620.0,
            dc_current_a=10.0,
        )
        for i in range(2)
    ]
    await _check_power_generation(r, "INV001", records)
    # 再触发 PR warning
    pr_records = [
        _rec(timestamp=now - timedelta(minutes=i * 5), active_power_kw=400.0, irradiance_w_m2=900.0)
        for i in range(5)
    ]
    await _check_pr_performance(r, "INV001", pr_records)
    # 综合评分：100 - critical*25 - warning*10
    critical = sum(1 for f in r.findings if f["severity"] == "critical")
    warning = sum(1 for f in r.findings if f["severity"] == "warning")
    expected = max(0, 100 - critical * 25 - warning * 10)
    assert r.overall_health == expected
    assert r.overall_health < 100


# ─── 新增规则 6-13 ──────────────────────────────────────


@pytest.mark.asyncio
async def test_check_high_module_temperature_triggers() -> None:
    """高辐照 + 高温 → warning."""
    r = _result()
    now = datetime.now()
    records = [_rec(timestamp=now, irradiance_w_m2=1000.0, ambient_temp_c=40.0) for _ in range(3)]
    await _check_high_module_temperature(r, "INV001", records)
    assert len(r.findings) >= 1
    assert "温度异常" in r.findings[0]["category"]


@pytest.mark.asyncio
async def test_check_high_module_temperature_ok() -> None:
    """正常温度 → 无告警."""
    r = _result()
    records = [_rec(irradiance_w_m2=200.0, ambient_temp_c=15.0)]
    await _check_high_module_temperature(r, "INV001", records)
    assert r.findings == []


@pytest.mark.asyncio
async def test_night_power_triggers() -> None:
    """夜间有功率 ≥3 次 → warning."""
    r = _result()
    records = [_rec(irradiance_w_m2=0.0, active_power_kw=1.0) for _ in range(5)]
    await _check_night_power_consumption(r, "INV001", records)
    assert len(r.findings) >= 1


@pytest.mark.asyncio
async def test_night_power_ok() -> None:
    r = _result()
    records = [_rec(irradiance_w_m2=0.0, active_power_kw=0.0) for _ in range(3)]
    await _check_night_power_consumption(r, "INV001", records)
    assert r.findings == []


@pytest.mark.asyncio
async def test_sudden_power_drop_triggers() -> None:
    r = _result()
    now = datetime.now()
    records = [
        _rec(timestamp=now - timedelta(minutes=5), active_power_kw=200.0, irradiance_w_m2=600.0),
        _rec(timestamp=now, active_power_kw=30.0, irradiance_w_m2=600.0),
    ]
    await _check_sudden_power_drop(r, "INV001", records)
    assert len(r.findings) >= 1
    assert r.findings[0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_sudden_power_drop_no_false_positive() -> None:
    r = _result()
    now = datetime.now()
    records = [
        _rec(timestamp=now - timedelta(minutes=5), active_power_kw=200.0),
        _rec(timestamp=now, active_power_kw=180.0),
    ]
    await _check_sudden_power_drop(r, "INV001", records)
    assert r.findings == []


@pytest.mark.asyncio
async def test_repeated_fault_triggers() -> None:
    r = _result()
    records = [_rec(fault_code=7) for _ in range(5)]
    await _check_repeated_fault(r, "INV001", records)
    assert len(r.findings) >= 1


@pytest.mark.asyncio
async def test_barely_repeated_fault_no_alert() -> None:
    """相同故障码只出现 1 次 → 不触发."""
    r = _result()
    records = [_rec(fault_code=7)]
    await _check_repeated_fault(r, "INV001", records)
    assert r.findings == []


@pytest.mark.asyncio
async def test_power_mismatch_triggers() -> None:
    r = _result()
    now = datetime.now()
    # theoretical=800/1000*1000=800, pr=100/800=0.125 < 0.5
    records = [
        _rec(
            timestamp=now - timedelta(minutes=i * 10), active_power_kw=100.0, irradiance_w_m2=800.0
        )
        for i in range(3)
    ]
    await _check_irradiance_power_mismatch(r, "INV001", records)
    assert len(r.findings) >= 1


@pytest.mark.asyncio
async def test_weather_data_gap_triggers() -> None:
    r = _result()
    records = [_rec(irradiance_w_m2=0.0, ambient_temp_c=-20.0) for _ in range(10)]
    await _check_weather_data_gap(r, "INV001", records)
    assert len(r.findings) >= 1


@pytest.mark.asyncio
async def test_voltage_imbalance_triggers() -> None:
    r = _result()
    records = [
        _rec(dc_voltage_v=600.0, dc_current_a=10.0),
        _rec(dc_voltage_v=680.0, dc_current_a=10.0),
    ]
    await _check_voltage_imbalance(r, "INV001", records)
    assert len(r.findings) >= 1


@pytest.mark.asyncio
async def test_voltage_imbalance_no_alert() -> None:
    r = _result()
    records = [
        _rec(dc_voltage_v=620.0, dc_current_a=10.0),
        _rec(dc_voltage_v=630.0, dc_current_a=10.0),
    ]
    await _check_voltage_imbalance(r, "INV001", records)
    assert r.findings == []
