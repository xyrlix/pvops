"""work_order_service 单元测试.

聚焦不依赖 DB 的纯逻辑：feedback 追加、solution 拼接。
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.work_order_service import (
    create_work_order,
    update_work_order_status,
)

# ─── helpers ────────────────────────────────────────────────


def _mock_session_for_wo(work_order: Any | None) -> Any:
    """构造返回特定 WorkOrder 的 AsyncSession mock."""
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = work_order
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


# ─── create_work_order ──────────────────────────────────────


@pytest.mark.asyncio
async def test_create_work_order_persists_with_defaults() -> None:
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    wo = await create_work_order(
        session,
        title="INV001 异常巡检",
        description="检查逆变器通信",
        priority="high",
        assignee="张三",
        station_id=1,
        alarm_id=42,
    )

    # 字段断言
    assert wo.title == "INV001 异常巡检"
    assert wo.priority == "high"
    assert wo.assignee == "张三"
    assert wo.station_id == 1
    assert wo.alarm_id == 42
    assert wo.status == "pending"  # 默认状态
    assert wo.feedback == []

    # session 行为断言
    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_work_order_minimal_args() -> None:
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    wo = await create_work_order(session, title="简单工单")
    assert wo.title == "简单工单"
    assert wo.priority == "medium"  # 默认
    assert wo.description is None
    assert wo.status == "pending"


# ─── update_work_order_status ───────────────────────────────


@pytest.mark.asyncio
async def test_update_status_returns_none_for_missing_work_order() -> None:
    session = _mock_session_for_wo(None)
    result = await update_work_order_status(session, 999, status="completed")
    assert result is None


@pytest.mark.asyncio
async def test_update_status_appends_feedback_entry() -> None:
    wo = SimpleNamespace(
        id=1,
        title="test",
        description="原描述",
        status="pending",
        feedback=[],
        updated_at=None,
    )
    session = _mock_session_for_wo(wo)

    result = await update_work_order_status(session, 1, status="in_progress", comment="开始处理")
    assert result is wo
    assert wo.status == "in_progress"
    assert len(wo.feedback) == 1
    entry = wo.feedback[0]
    assert entry["status"] == "in_progress"
    assert entry["comment"] == "开始处理"
    assert entry["solution"] == ""
    assert "created_at" in entry
    assert isinstance(wo.updated_at, datetime)


@pytest.mark.asyncio
async def test_update_status_appends_solution_to_description() -> None:
    """solution 非空时追加到 description."""
    wo = SimpleNamespace(
        id=2,
        title="t",
        description="原始描述",
        status="pending",
        feedback=[
            {
                "status": "pending",
                "comment": "已派单",
                "solution": "",
                "created_at": datetime.now().isoformat(),
            }
        ],
        updated_at=None,
    )
    session = _mock_session_for_wo(wo)

    await update_work_order_status(
        session, 2, status="completed", comment="已修复", solution="重启逆变器并更换保险丝"
    )
    assert "原始描述" in wo.description
    assert "【解决方案】" in wo.description
    assert "重启逆变器并更换保险丝" in wo.description
    assert len(wo.feedback) == 2


@pytest.mark.asyncio
async def test_update_status_solution_does_not_duplicate_marker() -> None:
    """多次更新 solution 不重复追加 【解决方案】 段."""
    wo = SimpleNamespace(
        id=3,
        title="t",
        description="desc",
        status="pending",
        feedback=[],
        updated_at=None,
    )
    session = _mock_session_for_wo(wo)

    await update_work_order_status(session, 3, status="in_progress", solution="step1")
    await update_work_order_status(session, 3, status="completed", solution="step2")
    # After 2 updates with solution, there should be 2 markers
    assert wo.description.count("【解决方案】") == 2
    assert "step1" in wo.description
    assert "step2" in wo.description
