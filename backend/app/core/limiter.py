"""慢速 API 限流器（slowapi）单例.

通过 ``app.state.limiter`` 挂载，并由 ``SlowAPIMiddleware`` 应用。
敏感接口（登录、注册、telemetry、LLM 调用）单独用 ``@limiter.limit("...")``
收紧；其他接口走 slowapi 的全局默认值（200/分钟/IP）。

单例而非模块级常量是为了方便测试时 ``limiter.reset()``。
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# key_func: 远端 IP；X-Forwarded-For 由 slowapi 自动读取（前提是反代正确设置）
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

__all__ = ["limiter"]