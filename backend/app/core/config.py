"""应用配置.

优先使用 pydantic-settings v2；不可用时回退到 pydantic v1 的 BaseSettings。
环境变量自动加载（大小写不敏感）。
"""

from __future__ import annotations

import os
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore

    _USES_PYDANTIC_V2 = True
except ImportError:  # pragma: no cover - legacy pydantic v1 fallback
    from pydantic import BaseSettings  # type: ignore

    _USES_PYDANTIC_V2 = False


def _build_settings_cls():
    """构造 Settings 类（v2 与 v1 配置注入方式不同）."""
    if _USES_PYDANTIC_V2:

        class Settings(BaseSettings):
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

        return Settings

    # pydantic v1 fallback
    class Settings(BaseSettings):  # type: ignore[no-redef]
        app_name: str = "PVOps"
        app_version: str = "0.1.0"
        debug: bool = True
        secret_key: str = "change-me-in-production"

        backend_host: str = "0.0.0.0"
        backend_port: int = 8000

        cors_allow_origins: str = "*"
        use_mock_data: bool = True
        seed_demo_on_startup: bool = True

        database_url: str = "sqlite+aiosqlite:///./pvops.db"

        tsdb_backend: str = "sqlite"

        tdengine_host: str = "tdengine"
        tdengine_port: int = 6030
        tdengine_user: str = "root"
        tdengine_password: str = "taosdata"
        tdengine_database: str = "pvops"

        redis_url: str = "redis://redis:6379/0"

        mqtt_host: str = "mosquitto"
        mqtt_port: int = 1883

        llm_provider: str = "openai"
        llm_api_key: str = ""
        llm_base_url: str = ""
        llm_model: str = ""
        embedding_provider: str = ""
        embedding_api_key: str = ""
        embedding_base_url: str = ""
        embedding_model: str = ""

        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"

    return Settings


Settings = _build_settings_cls()  # noqa: F811


@lru_cache
def get_settings() -> Settings:
    """获取配置单例."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return Settings(database_url=db_url)
    return Settings()
