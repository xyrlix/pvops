"""Add tenant_id to business tables + create tenants table.

Revision ID: 003
Revises: 002
Create Date: 2026-06-27

策略：
- 新增 tenants 表
- 给 users / stations / alarms / work_orders 加 tenant_id 列（nullable）
- 默认值通过回填到 DEFAULT_TENANT_ID = 1
- 给 tenant_id 列加索引
- 业务层通过 app.core.tenant.scoped_query() 显式过滤
"""

import sqlalchemy as sa

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


DEFAULT_TENANT_ID = 1


def upgrade() -> None:
    # 1. tenants 表
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_tenants_code"), "tenants", ["code"], unique=True)

    # 2. seed 默认 demo 租户
    op.execute(
        f"INSERT INTO tenants (id, code, name, status) "
        f"VALUES ({DEFAULT_TENANT_ID}, 'default', 'Demo Tenant', 'active') "
        f"ON CONFLICT (id) DO NOTHING"
    )

    # 3. 给业务表加 tenant_id 列 + 索引
    tables_with_tenant = [
        ("users", True),  # NOT NULL 没法给历史行赋值，所以保持 nullable
        ("stations", True),
        ("alarms", True),
        ("work_orders", True),
    ]
    for tbl, _nullable in tables_with_tenant:
        op.add_column(
            tbl,
            sa.Column("tenant_id", sa.Integer(), nullable=True),
        )
        # 回填所有 NULL 为默认 tenant
        op.execute(f"UPDATE {tbl} SET tenant_id = {DEFAULT_TENANT_ID} WHERE tenant_id IS NULL")
        # 加索引（注意：必须在数据回填后）
        op.create_index(op.f(f"ix_{tbl}_tenant_id"), tbl, ["tenant_id"], unique=False)


def downgrade() -> None:
    for tbl in ("users", "stations", "alarms", "work_orders"):
        op.drop_index(op.f(f"ix_{tbl}_tenant_id"), table_name=tbl)
        op.drop_column(tbl, "tenant_id")
    op.drop_index(op.f("ix_tenants_code"), table_name="tenants")
    op.drop_table("tenants")
