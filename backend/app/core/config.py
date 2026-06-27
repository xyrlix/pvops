"""应用配置.

pydantic-settings v2；通过 `.env` 加载。环境变量自动加载（大小写不敏感）。
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类 — mypy 可见的具名类型。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "PVOps"
    app_version: str = "0.1.0"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # CORS 允许来源（逗号分隔）。"*" 表示全部放行（仅推荐开发）。
    cors_allow_origins: str = "*"

    # Mock 数据开关：本地演示默认开启，接入真实数据后设为 false
    use_mock_data: bool = True

    # 启动时自动 seed 演示数据（生产环境应为 false）
    seed_demo_on_startup: bool = True

    # 默认设备协议（simulator / huawei_sun2000 / sungrow_sg / modbus_tcp / modbus_rtu / mqtt_source）
    default_device_protocol: str = "simulator"

    # 边缘网关 token（/ingest/telemetry 头 X-Gateway-Token）。
    # 空 = 跳过校验（仅推荐开发）。生产必须显式设置，建议 32+ 字符高熵随机。
    ingest_gateway_token: str = ""

    # Database - 默认使用 SQLite 便于本地演示
    database_url: str = "sqlite+aiosqlite:///./pvops.db"

    # 时序数据库后端：sqlite | tdengine
    tsdb_backend: str = "sqlite"

    # TDengine
    tdengine_host: str = "tdengine"
    tdengine_port: int = 6030
    tdengine_user: str = "root"
    tdengine_password: str = "taosdata"
    tdengine_database: str = "pvops"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MQTT
    mqtt_host: str = "mosquitto"
    mqtt_port: int = 1883

    # LLM / Embedding
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    embedding_provider: str = ""
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = ""


@lru_cache
def get_settings() -> Settings:
    """获取配置单例."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return Settings(database_url=db_url)
    return Settings()


# 启动时强制检查：secret_key 不得使用默认值；debug=True 时警告。
# 仅在主入口导入时执行一次，避免 unit-test 反复触发。
_DEFAULT_SECRET_KEYS = frozenset({"change-me-in-production", "secret", "changeme", ""})


def validate_settings_on_startup(settings: Settings | None = None) -> None:
    """应用启动时执行安全检查.

    - secret_key 不得为开发默认 / 空 / 常见弱口令。
    - debug=True 触发 WARNING。
    - seed_demo_on_startup=True 在生产模式 (debug=False) 触发 ERROR，
      防止演示数据混入生产数据库。
    """
    import logging
    import sys

    logger = logging.getLogger(__name__)
    settings = settings or get_settings()

    if settings.secret_key in _DEFAULT_SECRET_KEYS:
        msg = (
            "FATAL: secret_key 仍为默认值，必须在 .env 中显式设置一个高熵值。\n"
            '       生成方式: python -c "import secrets; print(secrets.token_urlsafe(64))"'
        )
        logger.critical(msg)
        print(msg, file=sys.stderr)
        raise SystemExit(1)

    if len(settings.secret_key) < 32:
        msg = f"FATAL: secret_key 太短 (len={len(settings.secret_key)})，至少需要 32 字符。"
        logger.critical(msg)
        print(msg, file=sys.stderr)
        raise SystemExit(1)

    if settings.debug:
        logger.warning("debug=True：仅推荐开发环境使用，生产请设为 false。")

    if settings.seed_demo_on_startup and not settings.debug:
        msg = "FATAL: 生产模式 (debug=False) 下不得开启 seed_demo_on_startup。"
        logger.critical(msg)
        print(msg, file=sys.stderr)
        raise SystemExit(1)
