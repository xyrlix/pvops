"""LLM / Embedding Provider 注册表.

内置 OpenAI 兼容实现；新增非 OpenAI 协议供应商（如 Anthropic）时调用
``register_chat_provider(name, factory)`` / ``register_embed_provider(...)`` 即可。

注册表是模块级单例，应用启动后保持不变；测试时可调用
``reset_providers_for_testing()`` 清空。
"""

from __future__ import annotations

import logging
from typing import Callable, Dict

from app.llm.providers.base import EmbeddingProvider, LLMProvider
from app.llm.providers.openai_compat import (
    OpenAICompatChatProvider,
    OpenAICompatEmbeddingProvider,
)

logger = logging.getLogger(__name__)


# 工厂签名：(name, api_key, base_url, model) -> Provider 实例
ChatFactory = Callable[[str, str, str, str], LLMProvider]
EmbedFactory = Callable[[str, str, str, str], EmbeddingProvider]

_chat_factories: Dict[str, ChatFactory] = {}
_embed_factories: Dict[str, EmbedFactory] = {}


def register_chat_provider(name: str, factory: ChatFactory) -> None:
    """注册聊天 provider 工厂."""
    if name in _chat_factories:
        logger.warning("覆盖已注册的聊天 provider: %s", name)
    _chat_factories[name] = factory
    logger.info("注册聊天 provider: %s", name)


def register_embed_provider(name: str, factory: EmbedFactory) -> None:
    """注册 embedding provider 工厂."""
    if name in _embed_factories:
        logger.warning("覆盖已注册的 embedding provider: %s", name)
    _embed_factories[name] = factory
    logger.info("注册 embedding provider: %s", name)


def get_chat_factory(name: str) -> ChatFactory | None:
    return _chat_factories.get(name)


def get_embed_factory(name: str) -> EmbedFactory | None:
    return _embed_factories.get(name)


def list_chat_providers() -> list[str]:
    return sorted(_chat_factories.keys())


def list_embed_providers() -> list[str]:
    return sorted(_embed_factories.keys())


# ─── 内置注册 ───────────────────────────────────────────────

# OpenAI 兼容协议覆盖: openai / deepseek / kimi / qwen / minimax / custom
for _name in ("openai", "deepseek", "kimi", "qwen", "minimax", "custom"):
    register_chat_provider(
        _name,
        lambda name, key, url, model: OpenAICompatChatProvider(name, key, url, model),
    )

# Embedding 兼容协议：openai 系列
for _name in ("openai", "deepseek", "qwen", "custom"):
    register_embed_provider(
        _name,
        lambda name, key, url, model: OpenAICompatEmbeddingProvider(name, key, url, model),
    )


def reset_providers_for_testing() -> None:
    """清空注册表（仅测试用）."""
    _chat_factories.clear()
    _embed_factories.clear()