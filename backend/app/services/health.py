"""健康度评分工具."""

from app.models.timeseries import InverterData, WeatherData


def calculate_health_score(inv_data: InverterData, weather_data: WeatherData | None) -> float:
    """计算健康度评分（0-100）."""
    score = 100.0

    # 白天有辐照但功率为 0，大幅扣分
    if weather_data and weather_data.irradiance_w_m2 > 100:
        if inv_data.active_power_kw < 1:
            score -= 50
        elif inv_data.active_power_kw < weather_data.irradiance_w_m2 / 1000 * 1000 * 0.3:
            score -= 20

    # 故障码扣分
    if inv_data.fault_code and inv_data.fault_code > 0:
        score -= 30

    return max(0.0, min(100.0, score))
