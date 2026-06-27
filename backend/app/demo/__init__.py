"""DataProvider 工厂.

``get_data_provider()`` 返回当前事件循环对应的 provider 实例，
根据 ``settings.use_mock_data`` 切换 mock / real 实现。

弱引用 + 事件循环缓存模式与 ``repositories.factory`` 一致，避免
uvicorn reload / pytest-asyncio 多 loop 下绑定已关闭 loop 报错。
"""

from __future__ import annotations

import asyncio
import logging
import weakref

from app.core.config import get_settings
from app.demo.mock_provider import MockDataProvider
from app.demo.provider import DataProvider
from app.demo.real_provider import RealDataProvider

logger = logging.getLogger(__name__)

# 缓存每个事件循环的 provider 实例
_loop_providers: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, DataProvider] = (
    weakref.WeakKeyDictionary()
)


def _build(use_mock: bool) -> DataProvider:
    """根据 use_mock 构造 provider."""
    if use_mock:
        logger.info("DataProvider: MockDataProvider")
        return MockDataProvider()
    logger.info("DataProvider: RealDataProvider")
    return RealDataProvider()


def get_data_provider() -> DataProvider:
    """获取当前事件循环对应的 provider.

    第一次调用根据 settings.use_mock_data 决定；之后若 settings 变更，
    需显式调用 ``reset_data_provider()`` 才能切换（默认仅 lifespan 启动时
    调用一次）。开发热改可用环境变量 ``PVOPS_FORCE_MOCK=1`` 强制 mock。
    """
    import os

    loop = asyncio.get_running_loop()
    provider = _loop_providers.get(loop)
    if provider is None:
        use_mock = get_settings().use_mock_data
        if os.getenv("PVOPS_FORCE_MOCK") == "1":
            use_mock = True
        elif os.getenv("PVOPS_FORCE_REAL") == "1":
            use_mock = False
        provider = _build(use_mock)
        _loop_providers[loop] = provider
    return provider


def reset_data_provider() -> None:
    """清空缓存（仅用于测试）。"""
    _loop_providers.clear()


__all__ = ["DataProvider", "get_data_provider", "reset_data_provider"]
