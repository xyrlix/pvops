"""协议适配器工厂测试."""

import pytest

from app.protocols.factory import create_adapter
from app.protocols.simulator import SimulatorAdapter


def test_create_simulator_adapter():
    """创建模拟器适配器."""
    adapter = create_adapter("simulator", "INV001", {"capacity_kw": 100})
    assert isinstance(adapter, SimulatorAdapter)
    assert adapter.capacity_kw == 100


def test_create_adapter_protocol_case_insensitive():
    """协议名大小写不敏感."""
    adapter = create_adapter("SIMULATOR", "WS001", {})
    assert isinstance(adapter, SimulatorAdapter)


def test_create_unsupported_protocol_raises():
    """不支持的协议应抛出异常."""
    with pytest.raises(ValueError):
        create_adapter("unknown_protocol", "DEV001", {})
