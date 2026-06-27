"""采集器本地缓存队列（断点续传）."""

import json
import logging
import os
from datetime import datetime
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

DEFAULT_QUEUE_DB = os.path.join(os.path.dirname(__file__), "..", "..", "collector_queue.db")


class LocalQueue:
    """基于 SQLite 的本地队列，用于网络中断时暂存采集数据."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_QUEUE_DB

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS collector_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """
            )
            await db.commit()

    async def enqueue(self, payload: dict[str, Any]) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO collector_queue (payload, created_at) VALUES (?, ?)",
                (json.dumps(payload, ensure_ascii=False), datetime.now().isoformat()),
            )
            await db.commit()

    async def dequeue_all(self) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, payload FROM collector_queue ORDER BY id ASC"
            ) as cursor:
                rows = await cursor.fetchall()

            payloads = []
            ids = []
            for row in rows:
                try:
                    payloads.append(json.loads(row[1]))
                    ids.append(row[0])
                except json.JSONDecodeError:
                    logger.warning(f"队列中存在非法 JSON，id={row[0]}")

            if ids:
                placeholders = ",".join("?" * len(ids))
                await db.execute(f"DELETE FROM collector_queue WHERE id IN ({placeholders})", ids)
                await db.commit()

            return payloads

    async def size(self) -> int:
        async with (
            aiosqlite.connect(self.db_path) as db,
            db.execute("SELECT COUNT(*) FROM collector_queue") as cursor,
        ):
            row = await cursor.fetchone()
            return row[0] if row else 0
