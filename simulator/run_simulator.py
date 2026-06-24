"""运行模拟器并发送数据到后端."""

import argparse
import time
from datetime import datetime, timedelta

import requests

from inverter_simulator import InverterSimulator, WeatherSimulator


def send_inverter_data(base_url: str, data: dict) -> bool:
    """发送逆变器数据."""
    try:
        response = requests.post(
            f"{base_url}/api/v1/simulator/inverter",
            json=data,
            timeout=5,
        )
        return response.status_code == 200
    except Exception as e:
        print(f"发送逆变器数据失败: {e}")
        return False


def send_weather_data(base_url: str, data: dict) -> bool:
    """发送气象数据."""
    try:
        response = requests.post(
            f"{base_url}/api/v1/simulator/weather",
            json=data,
            timeout=5,
        )
        return response.status_code == 200
    except Exception as e:
        print(f"发送气象数据失败: {e}")
        return False


def run_realtime_simulator(
    base_url: str,
    station_id: int,
    inverter_id: str,
    capacity_kw: float,
    interval: int = 60,
    duration_minutes: int = 0,
    demo_mode: bool = False,
) -> None:
    """实时发送模拟数据."""
    inverter = InverterSimulator(station_id, inverter_id, capacity_kw)
    weather = WeatherSimulator(station_id)

    print(f"开始实时模拟：电站 {station_id}，逆变器 {inverter_id}，容量 {capacity_kw} kW")
    print(f"数据将每 {interval} 秒推送到 {base_url}")
    if demo_mode:
        print("演示模式：模拟一天 6:00-18:00 的发电过程循环播放")
    print("按 Ctrl+C 停止")

    start_time = datetime.now()
    count = 0
    demo_minutes = 6 * 60  # 演示模式从早上 6 点开始

    try:
        while True:
            if demo_mode:
                # 演示模式：每 interval 秒推进 10 分钟虚拟时间
                now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                now += timedelta(minutes=demo_minutes)
                demo_minutes += 10
                # 循环一天
                if demo_minutes >= 20 * 60:
                    demo_minutes = 6 * 60
                    inverter.daily_energy_kwh = 0
            else:
                now = datetime.now()

            inv_data = inverter.generate(now)
            weather_data = weather.generate(now)

            send_inverter_data(base_url, inv_data)
            send_weather_data(base_url, weather_data)

            count += 1
            print(
                f"[{now.strftime('%H:%M:%S')}] "
                f"功率: {inv_data['active_power_kw']:6.2f} kW | "
                f"日发电: {inv_data['daily_energy_kwh']:8.2f} kWh | "
                f"辐照: {weather_data['irradiance_w_m2']:6.2f} W/m² | "
                f"温度: {weather_data['ambient_temp_c']:5.1f} ℃"
            )

            # 检查运行时长
            if not demo_mode and duration_minutes > 0:
                elapsed = (datetime.now() - start_time).total_seconds() / 60
                if elapsed >= duration_minutes:
                    print(f"已达到运行时长 {duration_minutes} 分钟，共发送 {count} 条数据")
                    break

            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n模拟器已停止，共发送 {count} 条数据")


def load_historical_data(base_url: str, file_path: str) -> None:
    """加载历史数据文件到后端."""
    import json

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"正在加载 {len(data)} 条历史数据...")

    # 分批发送，每批 100 条
    batch_size = 100
    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        try:
            response = requests.post(
                f"{base_url}/api/v1/simulator/inverter/batch",
                json=batch,
                timeout=30,
            )
            result = response.json()
            print(f"批次 {i//batch_size + 1}: 成功 {result.get('success', 0)} 条，失败 {result.get('failed', 0)} 条")
        except Exception as e:
            print(f"批次 {i//batch_size + 1} 发送失败: {e}")

    print("历史数据加载完成")


def main():
    parser = argparse.ArgumentParser(description="运行数据模拟器")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="后端地址")
    parser.add_argument("--station-id", type=int, default=1, help="电站ID")
    parser.add_argument("--inverter-id", type=str, default="INV001", help="逆变器ID")
    parser.add_argument("--capacity", type=float, default=1000, help="装机容量(kW)")
    parser.add_argument("--interval", type=int, default=5, help="发送间隔(秒)")
    parser.add_argument("--duration", type=int, default=0, help="运行时长(分钟)，0表示一直运行")
    parser.add_argument("--demo-mode", action="store_true", help="演示模式：循环播放一天发电过程")
    parser.add_argument("--load-history", type=str, help="加载历史数据文件路径")

    args = parser.parse_args()

    if args.load_history:
        load_historical_data(args.base_url, args.load_history)
    else:
        run_realtime_simulator(
            args.base_url,
            args.station_id,
            args.inverter_id,
            args.capacity,
            args.interval,
            args.duration,
            args.demo_mode,
        )


if __name__ == "__main__":
    main()
