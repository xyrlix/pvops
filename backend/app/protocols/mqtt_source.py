"""MQTT 数据源适配器.

边缘网关将设备数据发布到 MQTT Broker，本适配器订阅对应 topic 并解析 JSON 负载。
配置示例:
{
    "host": "localhost",
    "port": 1883,
    "topic": "pvops/station/{station_id}/device/{device_code}",
    "qos": 0,
    "client_id": "pvops_collector_xxx"
}
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.protocols.base import BaseProtocolAdapter, CollectorPoint

logger = logging.getLogger(__name__)


class MqttSourceAdapter(BaseProtocolAdapter):
    """MQTT 数据源适配器."""

    def __init__(self, device_code: str, config: dict[str, Any] | None = None):
        super().__init__(device_code, config)
        self.host = self.config.get("host", "localhost")
        self.port = int(self.config.get("port", 1883))
        self.topic = self.config.get("topic", f"pvops/device/{device_code}")
        self.qos = int(self.config.get("qos", 0))
        self.client_id = self.config.get("client_id", f"pvops_collector_{device_code}")
        self.timeout = float(self.config.get("timeout", 10))
        self._client = None
        self._latest_payload: dict[str, Any] | None = None

        try:
            from paho.mqtt.client import Client, MQTTMessage  # noqa: F401

            self._message_class = MQTTMessage
        except ImportError as e:
            logger.error("paho-mqtt 未安装，无法使用 MQTT 适配器")
            raise RuntimeError("paho-mqtt 未安装") from e

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info(f"MQTT 已连接，订阅 topic: {self.topic}")
            client.subscribe(self.topic, qos=self.qos)
        else:
            logger.warning(f"MQTT 连接返回码: {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            self._latest_payload = payload
            logger.debug(f"收到 MQTT 消息: {msg.topic} -> {payload}")
        except json.JSONDecodeError as e:
            logger.warning(f"MQTT 消息 JSON 解析失败: {e}")
        except Exception as e:
            logger.warning(f"MQTT 消息处理异常: {e}")

    async def connect(self) -> None:
        from paho.mqtt.client import Client

        client = Client(callback_api_version=2, client_id=self.client_id)
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.connect(self.host, self.port, keepalive=60)
        client.loop_start()
        self._client = client

    async def disconnect(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None

    async def read_points(self, points: list[CollectorPoint]) -> dict[str, Any]:
        """MQTT 通常直接推送完整 JSON，因此 read_points 返回最新 payload."""
        return self._latest_payload or {}

    async def collect_once(self) -> dict[str, Any]:
        payload = self._latest_payload or {}
        self._latest_payload = None
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            **payload,
        }


# mypy: disable-error-code="assignment,arg-type"
