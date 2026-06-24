"""创建演示数据."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.core.security import get_password_hash
from app.models.station import Station
from app.models.user import User


async def create_demo_station() -> None:
    """创建演示电站."""
    async with AsyncSessionLocal() as session:
        # 检查是否已存在
        from sqlalchemy import select

        result = await session.execute(select(Station).where(Station.code == "DEMO001"))
        existing = result.scalar_one_or_none()
        if existing:
            print("演示电站已存在")
            return

        station = Station(
            name="演示电站",
            code="DEMO001",
            capacity_kw=1000.0,
            location="上海市浦东新区",
            longitude=121.47,
            latitude=31.23,
            contact_name="张三",
            contact_phone="13800138000",
            status="active",
        )
        session.add(station)
        await session.commit()
        print(f"演示电站创建成功，ID: {station.id}")


async def init_db() -> None:
    """初始化数据库表."""
    from app.core.database import Base
    from app.models.alarm import Alarm  # noqa: F401
    from app.models.report import DiagnosisReport  # noqa: F401
    from app.models.timeseries import InverterData, WeatherData  # noqa: F401
    from app.models.user import User  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表初始化完成")


async def create_admin_user() -> None:
    """创建管理员用户."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.username == "admin"))
        existing = result.scalar_one_or_none()
        if existing:
            print("管理员用户已存在")
            return

        user = User(
            username="admin",
            email="admin@pvops.example",
            full_name="系统管理员",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            status="active",
        )
        session.add(user)
        await session.commit()
        print("管理员用户创建成功：admin / admin123")


async def main() -> None:
    await init_db()
    await create_demo_station()
    await create_admin_user()


if __name__ == "__main__":
    asyncio.run(main())
