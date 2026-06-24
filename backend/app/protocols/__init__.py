"""协议适配层."""

from app.protocols.base import BaseProtocolAdapter, CollectorPoint
from app.protocols.factory import create_adapter

__all__ = ["BaseProtocolAdapter", "CollectorPoint", "create_adapter"]
