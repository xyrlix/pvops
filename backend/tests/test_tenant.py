"""tenant 模块单测.

聚焦 TenantContext 解析 + scoped_query 过滤逻辑（不依赖 DB）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.core.tenant import (
    DEFAULT_TENANT_ID,
    TenantContext,
    scoped_query,
    scoped_query_unrestricted,
)


# ─── TenantContext dataclass ────────────────────────────────


def test_tenant_context_requires_tenant_id() -> None:
    with pytest.raises(ValueError):
        TenantContext(tenant_id=None)


def test_tenant_context_basic() -> None:
    tc = TenantContext(tenant_id=42, is_superadmin=False)
    assert tc.tenant_id == 42
    assert tc.is_superadmin is False


def test_tenant_context_superadmin_flag() -> None:
    tc = TenantContext(tenant_id=1, is_superadmin=True)
    assert tc.is_superadmin is True


# ─── scoped_query ───────────────────────────────────────────


class _HasTenantCol:
    tenant_id = "tenant_id_col"


class _NoTenantCol:
    pass


class _FakeQuery:
    """记录被调用的 .where(...) 入参."""

    def __init__(self) -> None:
        self.where_calls: List[Any] = []

    def where(self, expr: Any) -> "_FakeQuery":
        self.where_calls.append(expr)
        return self


def test_scoped_query_adds_tenant_filter_when_model_has_column() -> None:
    tc = TenantContext(tenant_id=7)
    q = _FakeQuery()
    out = scoped_query(q, _HasTenantCol, tc)
    assert out is q
    assert len(q.where_calls) == 1


def test_scoped_query_no_op_when_model_lacks_column() -> None:
    tc = TenantContext(tenant_id=7)
    q = _FakeQuery()
    out = scoped_query(q, _NoTenantCol, tc)
    assert out is q
    assert q.where_calls == []


def test_scoped_query_unrestricted_returns_query_unchanged() -> None:
    q = _FakeQuery()
    out = scoped_query_unrestricted(q)
    assert out is q
    assert q.where_calls == []


# ─── get_current_tenant Depends ──────────────────────────────


@pytest.mark.asyncio
async def test_get_current_tenant_from_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    """JWT 含 tenant_id 时优先使用."""
    from app.core import tenant as tenant_mod

    def fake_decode(token: str) -> Optional[Dict[str, Any]]:
        return {"sub": "alice", "role": "operator", "tenant_id": 99}

    monkeypatch.setattr(tenant_mod, "decode_token", fake_decode)

    request = MagicMock()
    request.headers = {"Authorization": "Bearer fake.jwt.token"}

    db = AsyncMock()
    tc = await tenant_mod.get_current_tenant(request=request, db=db)
    assert tc.tenant_id == 99
    assert tc.is_superadmin is False


@pytest.mark.asyncio
async def test_get_current_tenant_superadmin_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import tenant as tenant_mod

    def fake_decode(token: str) -> Optional[Dict[str, Any]]:
        return {"sub": "root", "role": "superadmin", "tenant_id": 1}

    monkeypatch.setattr(tenant_mod, "decode_token", fake_decode)

    request = MagicMock()
    request.headers = {"Authorization": "Bearer x"}
    db = AsyncMock()
    tc = await tenant_mod.get_current_tenant(request=request, db=db)
    assert tc.is_superadmin is True


@pytest.mark.asyncio
async def test_get_current_tenant_fallback_to_header(monkeypatch: pytest.MonkeyPatch) -> None:
    """无 JWT 时从 X-Tenant-Id 头读取."""
    from app.core import tenant as tenant_mod

    monkeypatch.setattr(tenant_mod, "decode_token", lambda t: None)

    request = MagicMock()
    request.headers = {"X-Tenant-Id": "42"}
    db = AsyncMock()
    tc = await tenant_mod.get_current_tenant(request=request, db=db)
    assert tc.tenant_id == 42


@pytest.mark.asyncio
async def test_get_current_tenant_default_when_no_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """无 JWT / 无 header → 默认租户."""
    from app.core import tenant as tenant_mod

    monkeypatch.setattr(tenant_mod, "decode_token", lambda t: None)

    request = MagicMock()
    request.headers = {}
    db = AsyncMock()
    tc = await tenant_mod.get_current_tenant(request=request, db=db)
    assert tc.tenant_id == DEFAULT_TENANT_ID


# ─── 模型 TenantScopedMixin 集成 ────────────────────────────


def test_alarm_model_has_tenant_id_column() -> None:
    from app.models.alarm import Alarm

    assert hasattr(Alarm, "tenant_id")


def test_station_model_has_tenant_id_column() -> None:
    from app.models.station import Station

    assert hasattr(Station, "tenant_id")


def test_work_order_model_has_tenant_id_column() -> None:
    from app.models.work_order import WorkOrder

    assert hasattr(WorkOrder, "tenant_id")


def test_user_model_has_tenant_id_column() -> None:
    from app.models.user import User

    assert hasattr(User, "tenant_id")


def test_tenant_model_exists() -> None:
    from app.models.tenant import Tenant

    assert Tenant.__tablename__ == "tenants"