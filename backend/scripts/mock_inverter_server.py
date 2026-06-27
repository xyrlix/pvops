"""本地 Modbus TCP 模拟器（无硬件时也能跑通 SUN2000 / Sungrow 协议）.

模拟一台华为 SUN2000 逆变器在 127.0.0.1:5020 上响应 Modbus TCP 请求。
对应 register 地址参考 ``app/protocols/huawei_sun2000.py``。

启动方式::

    PYTHONPATH=backend:. python3 backend/scripts/mock_inverter_server.py \\
        --vendor huawei_sun2000 --host 127.0.0.1 --port 5020

运行模式：
- ``--vendor huawei_sun2000``：按华为 SUN2000 register map 响应
- ``--vendor sungrow_sg``：按阳光 SG register map 响应

数据特征：基于 datetime + device_code 生成确定性伪随机曲线，模拟白天
功率曲线 + 早晚余弦过渡 + 偶尔故障码。
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)


# ─── 通用：确定性伪随机 ─────────────────────────────────────


def _seed(value: str) -> random.Random:
    h = sum(ord(c) for c in value) % 1000003
    return random.Random(h)


# ─── 华为 SUN2000 模拟数据 ─────────────────────────────────


def _huawei_payload(device_code: str) -> dict[int, int]:
    """生成符合 SUN2000 register map 的瞬时遥测."""
    rng = _seed(f"{device_code}-{datetime.now().strftime('%Y%m%d%H%M')}")
    hour = datetime.now().hour + datetime.now().minute / 60
    if 6 <= hour <= 18:
        peak = ((hour - 6) / 12) * 8000  # 8 kW 峰值
        active_power_w = max(0, peak + rng.uniform(-500, 500))
    else:
        active_power_w = max(0, rng.uniform(-50, 50))
    pv_voltage = 620 + rng.uniform(-20, 20) if active_power_w > 0 else 0
    pv_current = active_power_w / max(pv_voltage, 1) if pv_voltage > 0 else 0
    daily_wh = int((3000 + rng.uniform(0, 500)) * 100)  # Wh
    total_kwh = int(1_000_000 + rng.uniform(0, 50000))
    internal_temp = 35 + rng.uniform(-5, 15)
    fault_code = 0 if rng.random() > 0.02 else rng.randint(1, 5)
    inverter_status = 2 if active_power_w > 0 else 0

    # 按 SUN2000 register map 索引
    return {
        32064: int(active_power_w),
        32065: int(rng.uniform(-200, 200)),
        32066: int(rng.uniform(900, 1000)),  # power factor * 1000
        32067: int(rng.uniform(4990, 5010)),  # grid freq * 100
        32069: daily_wh,
        32071: total_kwh,
        32072: int(internal_temp * 10),
        32080: int(pv_voltage * 10),
        32082: int(pv_current * 100),
        32084: int(pv_voltage * 10 * 0.95),
        32086: int(pv_current * 100 * 0.92),
        32106: inverter_status,
        32114: fault_code,
    }


# ─── 阳光 SG 模拟数据 ──────────────────────────────────────


def _sungrow_payload(device_code: str) -> dict[int, int]:
    """按阳光 SG register map（input register，地址更小）."""
    rng = _seed(f"{device_code}-{datetime.now().strftime('%Y%m%d%H%M')}")
    hour = datetime.now().hour + datetime.now().minute / 60
    if 6 <= hour <= 18:
        peak = ((hour - 6) / 12) * 5000
        active_power_w = max(0, peak + rng.uniform(-300, 300))
    else:
        active_power_w = max(0, rng.uniform(-30, 30))
    pv_voltage = 580 + rng.uniform(-15, 15) if active_power_w > 0 else 0
    pv_current = active_power_w / max(pv_voltage, 1) if pv_voltage > 0 else 0
    daily_wh = int((2500 + rng.uniform(0, 400)) * 100)
    total_kwh = int(800_000 + rng.uniform(0, 40000))
    return {
        2: daily_wh,
        4: total_kwh,
        12: int(pv_voltage * 10),
        14: int(pv_current * 10),
        20: int(active_power_w),
        22: int(rng.uniform(-150, 150)),
        26: int(rng.uniform(4995, 5005)),
        28: int(33 + rng.uniform(-5, 10)),
        44: 2 if active_power_w > 0 else 0,
        66: 0 if rng.random() > 0.02 else rng.randint(1, 3),
    }


# ─── Modbus TCP Server（基于 pymodbus）────────────────────────


async def run_server(vendor: str, host: str, port: int, device_code: str) -> None:
    """启动本地 Modbus TCP server，模拟一台指定厂商的逆变器."""
    try:
        from pymodbus.datastore import (
            ModbusSequentialDataBlock,
            ModbusServerContext,
            ModbusSlaveContext,
        )
        from pymodbus.server import StartAsyncTcpServer
    except ImportError as exc:
        raise SystemExit(f"pymodbus 未安装: {exc}") from exc

    # 注册大范围数据块（覆盖 0x0000 - 0xFFFF）
    data_block = ModbusSequentialDataBlock(0, [0] * 0x10000)
    context = ModbusServerContext(
        slaves={1: ModbusSlaveContext(hr=data_block, ir=data_block)}, single=False
    )

    async def update_loop() -> None:
        """每 2s 刷新一次输入寄存器."""
        while True:
            try:
                if vendor == "huawei_sun2000":
                    payload = _huawei_payload(device_code)
                else:
                    payload = _sungrow_payload(device_code)
                # pymodbus 3.x: 通过 store 拿 input register
                slave = context[1]
                for addr, val in payload.items():
                    slave.setValues(4, addr, [val & 0xFFFF])  # 4 = INPUT
                logger.debug("Mock %s refresh: %d registers", vendor, len(payload))
            except Exception as exc:
                logger.warning("mock inverter refresh failed: %s", exc)
            await asyncio.sleep(2)

    # 启动后台刷新
    asyncio.create_task(update_loop())

    logger.info(
        "Mock inverter server (%s) listening on %s:%d (device_code=%s)",
        vendor,
        host,
        port,
        device_code,
    )
    await StartAsyncTcpServer(context=context, address=(host, port))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vendor", choices=["huawei_sun2000", "sungrow_sg"], default="huawei_sun2000"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5020)
    parser.add_argument("--device-code", default="INV-SUN2000-DEMO")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    asyncio.run(run_server(args.vendor, args.host, args.port, args.device_code))


if __name__ == "__main__":
    main()
