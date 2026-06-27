"""标准寄存器映射."""

from app.protocols.base import CollectorPoint

# 逆变器常用 Modbus 寄存器映射（示例，需按实际设备手册调整）
INVERTER_REGISTER_MAP: list[CollectorPoint] = [
    CollectorPoint("active_power_kw", "holding", 3001, "uint", 0.001, "kW"),
    CollectorPoint("dc_voltage_v", "holding", 3011, "uint", 0.1, "V"),
    CollectorPoint("dc_current_a", "holding", 3012, "uint", 0.01, "A"),
    CollectorPoint("daily_energy_kwh", "holding", 3101, "uint", 0.01, "kWh"),
    CollectorPoint("total_energy_kwh", "holding", 3102, "uint", 0.1, "kWh"),
    CollectorPoint("inverter_status", "holding", 3201, "int", 1.0, ""),
    CollectorPoint("fault_code", "holding", 3202, "int", 1.0, ""),
]

# 气象站寄存器映射
WEATHER_REGISTER_MAP: list[CollectorPoint] = [
    CollectorPoint("irradiance_w_m2", "holding", 4001, "uint", 1.0, "W/m²"),
    CollectorPoint("ambient_temp_c", "holding", 4002, "int", 0.1, "°C"),
    CollectorPoint("module_temp_c", "holding", 4003, "int", 0.1, "°C"),
    CollectorPoint("wind_speed_m_s", "holding", 4004, "uint", 0.1, "m/s"),
]

# 关口表寄存器映射
METER_REGISTER_MAP: list[CollectorPoint] = [
    CollectorPoint("active_power_kw", "holding", 5001, "uint", 0.001, "kW"),
    CollectorPoint("total_energy_kwh", "holding", 5002, "uint", 0.01, "kWh"),
]

DEVICE_REGISTER_MAPS: dict[str, list[CollectorPoint]] = {
    "inverter": INVERTER_REGISTER_MAP,
    "weather_station": WEATHER_REGISTER_MAP,
    "meter": METER_REGISTER_MAP,
}
