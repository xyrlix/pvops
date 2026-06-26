"""Schema 迁移封装.

应用启动时调用 `run_migrations()`：
- 优先 `alembic upgrade head`（生产部署应走这条）
- alembic 不可用时 fallback 到 `create_all`（仅用于极简本地演示）

任何 schema 变更都应通过 `alembic revision --autogenerate` 生成迁移。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_ALEMBIC_AVAILABLE: Optional[bool] = None


def _has_alembic() -> bool:
    """检查 alembic 是否真的可用（含 command 子模块）。

    仅 `import alembic` 不够：项目根的 alembic/ 目录会让 Python
    把它当作 namespace package，导致 `import alembic` 成功但
    `from alembic import command` 失败。这里直接探测 command 子模块。
    """
    global _ALEMBIC_AVAILABLE
    if _ALEMBIC_AVAILABLE is not None:
        return _ALEMBIC_AVAILABLE
    try:
        import alembic.command  # noqa: F401

        _ALEMBIC_AVAILABLE = True
    except (ImportError, AttributeError):
        _ALEMBIC_AVAILABLE = False
    return _ALEMBIC_AVAILABLE


async def _alembic_upgrade_async() -> None:
    """在线程中执行 alembic upgrade head."""
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    backend_dir = Path(__file__).resolve().parent.parent.parent
    ini_path = backend_dir / "alembic.ini"
    if not ini_path.exists():
        raise FileNotFoundError(f"alembic.ini not found at {ini_path}")

    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    cfg.set_main_option("sqlalchemy.url", get_settings().database_url)

    logger.info("运行 alembic upgrade head ...")
    await asyncio.to_thread(command.upgrade, cfg, "head")
    logger.info("数据库迁移完成")


async def _create_all_async() -> None:
    """alembic 不可用时的 fallback：直接 create_all."""
    logger.warning("alembic 未安装，使用 create_all fallback（仅推荐开发环境）")
    from app.core.database import Base, engine

    # 显式 import 所有模型以注册到 Base.metadata
    from app.models.alarm import Alarm  # noqa: F401
    from app.models.device import Device, Inverter, StringUnit  # noqa: F401
    from app.models.knowledge import KnowledgeChunk, KnowledgeDoc  # noqa: F401
    from app.models.report import DiagnosisFeedback, DiagnosisReport, Report  # noqa: F401
    from app.models.station import Station  # noqa: F401
    from app.models.timeseries import InverterData, MeterData, WeatherData  # noqa: F401
    from app.models.user import User  # noqa: F401
    from app.models.work_order import WorkOrder  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def run_migrations() -> None:
    """异步执行 schema 升级."""
    if _has_alembic():
        await _alembic_upgrade_async()
        return
    await _create_all_async()
