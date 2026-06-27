"""用户模型."""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """用户表."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(50), nullable=True)
    role = Column(
        String(20), default="operator"
    )  # admin / manager / operator / viewer / superadmin
    status = Column(String(20), default="active")  # active / disabled
    # 租户 ID：null 表示超管（跨租户访问）；否则限定到单一租户。
    tenant_id = Column(Integer, nullable=True, index=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
