"""诊断 Agent."""

from typing import Any

from app.services import diagnosis_service


class DiagnosisAgent:
    """电站/设备诊断 Agent."""

    async def diagnose_station(self, station_id: int) -> dict[str, Any]:
        """生成电站诊断报告."""
        # 目前使用规则引擎进行诊断
        # 后续可接入 LLM 对规则结果进行自然语言润色和扩展
        return await diagnosis_service.diagnose_station(station_id)

    async def diagnose_device(
        self,
        station_id: int,
        device_id: str,
    ) -> dict[str, Any]:
        """生成设备级诊断（预留）."""
        result = await diagnosis_service.diagnose_station(station_id)
        # 过滤特定设备的发现
        device_findings = [
            f for f in result.get("findings", [])
            if device_id in f.get("title", "")
        ]
        result["findings"] = device_findings
        result["summary"] = f"设备 {device_id} 诊断完成，发现 {len(device_findings)} 项异常。"
        return result
