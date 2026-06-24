"""用户 schema."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    """用户基础 schema."""

    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "operator"
    status: str = "active"


class UserCreate(UserBase):
    """创建用户 schema."""

    password: str


class UserUpdate(BaseModel):
    """更新用户 schema."""

    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class UserResponse(UserBase):
    """用户响应 schema."""

    class Config:
        orm_mode = True

    id: int
    last_login: Optional[datetime]
    created_at: datetime


class UserLogin(BaseModel):
    """用户登录 schema."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """登录令牌响应."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
