"""逆变器数据模拟器."""

import argparse
import json
import math
import random
import time
from datetime import datetime, timedelta


class InverterSimulator:
    """逆变器数据模拟器."""

    def __init__(
        self,
        station_id: int,
        inverter_id: str,
        capacity_kw: float,
        base_latitude: float = 31.23,
        base_longitude: float = 121.47,
    ):
        self.station_id = station_id
        self.inverter_id = inverter_id
        self.capacity_kw = capacity_kw
        self.base_latitude = base_latitude
        self.base_longitude = base_longitude
        self.total_energy_kwh = random.uniform(100000, 500000)
        self.daily_energy_kwh = 0.0
        self.last_day = None

    def _simulate_irradiance(self, dt: datetime) -> float:
        """模拟辐照度."""
        hour = dt.hour + dt.minute / 60
        
        if hour < 6 or hour > 18:
            return 0.0
        
        # 正午最高，正弦曲线
        peak = math.sin(((hour - 6) / 12) * math.pi)
        
        # 添加云层随机波动
        cloud_factor = random.uniform(0.7, 1.0)
        
        # 最高辐照度约 1000 W/m²
        return max(0, peak * 1000 * cloud_factor)

    def _reset_daily_energy(self, dt: datetime) -> None:
        """跨天重置日发电量."""
        current_day = dt.date()
        if self.last_day != current_day:
            self.daily_energy_kwh = 0.0
            self.last_day = current_day

    def generate(self, dt: datetime | None = None) -> dict:
        """生成一条逆变器数据."""
        if dt is None:
            dt = datetime.now()
        
        self._reset_daily_energy(dt)
        
        irradiance = self._simulate_irradiance(dt)
        
        # 功率 = 辐照度/1000 * 容量 * 效率
        efficiency = 0.85 + random.gauss(0, 0.02)
        active_power_kw = min(
            self.capacity_kw,
            irradiance / 1000 * self.capacity_kw * efficiency,
        )
        
        # 直流侧参数
        dc_voltage_v = 0.0
        dc_current_a = 0.0
        
        if active_power_kw > 0:
            dc_voltage_v = 620 + random.gauss(0, 5)
            dc_current_a = active_power_kw * 1000 / dc_voltage_v
        
        # 累加日发电量和总发电量
        energy_increment = active_power_kw / 60  # 假设 1 分钟一条数据
        self.daily_energy_kwh += energy_increment
        self.total_energy_kwh += energy_increment
        
        # 状态：白天有功率为运行，否则待机
        inverter_status = 1 if active_power_kw > 1 else 0
        fault_code = 0
        
        return {
            "timestamp": dt.isoformat(),
            "station_id": self.station_id,
            "inverter_id": self.inverter_id,
            "active_power_kw": round(active_power_kw, 2),
            "dc_voltage_v": round(dc_voltage_v, 2),
            "dc_current_a": round(dc_current_a, 2),
            "daily_energy_kwh": round(self.daily_energy_kwh, 2),
            "total_energy_kwh": round(self.total_energy_kwh, 2),
            "inverter_status": inverter_status,
            "fault_code": fault_code,
            "irradiance_w_m2": round(irradiance, 2),
            "ambient_temp_c": round(25 + random.gauss(0, 3), 1),
        }

    def inject_fault(self, fault_type: str, start: datetime, end: datetime) -> None:
        """注入故障（预留）."""
        # TODO: 在指定时间段内降低发电功率或设置故障码
        pass


class WeatherSimulator:
    """气象站数据模拟器."""

    def __init__(self, station_id: int, device_id: str = "WS001"):
        self.station_id = station_id
        self.device_id = device_id

    def generate(self, dt: datetime | None = None) -> dict:
        """生成气象数据."""
        if dt is None:
            dt = datetime.now()
        
        hour = dt.hour + dt.minute / 60
        
        irradiance = 0.0
        if 6 <= hour <= 18:
            peak = math.sin(((hour - 6) / 12) * math.pi)
            irradiance = peak * 1000 * random.uniform(0.7, 1.0)
        
        return {
            "timestamp": dt.isoformat(),
            "station_id": self.station_id,
            "device_id": self.device_id,
            "irradiance_w_m2": round(irradiance, 2),
            "ambient_temp_c": round(25 + random.gauss(0, 3), 1),
            "module_temp_c": round(30 + random.gauss(0, 5), 1),
            "wind_speed_m_s": round(max(0, random.gauss(3, 1.5)), 1),
        }


def generate_historical_data(
    station_id: int,
    inverter_id: str,
    capacity_kw: float,
    days: int = 30,
    interval_minutes: int = 5,
) -> list[dict]:
    """生成历史数据."""
    simulator = InverterSimulator(station_id, inverter_id, capacity_kw)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    data = []
    current = start_time
    while current <= end_time:
        data.append(simulator.generate(current))
        current += timedelta(minutes=interval_minutes)
    
    return data


def main():
    """命令行入口."""
    parser = argparse.ArgumentParser(description="逆变器数据模拟器")
    parser.add_argument("--station-id", type=int, default=1, help="电站ID")
    parser.add_argument("--inverter-id", type=str, default="INV001", help="逆变器ID")
    parser.add_argument("--capacity", type=float, default=1000, help="装机容量(kW)")
    parser.add_argument("--days", type=int, default=30, help="历史数据天数")
    parser.add_argument("--interval", type=int, default=5, help="数据间隔(分钟)")
    parser.add_argument("--output", type=str, default="simulated_data.json", help="输出文件")
    
    args = parser.parse_args()
    
    print(f"正在生成 {args.days} 天历史数据，间隔 {args.interval} 分钟...")
    data = generate_historical_data(
        args.station_id,
        args.inverter_id,
        args.capacity,
        args.days,
        args.interval,
    )
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"已生成 {len(data)} 条数据，保存到 {args.output}")


if __name__ == "__main__":
    main()
