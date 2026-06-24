"""应用配置."""

import os
from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    """应用配置类."""

    app_name: str = "PVOps"
    app_version: str = "0.1.0"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

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

    # Mock 数据开关：本地演示默认开启，接入真实数据后设为 false
    use_mock_data: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例."""
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./pvops.db"),
    )
