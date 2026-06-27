"""Initial migration — all business tables.

Revision ID: 001
Revises:
Create Date: 2026-06-26

注意：本迁移涵盖 PVOps 启动所需的全部业务库表结构。
后续 schema 变更请通过 `alembic revision --autogenerate` 增量生成新迁移，
不要再修改本文件。
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 用户
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("full_name", sa.String(length=100), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="viewer"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # 电站
    op.create_table(
        "stations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("capacity_kw", sa.Float(), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("contact_name", sa.String(length=50), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_stations_code"), "stations", ["code"], unique=True)
    op.create_index(op.f("ix_stations_id"), "stations", ["id"], unique=False)

    # 设备（统一设备资产表）
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("device_type", sa.String(length=32), nullable=False),
        sa.Column("device_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("vendor", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("sn", sa.String(length=100), nullable=True),
        sa.Column("protocol", sa.String(length=32), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True, server_default="active"),
        sa.Column("sort_order", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("created_at", sa.String(length=50), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["parent_id"], ["devices.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_devices_id"), "devices", ["id"], unique=False)
    op.create_index(op.f("ix_devices_station_id"), "devices", ["station_id"], unique=False)
    op.create_index(op.f("ix_devices_parent_id"), "devices", ["parent_id"], unique=False)

    # 逆变器资产
    op.create_table(
        "inverters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("inverter_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("capacity_kw", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True, server_default="active"),
        sa.Column("created_at", sa.String(length=50), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inverters_id"), "inverters", ["id"], unique=False)
    op.create_index(op.f("ix_inverters_station_id"), "inverters", ["station_id"], unique=False)
    op.create_index(op.f("ix_inverters_device_id"), "inverters", ["device_id"], unique=False)

    # 组串资产
    op.create_table(
        "string_units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("inverter_id", sa.String(length=64), nullable=False),
        sa.Column("string_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("capacity_kw", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True, server_default="active"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 时序：逆变器
    op.create_table(
        "inverter_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("inverter_id", sa.String(length=64), nullable=False),
        sa.Column("active_power_kw", sa.Float(), server_default="0.0"),
        sa.Column("dc_voltage_v", sa.Float(), server_default="0.0"),
        sa.Column("dc_current_a", sa.Float(), server_default="0.0"),
        sa.Column("daily_energy_kwh", sa.Float(), server_default="0.0"),
        sa.Column("total_energy_kwh", sa.Float(), server_default="0.0"),
        sa.Column("inverter_status", sa.Integer(), server_default="0"),
        sa.Column("fault_code", sa.Integer(), server_default="0"),
        sa.Column("irradiance_w_m2", sa.Float(), server_default="0.0"),
        sa.Column("ambient_temp_c", sa.Float(), server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inverter_data_id"), "inverter_data", ["id"], unique=False)
    op.create_index(
        op.f("ix_inverter_data_timestamp"), "inverter_data", ["timestamp"], unique=False
    )
    op.create_index(
        op.f("ix_inverter_data_station_id"), "inverter_data", ["station_id"], unique=False
    )
    op.create_index(
        op.f("ix_inverter_data_inverter_id"), "inverter_data", ["inverter_id"], unique=False
    )
    op.create_index("ix_inverter_data_station_time", "inverter_data", ["station_id", "timestamp"])

    # 时序：气象
    op.create_table(
        "weather_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=False, server_default="WS001"),
        sa.Column("irradiance_w_m2", sa.Float(), server_default="0.0"),
        sa.Column("ambient_temp_c", sa.Float(), server_default="0.0"),
        sa.Column("module_temp_c", sa.Float(), server_default="0.0"),
        sa.Column("wind_speed_m_s", sa.Float(), server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_weather_data_id"), "weather_data", ["id"], unique=False)
    op.create_index(op.f("ix_weather_data_timestamp"), "weather_data", ["timestamp"], unique=False)
    op.create_index(
        op.f("ix_weather_data_station_id"), "weather_data", ["station_id"], unique=False
    )

    # 时序：关口表
    op.create_table(
        "meter_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=False),
        sa.Column("active_power_kw", sa.Float(), server_default="0.0"),
        sa.Column("reactive_power_kvar", sa.Float(), server_default="0.0"),
        sa.Column("forward_active_energy_kwh", sa.Float(), server_default="0.0"),
        sa.Column("reverse_active_energy_kwh", sa.Float(), server_default="0.0"),
        sa.Column("voltage_v", sa.Float(), server_default="0.0"),
        sa.Column("current_a", sa.Float(), server_default="0.0"),
        sa.Column("power_factor", sa.Float(), server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meter_data_id"), "meter_data", ["id"], unique=False)
    op.create_index(op.f("ix_meter_data_timestamp"), "meter_data", ["timestamp"], unique=False)
    op.create_index(op.f("ix_meter_data_station_id"), "meter_data", ["station_id"], unique=False)
    op.create_index("ix_meter_data_station_time", "meter_data", ["station_id", "timestamp"])

    # 告警
    op.create_table(
        "alarms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=True),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("acknowledged_by", sa.Integer(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", sa.Integer(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["closed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["acknowledged_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alarms_id"), "alarms", ["id"], unique=False)
    op.create_index(op.f("ix_alarms_station_id"), "alarms", ["station_id"], unique=False)

    # 工单
    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=True),
        sa.Column("alarm_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("assignee", sa.String(length=100), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("solution", sa.Text(), nullable=True),
        sa.Column("feedback_comment", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["alarm_id"], ["alarms.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_work_orders_id"), "work_orders", ["id"], unique=False)
    op.create_index(op.f("ix_work_orders_station_id"), "work_orders", ["station_id"], unique=False)
    op.create_index(op.f("ix_work_orders_alarm_id"), "work_orders", ["alarm_id"], unique=False)

    # 报告
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=True),
        sa.Column("report_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_id"), "reports", ["id"], unique=False)
    op.create_index(op.f("ix_reports_station_id"), "reports", ["station_id"], unique=False)

    # 诊断报告
    op.create_table(
        "diagnosis_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("station_name", sa.String(length=100), nullable=True),
        sa.Column("diagnosis_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("overall_health", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("findings", sa.JSON(), nullable=True),
        sa.Column("suggestions", sa.JSON(), nullable=True),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_diagnosis_reports_id"), "diagnosis_reports", ["id"], unique=False)
    op.create_index(
        op.f("ix_diagnosis_reports_station_id"), "diagnosis_reports", ["station_id"], unique=False
    )

    op.create_table(
        "diagnosis_feedbacks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.String(length=16), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["report_id"], ["diagnosis_reports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_diagnosis_feedbacks_id"), "diagnosis_feedbacks", ["id"], unique=False)
    op.create_index(
        op.f("ix_diagnosis_feedbacks_report_id"), "diagnosis_feedbacks", ["report_id"], unique=False
    )

    # 知识库
    op.create_table(
        "knowledge_docs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_docs_id"), "knowledge_docs", ["id"], unique=False)

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("vector_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["doc_id"], ["knowledge_docs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_chunks_id"), "knowledge_chunks", ["id"], unique=False)
    op.create_index(
        op.f("ix_knowledge_chunks_doc_id"), "knowledge_chunks", ["doc_id"], unique=False
    )
    op.create_index(
        op.f("ix_knowledge_chunks_vector_id"), "knowledge_chunks", ["vector_id"], unique=False
    )


def downgrade() -> None:
    # 反向顺序：先删外键依赖表
    for tbl in [
        "knowledge_chunks",
        "knowledge_docs",
        "diagnosis_feedbacks",
        "diagnosis_reports",
        "reports",
        "work_orders",
        "alarms",
        "meter_data",
        "weather_data",
        "inverter_data",
        "string_units",
        "inverters",
        "devices",
        "stations",
        "users",
    ]:
        op.drop_table(tbl)
