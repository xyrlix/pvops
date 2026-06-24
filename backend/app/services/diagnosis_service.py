"""诊断服务."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.station import Station
from app.models.timeseries import InverterData, WeatherData

logger = logging.getLogger(__name__)


class DiagnosisResult:
    """诊断结果."""

    def __init__(
        self,
        station_id: int,
        station_name: str,
        diagnosis_time: datetime,
    ):
        self.station_id = station_id
        self.station_name = station_name
        self.diagnosis_time = diagnosis_time
        self.overall_health = 100.0
        self.findings: List[Dict[str, Any]] = []
        self.summary = ""
        self.suggestions: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "station_id": self.station_id,
            "station_name": self.station_name,
            "diagnosis_time": self.diagnosis_time.isoformat(),
            "overall_health": round(self.overall_health, 1),
            "summary": self.summary,
            "findings": self.findings,
            "suggestions": self.suggestions,
        }


async def get_station_name(station_id: int) -> str:
    """获取电站名称."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Station).where(Station.id == station_id))
        station = result.scalar_one_or_none()
        return station.name if station else f"电站 {station_id}"


async def diagnose_station(station_id: int) -> Dict[str, Any]:
    """对电站进行全面诊断."""
    station_name = await get_station_name(station_id)
    result = DiagnosisResult(station_id, station_name, datetime.now())

    async with AsyncSessionLocal() as session:
        # 获取最近 24 小时数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        inv_result = await session.execute(
            select(InverterData)
            .where(
                InverterData.station_id == station_id,
                InverterData.timestamp >= start_time,
                InverterData.timestamp <= end_time,
            )
            .order_by(desc(InverterData.id))
        )
        inv_data = list(inv_result.scalars().all())

        weather_result = await session.execute(
            select(WeatherData)
            .where(
                WeatherData.station_id == station_id,
                WeatherData.timestamp >= start_time,
                WeatherData.timestamp <= end_time,
            )
            .order_by(desc(WeatherData.id))
        )
        weather_data = list(weather_result.scalars().all())

    if not inv_data:
        result.summary = "近 24 小时内没有逆变器数据，无法完成诊断。请检查数据采集是否正常。"
        result.overall_health = 0
        result.suggestions.append("检查采集网关和通信链路")
        return result.to_dict()

    # 按逆变器分组
    inverter_groups: Dict[str, List[InverterData]] = {}
    for record in inv_data:
        inverter_groups.setdefault(record.inverter_id, []).append(record)

    # 执行各项诊断规则
    for inverter_id, records in inverter_groups.items():
        await _check_power_generation(result, inverter_id, records)
        await _check_pr_performance(result, inverter_id, records)
        await _check_communication_gap(result, inverter_id, records)
        await _check_fault_codes(result, inverter_id, records)
        await _check_voltage_current(result, inverter_id, records)

    # 计算综合健康度
    if result.findings:
        critical_count = sum(1 for f in result.findings if f["severity"] == "critical")
        warning_count = sum(1 for f in result.findings if f["severity"] == "warning")
        result.overall_health = max(0, 100 - critical_count * 25 - warning_count * 10)

    # 生成总结
    if not result.findings:
        result.summary = f"{station_name} 近 24 小时运行正常，未检测到明显异常。系统健康度良好。"
        result.suggestions.append("继续保持日常巡检")
        result.suggestions.append("关注组件清洗周期")
    else:
        critical_items = [f for f in result.findings if f["severity"] == "critical"]
        warning_items = [f for f in result.findings if f["severity"] == "warning"]
        if critical_items:
            result.summary = (
                f"{station_name} 近 24 小时诊断发现 "
                f"{len(critical_items)} 项严重问题、{len(warning_items)} 项警告。"
                f"建议优先处理严重问题，并持续观察警告项。"
            )
        else:
            result.summary = (
                f"{station_name} 近 24 小时诊断发现 {len(warning_items)} 项警告，"
                f"暂无严重问题。建议持续观察并适时处理。"
            )

        # 提取前 3 条建议
        all_suggestions = []
        for finding in result.findings:
            all_suggestions.extend(finding.get("suggestions", []))
        result.suggestions = all_suggestions[:3]

    return result.to_dict()


async def _check_power_generation(
    result: DiagnosisResult,
    inverter_id: str,
    records: List[InverterData],
) -> None:
    """检查白天发电情况."""
    # 白天有辐照但功率为 0 的记录
    daytime_zero_power = [
        r for r in records
        if r.irradiance_w_m2 > 200 and r.active_power_kw < 1
    ]

    if daytime_zero_power:
        latest = daytime_zero_power[0]
        result.findings.append({
            "category": "发电异常",
            "severity": "critical",
            "title": f"逆变器 {inverter_id} 白天无功率",
            "description": (
                f"在辐照度 {latest.irradiance_w_m2:.1f} W/m² 的条件下，"
                f"逆变器输出功率为 {latest.active_power_kw:.2f} kW，存在发电中断风险。"
            ),
            "evidence": [
                f"时间：{latest.timestamp.strftime('%Y-%m-%d %H:%M')}",
                f"辐照度：{latest.irradiance_w_m2:.1f} W/m²",
                f"有功功率：{latest.active_power_kw:.2f} kW",
                f"直流电压：{latest.dc_voltage_v:.1f} V",
                f"直流电流：{latest.dc_current_a:.1f} A",
            ],
            "root_cause": "可能原因：逆变器停机、直流侧断路器跳闸、组件严重遮挡或直流线缆故障。",
            "suggestions": [
                "检查逆变器运行状态和故障码",
                "检查直流侧开关和线缆连接",
                "检查组件是否存在大面积遮挡或损坏",
            ],
        })


async def _check_pr_performance(
    result: DiagnosisResult,
    inverter_id: str,
    records: List[InverterData],
) -> None:
    """检查 PR 性能."""
    # 筛选白天高辐照数据
    high_irradiance = [r for r in records if r.irradiance_w_m2 > 500]
    if not high_irradiance:
        return

    low_pr_records = []
    for r in high_irradiance:
        theoretical = r.irradiance_w_m2 / 1000 * 1000  # 假设装机容量 1000kW
        if theoretical > 0:
            pr = r.active_power_kw / theoretical
            if pr < 0.7:
                low_pr_records.append((r, pr))

    if len(low_pr_records) >= 3:
        latest, pr = low_pr_records[0]
        avg_pr = sum(pr for _, pr in low_pr_records[:5]) / len(low_pr_records[:5])
        result.findings.append({
            "category": "性能衰减",
            "severity": "warning",
            "title": f"逆变器 {inverter_id} PR 偏低",
            "description": (
                f"近 24 小时检测到 {len(low_pr_records)} 次 PR 低于 70%，"
                f"最新一次 PR 为 {pr*100:.1f}%，平均 PR {avg_pr*100:.1f}%。"
            ),
            "evidence": [
                f"时间：{latest.timestamp.strftime('%Y-%m-%d %H:%M')}",
                f"辐照度：{latest.irradiance_w_m2:.1f} W/m²",
                f"实际功率：{latest.active_power_kw:.2f} kW",
                f"理论功率：{latest.irradiance_w_m2 / 1000 * 1000:.2f} kW",
                f"PR：{pr*100:.1f}%",
            ],
            "root_cause": "可能原因：组件积灰、局部遮挡、组件衰减、逆变器效率下降或温度异常。",
            "suggestions": [
                "检查组件表面清洁度，安排清洗",
                "排查周边遮挡物（树木、建筑、积雪等）",
                "检查逆变器散热是否正常",
            ],
        })


async def _check_communication_gap(
    result: DiagnosisResult,
    inverter_id: str,
    records: List[InverterData],
) -> None:
    """检查通讯中断."""
    if len(records) < 2:
        return

    # 按时间正序
    sorted_records = sorted(records, key=lambda r: r.timestamp)
    max_gap = timedelta(minutes=0)
    gap_start = None

    for i in range(1, len(sorted_records)):
        gap = sorted_records[i].timestamp - sorted_records[i - 1].timestamp
        if gap > max_gap:
            max_gap = gap
            gap_start = sorted_records[i - 1].timestamp

    if max_gap > timedelta(minutes=30):
        result.findings.append({
            "category": "通讯异常",
            "severity": "warning",
            "title": f"逆变器 {inverter_id} 通讯中断",
            "description": f"检测到最长通讯中断 {int(max_gap.total_seconds() // 60)} 分钟。",
            "evidence": [
                f"中断开始：{gap_start.strftime('%Y-%m-%d %H:%M') if gap_start else '未知'}",
                f"中断时长：{int(max_gap.total_seconds() // 60)} 分钟",
                f"数据点数：{len(records)} 条",
            ],
            "root_cause": "可能原因：网络波动、采集网关异常、逆变器离线或通信线缆故障。",
            "suggestions": [
                "检查采集网关运行状态",
                "检查逆变器网络连接",
                "确认通信协议配置是否正确",
            ],
        })


async def _check_fault_codes(
    result: DiagnosisResult,
    inverter_id: str,
    records: List[InverterData],
) -> None:
    """检查故障码."""
    fault_records = [r for r in records if r.fault_code and r.fault_code > 0]

    if fault_records:
        latest = fault_records[0]
        result.findings.append({
            "category": "设备故障",
            "severity": "critical",
            "title": f"逆变器 {inverter_id} 故障码 {latest.fault_code}",
            "description": f"逆变器上报故障码 {latest.fault_code}，共出现 {len(fault_records)} 次。",
            "evidence": [
                f"时间：{latest.timestamp.strftime('%Y-%m-%d %H:%M')}",
                f"故障码：{latest.fault_code}",
                f"出现次数：{len(fault_records)}",
            ],
            "root_cause": "逆变器检测到内部异常，具体原因需参考厂家故障码手册。",
            "suggestions": [
                "查询逆变器故障码手册",
                "重启逆变器观察是否恢复",
                "联系厂家技术支持",
            ],
        })


async def _check_voltage_current(
    result: DiagnosisResult,
    inverter_id: str,
    records: List[InverterData],
) -> None:
    """检查电压电流异常."""
    high_voltage = [r for r in records if r.dc_voltage_v > 800]
    low_voltage = [r for r in records if r.dc_voltage_v > 0 and r.dc_voltage_v < 400]

    if high_voltage:
        latest = high_voltage[0]
        result.findings.append({
            "category": "电气异常",
            "severity": "warning",
            "title": f"逆变器 {inverter_id} 直流电压偏高",
            "description": f"检测到 {len(high_voltage)} 次直流电压超过 800V，最高 {latest.dc_voltage_v:.1f} V。",
            "evidence": [
                f"时间：{latest.timestamp.strftime('%Y-%m-%d %H:%M')}",
                f"直流电压：{latest.dc_voltage_v:.1f} V",
                f"直流电流：{latest.dc_current_a:.1f} A",
            ],
            "root_cause": "可能原因：组串串联过多、温度降低导致开路电压升高。",
            "suggestions": [
                "检查组串配置是否超限",
                "确认逆变器最大直流输入电压",
            ],
        })

    if low_voltage:
        latest = low_voltage[0]
        result.findings.append({
            "category": "电气异常",
            "severity": "warning",
            "title": f"逆变器 {inverter_id} 直流电压偏低",
            "description": f"检测到 {len(low_voltage)} 次直流电压低于 400V，最低 {latest.dc_voltage_v:.1f} V。",
            "evidence": [
                f"时间：{latest.timestamp.strftime('%Y-%m-%d %H:%M')}",
                f"直流电压：{latest.dc_voltage_v:.1f} V",
                f"直流电流：{latest.dc_current_a:.1f} A",
            ],
            "root_cause": "可能原因：组串连接松动、组件损坏、光照不足或MPPT故障。",
            "suggestions": [
                "检查组串连接是否牢固",
                "排查损坏组件",
            ],
        })
