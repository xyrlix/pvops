"""创建/补齐演示数据。

执行：
    PYTHONPATH=backend:. python3 scripts/seed_demo.py

幂等：重复执行不会产生重复行。
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import Base, engine
from app.core.seed import seed_initial_data

# 显式 import 模型以确保 metadata 注册
from app.models.alarm import Alarm  # noqa: F401
from app.models.device import Device, Inverter, StringUnit  # noqa: F401
from app.models.knowledge import KnowledgeChunk, KnowledgeDoc  # noqa: F401
from app.models.report import DiagnosisReport, Report  # noqa: F401
from app.models.timeseries import InverterData, MeterData, WeatherData  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.work_order import WorkOrder  # noqa: F401
from app.models.station import Station  # noqa: F401


async def init_db() -> None:
    """初始化业务库表（不创建时序/向量库 schema）。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表初始化完成")


async def main() -> None:
    await init_db()
    await seed_initial_data()
    print("演示数据 seeding 完成")


if __name__ == "__main__":
    asyncio.run(main())
