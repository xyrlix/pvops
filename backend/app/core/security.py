"""安全相关工具."""

import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_gateway_token(request: Request) -> None:
    """校验边缘网关 token.

    期望请求头 ``X-Gateway-Token``，与 .env 中的 ``INGEST_GATEWAY_TOKEN``
    常量时间比较（hmac.compare_digest），防时序攻击。

    未配置 INGEST_GATEWAY_TOKEN 时（开发环境），跳过校验并打 WARNING。
    """
    expected = settings.ingest_gateway_token
    if not expected:
        import logging

        logging.getLogger(__name__).warning(
            "INGEST_GATEWAY_TOKEN 未配置：遥测接口处于开放状态，"
            "生产环境必须显式设置（建议 32+ 字符高熵随机）。"
        )
        return

    provided = request.headers.get("X-Gateway-Token", "")
    # 必须先编码成 bytes，hmac.compare_digest 不接受 str 与 bytes 混用
    if not hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing gateway token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """解码令牌."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
