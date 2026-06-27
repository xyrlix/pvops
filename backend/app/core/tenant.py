"""租户上下文与查询过滤.

- ``get_current_tenant()``:  从 JWT / X-Tenant-Id 头推断当前用户的 tenant_id
- ``TenantContext`` dataclass: 在 request scope 内传递
- ``scoped_query()``: 给定 model class + TenantContext，注入 .where(Model.tenant_id == ...)
- ``TenantMiddleware``: ASGI 中间件，把 X-Tenant-Id 头塞进 request.state

迁移策略：
- 旧数据 tenant_id 为 NULL（混合租户或预迁移）
- 默认 tenant_id = 1（demo 租户）
- superadmin (User.role == 'superadmin' 且 tenant_id IS NULL) 可跨租户
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import Column
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token

DEFAULT_TENANT_ID = 1  # demo 租户


@dataclass
class TenantContext:
    """当前请求的租户上下文."""

    tenant_id: int
    is_superadmin: bool = False

    def __post_init__(self) -> None:
        if self.tenant_id is None:
            raise ValueError("tenant_id must not be None")


async def get_current_tenant(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TenantContext:
    """从 JWT 提取 tenant_id + role；缺失时回退默认租户.

    注意：不要在生产中跳过此 Depends；``TenantContext`` 是
    ``scoped_query()`` 必需的入参。
    """
    # 优先从 Authorization 头解析
    auth = request.headers.get("Authorization", "")
    tenant_id: Optional[int] = None
    role = "viewer"
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = decode_token(token) or {}
        sub = payload.get("sub")  # username
        tid = payload.get("tenant_id")
        if isinstance(tid, int):
            tenant_id = tid
        role = payload.get("role", "viewer")

    # 其次从 X-Tenant-Id 头解析（gateway 转发场景）
    if tenant_id is None:
        header_tid = request.headers.get("X-Tenant-Id")
        if header_tid and header_tid.isdigit():
            tenant_id = int(header_tid)

    # 最终兜底
    if tenant_id is None:
        tenant_id = DEFAULT_TENANT_ID

    return TenantContext(
        tenant_id=tenant_id,
        is_superadmin=(role == "superadmin"),
    )


def scoped_query(
    query: Any,
    model: type,
    tenant: TenantContext,
) -> Any:
    """给 query 加上 tenant 过滤.

    若 model 没有 tenant_id 列（如 User / Tenant 自身），直接透传 query。
    superadmin 默认仍受 tenant 约束（避免误操作）；如需跨租户，
    请使用 ``scoped_query_unrestricted()``。
    """
    tenant_col: Optional[Column] = getattr(model, "tenant_id", None)
    if tenant_col is None:
        return query
    return query.where(tenant_col == tenant.tenant_id)


def scoped_query_unrestricted(query: Any) -> Any:
    """跨租户查询（仅 superadmin 内部使用）."""
    return query


__all__ = [
    "DEFAULT_TENANT_ID",
    "TenantContext",
    "get_current_tenant",
    "scoped_query",
    "scoped_query_unrestricted",
]