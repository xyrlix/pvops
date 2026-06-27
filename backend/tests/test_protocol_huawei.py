"""华为 SUN2000 / 阳光 SG 协议适配器单测.

重点验证：
- 寄存器解码（scale + data_type）
- 字段映射（active_power_kw / dc_voltage_v / dc_current_a ...）
- 工厂注册（huawei_sun2000 / sungrow_sg 协议）
- 错误恢复（连接失败、读取失败）
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.protocols import create_adapter
from app.protocols.huawei_sun2000 import (
    HUAWEI_SUN2000_REGISTER_MAP,
    HuaweiSUN2000Adapter,
    _decode_huawei_register,
)
from app.protocols.sungrow_sg import (
    SUNGROW_SG_REGISTER_MAP,
    SungrowSGAdapter,
)


# ─── _decode_huawei_register ──────────────────────────────


def test_decode_int_zero() -> None:
    from app.protocols.base import CollectorPoint

    p = CollectorPoint("x", "holding", 0, "int", 1.0, "")
    assert _decode_huawei_register(0, p) == 0


def test_decode_uint_with_scale() -> None:
    from app.protocols.base import CollectorPoint

    p = CollectorPoint("voltage", "holding", 0, "uint", 0.1, "V")
    # raw=6200, scale=0.1 → 620.0
    assert _decode_huawei_register(6200, p) == 620.0


def test_decode_int_preserves_negative() -> None:
    """负数（如反向功率）保留符号."""
    from app.protocols.base import CollectorPoint

    p = CollectorPoint("power", "holding", 0, "int", 1.0, "W")
    result = _decode_huawei_register(-100, p)
    # 应为 -100（W 直接 × 1.0）
    assert result == -100


# ─── 寄存器表完整性 ──────────────────────────────────────


def test_huawei_register_map_required_fields() -> None:
    """register map 必须覆盖 InverterData 核心字段."""
    names = {p.name for p in HUAWEI_SUN2000_REGISTER_MAP}
    required = {"active_power_w", "dc_voltage_v", "dc_current_a",
                "daily_energy_wh", "fault_code", "inverter_status"}
    assert required.issubset(names), f"缺字段: {required - names}"


def test_sungrow_register_map_required_fields() -> None:
    names = {p.name for p in SUNGROW_SG_REGISTER_MAP}
    required = {"active_power_w", "dc_voltage_v", "dc_current_a",
                "daily_energy_wh", "fault_code", "inverter_status"}
    assert required.issubset(names)


# ─── 字段映射：active_power_kw 从 raw W 转为 kW ────────────


def _mk_client_with_registers(registers: dict[int, int]):
    """构造一个 mock AsyncModbusTcpClient, read_input_registers 返回给定值."""
    client = MagicMock()

    async def fake_read(address: int, count: int, slave: int):
        # 返回前两个 register（高位 + 低位）
        lo = registers.get(address, 0)
        hi = registers.get(address + 1, 0)
        rr = MagicMock()
        rr.isError.return_value = False
        rr.registers = [lo, hi]
        return rr

    client.read_input_registers = fake_read
    return client


@pytest.mark.asyncio
async def test_huawei_collect_once_unit_conversion() -> None:
    """active_power_w (W) → active_power_kw (kW)."""
    adapter = HuaweiSUN2000Adapter("INV-TEST", {"host": "127.0.0.1", "port": 5020})
    adapter._client = _mk_client_with_registers({
        32064: 5000,  # 5 kW
        32065: 0,
        32066: 990,   # power factor 0.99
        32067: 5000,  # 50.00 Hz
        32069: 12000, # daily energy
        32071: 1_500_000,
        32072: 350,   # 35.0°C
        32080: 6200,  # 620.0 V
        32082: 800,   # 8.00 A
        32084: 0, 32086: 0,
        32106: 2,     # on-grid
        32114: 0,
    })

    data = await adapter.collect_once()
    assert data["active_power_kw"] == 5.0
    assert data["reactive_power_kvar"] == 0.0
    assert data["power_factor"] == 990
    assert data["dc_voltage_v"] == 620.0
    assert abs(data["dc_current_a"] - 8.0) < 0.01
    assert data["daily_energy_kwh"] == 12000
    assert data["total_energy_kwh"] == 1_500_000
    assert data["inverter_temp_c"] == 35.0
    assert data["inverter_status"] == "并网运行"
    assert data["fault_code"] == 0


@pytest.mark.asyncio
async def test_huawei_status_label_mapping() -> None:
    """不同设备状态码 → 中文标签."""
    adapter = HuaweiSUN2000Adapter("INV-TEST")
    adapter._client = _mk_client_with_registers({32106: 0})  # standby
    data = await adapter.collect_once()
    assert data["inverter_status"] == "待机"

    adapter._client = _mk_client_with_registers({32106: 4})  # 降额
    data = await adapter.collect_once()
    assert data["inverter_status"] == "降额并网"


@pytest.mark.asyncio
async def test_huawei_collect_once_handles_read_errors() -> None:
    """读错误时 skip 点位，不抛异常."""
    adapter = HuaweiSUN2000Adapter("INV-TEST", {"host": "127.0.0.1", "port": 5020})
    client = MagicMock()

    async def fake_read(address: int, count: int, slave: int):
        rr = MagicMock()
        rr.isError.return_value = True  # 模拟协议错误
        rr.registers = []
        return rr

    client.read_input_registers = fake_read
    adapter._client = client

    data = await adapter.collect_once()
    # 即使所有点位都失败，也应返回结构化字段（值为 0）
    assert data["active_power_kw"] == 0
    assert data["inverter_status"] == "未知"  # default label
    assert data["fault_code"] == 0


# ─── sungrow ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sungrow_collect_once_unit_conversion() -> None:
    adapter = SungrowSGAdapter("INV-TEST")
    adapter._client = _mk_client_with_registers({
        12: 6200,  # 620.0 V
        14: 80,    # 8.0 A
        20: 3000,  # 3 kW
        22: 0,
        26: 5000,
        28: 35,
        44: 2,     # on-grid
        66: 0,
        2: 12000,  # 120 kWh daily
        4: 800_000,
    })

    data = await adapter.collect_once()
    assert data["active_power_kw"] == 3.0
    assert data["dc_voltage_v"] == 620.0
    assert data["dc_current_a"] == 8.0
    assert data["daily_energy_kwh"] == 12000
    assert data["total_energy_kwh"] == 800_000
    assert data["inverter_temp_c"] == 35
    assert data["inverter_status"] == "并网运行"
    assert data["fault_code"] == 0


# ─── factory 注册 ──────────────────────────────────────


def test_factory_creates_huawei_sun2000() -> None:
    adapter = create_adapter("huawei_sun2000", "INV001", {"host": "127.0.0.1"})
    assert isinstance(adapter, HuaweiSUN2000Adapter)
    assert adapter.host == "127.0.0.1"


def test_factory_creates_sungrow_sg() -> None:
    adapter = create_adapter("sungrow_sg", "INV002", {"host": "192.168.1.10"})
    assert isinstance(adapter, SungrowSGAdapter)
    assert adapter.host == "192.168.1.10"


def test_factory_unknown_protocol_raises() -> None:
    with pytest.raises(ValueError, match="不支持的协议"):
        create_adapter("nonexistent_protocol", "INV")


def test_factory_case_insensitive() -> None:
    adapter = create_adapter("Huawei_SUN2000", "INV")
    assert isinstance(adapter, HuaweiSUN2000Adapter)


def test_factory_default_falls_back_to_simulator() -> None:
    adapter = create_adapter("", "INV")
    from app.protocols.simulator import SimulatorAdapter
    assert isinstance(adapter, SimulatorAdapter)


def test_factory_simulator_still_works() -> None:
    """向后兼容：simulator 协议不变."""
    adapter = create_adapter("simulator", "INV")
    from app.protocols.simulator import SimulatorAdapter
    assert isinstance(adapter, SimulatorAdapter)


# ─── connect/disconnect 生命周期 ────────────────────────────


@pytest.mark.asyncio
async def test_huawei_connect_missing_pymodbus_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """pymodbus 缺失时构造期就 raise，不会延迟到 read."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pymodbus.client":
            raise ImportError("simulated missing pymodbus")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="pymodbus 未安装"):
        HuaweiSUN2000Adapter("INV", {})


@pytest.mark.asyncio
async def test_huawei_disconnect_safe_when_not_connected() -> None:
    adapter = HuaweiSUN2000Adapter("INV")
    # 重复 disconnect 不报错
    await adapter.disconnect()
    await adapter.disconnect()


@pytest.mark.asyncio
async def test_huawei_read_points_requires_connect() -> None:
    adapter = HuaweiSUN2000Adapter("INV")
    with pytest.raises(RuntimeError, match="未连接"):
        await adapter.read_points([])