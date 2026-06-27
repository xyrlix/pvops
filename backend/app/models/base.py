"""模型公共 mixin."""

from __future__ import annotations

from sqlalchemy import Column, Integer


class TenantScopedMixin:
    """为模型添加 tenant_id 列 + 索引.

    nullable=True 以便从无 tenant 的历史数据平滑迁移；
    上线后所有业务路由都应通过 ``get_current_tenant()`` 注入 tenant_id。
    """

    tenant_id = Column(Integer, nullable=True, index=True)


__all__ = ["TenantScopedMixin"]