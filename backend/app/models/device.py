"""设备资产模型."""

from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class Device(Base):
    """统一设备资产表.

    覆盖逆变器、气象站、关口表、汇流箱、组串等设备类型，
    通过 `device_type` 区分，config 字段存储协议与寄存器配置。
    """

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    device_type = Column(
        String(32),
        nullable=False,
        comment="设备类型: inverter, weather_station, meter, combiner_box, string",
    )
    device_code = Column(String(64), nullable=False, comment="设备编号")
    name = Column(String(100), nullable=False, comment="设备名称")
    vendor = Column(String(100), nullable=True, comment="厂商")
    model = Column(String(100), nullable=True, comment="型号")
    sn = Column(String(100), nullable=True, comment="序列号")
    protocol = Column(
        String(32),
        nullable=True,
        comment="协议: simulator, modbus_tcp, modbus_rtu, huawei_cloud, ...",
    )
    config = Column(JSON, nullable=True, comment="协议配置/寄存器映射/连接参数")
    status = Column(String(20), default="active", comment="状态")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(String(50), server_default=func.now())


class Inverter(Base):
    """逆变器资产（保留，用于容量与运行指标计算）."""

    __tablename__ = "inverters"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    inverter_id = Column(String(64), nullable=False, comment="设备编号")
    name = Column(String(100), nullable=False, comment="设备名称")
    capacity_kw = Column(Float, nullable=False, comment="额定容量(kW)")
    status = Column(String(20), default="active", comment="状态")
    created_at = Column(String(50), server_default=func.now())


class StringUnit(Base):
    """组串资产."""

    __tablename__ = "string_units"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    inverter_id = Column(String(64), nullable=False, index=True)
    string_id = Column(String(64), nullable=False, comment="组串编号")
    name = Column(String(100), nullable=False, comment="组串名称")
    capacity_kw = Column(Float, nullable=False, comment="额定容量(kW)")
    status = Column(String(20), default="active", comment="状态")
