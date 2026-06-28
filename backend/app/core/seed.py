"""演示数据 seeding.

仅在本地演示或测试环境调用；生产部署应设置 `SEED_DEMO_ON_STARTUP=false`。
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.device import Device, Inverter, StringUnit
from app.models.knowledge import KnowledgeDoc
from app.models.station import Station
from app.models.user import User
from app.services.knowledge_service import _chunk_text

logger = logging.getLogger(__name__)

DEMO_STATION_CODE = "DEMO-001"
DEMO_ADMIN_USERNAME = "admin"


async def seed_initial_data() -> None:
    """初始化默认管理员和演示电站 + 演示设备资产 + 种子知识库文档."""
    async with AsyncSessionLocal() as session:
        await _ensure_admin(session)
        station_id = await _ensure_demo_station(session)
        if station_id is not None:
            await _ensure_demo_devices(session, station_id)
        await session.commit()

    # 知识库种子文档：首次启动时导入
    await _seed_knowledge_docs()


async def _seed_knowledge_docs() -> None:
    """导入 seed/ 目录下的预置知识文档（跳过已导入的）。"""
    from sqlalchemy import select

    logger.info("检查知识库种子文档…")
    async with AsyncSessionLocal() as session:
        count = (
            await session.execute(select(func.count()).select_from(KnowledgeDoc))
        ).scalar() or 0
    if count > 0:
        logger.info("知识库已有 %d 篇文档，跳过种子导入", count)
        return

    seed_dir = Path(__file__).parent.parent.parent / "seed"
    if not seed_dir.exists():
        logger.warning("seed 目录不存在: %s", seed_dir)
        return

    files = sorted(f for f in seed_dir.iterdir() if f.suffix in (".md", ".txt", ".pdf", ".docx"))
    if not files:
        return

    from app.services import knowledge_service

    for fp in files:
        try:
            content = fp.read_bytes()
            doc = await knowledge_service.save_upload(fp.name, content)
            text = (
                (await asyncio.to_thread(fp.read_text, encoding="utf-8"))
                if fp.suffix in (".md", ".txt")
                else ""
            )
            if not text:
                text = (
                    (await asyncio.to_thread(fp.read_text, encoding="utf-8"))
                    if doc.content_text
                    else ""
                )
            if text:
                await knowledge_service.create_chunks(int(doc.id), text)
                async with AsyncSessionLocal() as session:
                    db_doc = await session.get(KnowledgeDoc, doc.id)
                    if db_doc:
                        db_doc.content_text = text
                        db_doc.chunk_count = len(_chunk_text(text))
                        await session.commit()
                logger.info("  导入知识库: %s (%d 块)", fp.name, db_doc.chunk_count)
        except Exception as exc:
            logger.error("  导入失败: %s — %s", fp.name, exc)


async def _ensure_admin(session) -> None:
    result = await session.execute(select(User).where(User.username == DEMO_ADMIN_USERNAME))
    if result.scalar_one_or_none():
        return
    admin = User(
        username=DEMO_ADMIN_USERNAME,
        full_name="系统管理员",
        email="admin@pvops.local",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        status="active",
    )
    session.add(admin)
    logger.info("已创建默认管理员 %s", DEMO_ADMIN_USERNAME)


async def _ensure_demo_station(session) -> int | None:
    result = await session.execute(select(Station).where(Station.code == DEMO_STATION_CODE))
    station = result.scalar_one_or_none()
    if station is None:
        station = Station(
            name="光伏电站 A",
            code=DEMO_STATION_CODE,
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
        logger.info("已创建演示电站 %s id=%s", DEMO_STATION_CODE, station.id)
    return station.id


async def _ensure_demo_devices(session, station_id: int) -> None:
    existing = await session.execute(select(Device).where(Device.station_id == station_id))
    if existing.scalars().first():
        return

    weather = Device(
        station_id=station_id,
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
    session.add(weather)
    await session.flush()

    meter = Device(
        station_id=station_id,
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
    session.add(meter)

    for i in range(1, 4):
        inv_code = f"INV00{i}"
        inv_device = Device(
            station_id=station_id,
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

        session.add(
            Inverter(
                station_id=station_id,
                device_id=inv_device.id,
                inverter_id=inv_code,
                name=f"逆变器 {i}",
                capacity_kw=350.0,
                status="active",
            )
        )

        for s in range(1, 5):
            string_code = f"{inv_code}-S{s:02d}"
            string_device = Device(
                station_id=station_id,
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
                    station_id=station_id,
                    device_id=string_device.id,
                    inverter_id=inv_code,
                    string_id=string_code,
                    name=f"组串 {s}",
                    capacity_kw=80.0,
                )
            )
    logger.info("已创建演示设备资产（3 台逆变器 + 12 组组串 + 气象/关口表）")
