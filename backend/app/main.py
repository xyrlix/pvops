"""FastAPI 应用入口."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.device import Device, Inverter, StringUnit
from app.models.station import Station
from app.models.user import User
from app.repositories import get_repository

settings = get_settings()


async def _seed_initial_data() -> None:
    """初始化默认管理员和演示电站."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        # 默认管理员
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                full_name="系统管理员",
                email="admin@pvops.local",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                status="active",
            )
            session.add(admin)

        # 演示电站
        result = await session.execute(select(Station).where(Station.code == "DEMO-001"))
        station = result.scalar_one_or_none()
        if not station:
            station = Station(
                name="光伏电站 A",
                code="DEMO-001",
                capacity_kw=1000.0,
                location="浙江省杭州市",
                longitude=120.16,
                latitude=30.25,
                contact_name="张工",
                contact_phone="13800138000",
                status="active",
            )
            session.add(station)
            await session.flush()

        # 演示设备资产：气象站、关口表、逆变器、组串
        if station:
            existing = await session.execute(
                select(Device).where(Device.station_id == station.id)
            )
            if not existing.scalars().first():
                # 气象站
                weather_device = Device(
                    station_id=station.id,
                    device_type="weather_station",
                    device_code="WS001",
                    name="气象站 001",
                    vendor="Campbell",
                    model="CR1000",
                    protocol="simulator",
                    config={"interval": 60},
                    status="active",
                    sort_order=0,
                )
                session.add(weather_device)
                await session.flush()

                # 关口表
                meter_device = Device(
                    station_id=station.id,
                    device_type="meter",
                    device_code="METER001",
                    name="关口表 001",
                    vendor="华立",
                    model="DTZY",
                    protocol="simulator",
                    config={"interval": 60},
                    status="active",
                    sort_order=1,
                )
                session.add(meter_device)

                for i in range(1, 4):
                    inv_code = f"INV00{i}"
                    inv_device = Device(
                        station_id=station.id,
                        device_type="inverter",
                        device_code=inv_code,
                        name=f"逆变器 {i}",
                        vendor="阳光电源",
                        model="SG350HX",
                        protocol="simulator",
                        config={"interval": 5, "capacity_kw": 350.0},
                        status="active",
                        sort_order=10 + i,
                    )
                    session.add(inv_device)
                    await session.flush()

                    inv = Inverter(
                        station_id=station.id,
                        device_id=inv_device.id,
                        inverter_id=inv_code,
                        name=f"逆变器 {i}",
                        capacity_kw=350.0,
                        status="active",
                    )
                    session.add(inv)

                    for s in range(1, 5):
                        string_code = f"{inv_code}-S{s:02d}"
                        string_device = Device(
                            station_id=station.id,
                            parent_id=inv_device.id,
                            device_type="string",
                            device_code=string_code,
                            name=f"组串 {s}",
                            protocol="simulator",
                            config={"capacity_kw": 80.0},
                            status="active",
                            sort_order=100 + i * 10 + s,
                        )
                        session.add(string_device)
                        await session.flush()

                        session.add(
                            StringUnit(
                                station_id=station.id,
                                device_id=string_device.id,
                                inverter_id=inv_code,
                                string_id=string_code,
                                name=f"组串 {s}",
                                capacity_kw=80.0,
                            )
                        )

        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    # 启动时创建数据库表
    from app.core.database import Base, AsyncSessionLocal, engine
    from app.models.alarm import Alarm  # noqa: F401
    from app.models.device import Device, Inverter, StringUnit  # noqa: F401
    from app.models.knowledge import KnowledgeChunk, KnowledgeDoc  # noqa: F401
    from app.models.report import DiagnosisReport, Report  # noqa: F401
    from app.models.timeseries import InverterData, WeatherData  # noqa: F401
    from app.models.user import User  # noqa: F401
    from app.models.work_order import WorkOrder  # noqa: F401
    from app.models.station import Station  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 初始化演示数据
    await _seed_initial_data()

    # 启动时初始化时序仓库（SQLite / TDengine）
    repo = get_repository()
    await repo.init()
    yield
    # 关闭时清理资源
    await repo.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="光伏运维智能体 API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(api_router, prefix="/api/v1")

# 静态前端文件
# 本地开发：frontend/dist；Docker：backend/static
possible_static_dirs = [
    Path(__file__).parent.parent.parent / "frontend" / "dist",
    Path(__file__).parent.parent / "static",
]
static_dir = next((d for d in possible_static_dirs if d.exists()), None)

if static_dir and static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """SPA fallback."""
    if not request.url.path.startswith("/api") and static_dir:
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
    from fastapi.responses import JSONResponse

    return JSONResponse({"detail": "Not found"}, status_code=404)
