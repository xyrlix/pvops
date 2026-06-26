"""认证接口."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 天


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")  # 防爆破：每个 IP 每分钟最多 10 次
async def login(request: Request, form_data: UserLogin) -> dict:
    """用户登录."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.username == form_data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已禁用",
            )

        # 更新最后登录时间
        user.last_login = datetime.now()
        await session.commit()

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role},
            expires_delta=access_token_expires,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": UserResponse.from_orm(user),
        }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # 防滥用注册：每个 IP 每分钟最多 5 次
async def register(request: Request, user_data: UserCreate) -> User:
    """用户注册（预留，生产环境应关闭或仅限管理员）."""
    from app.core.security import get_password_hash

    async with AsyncSessionLocal() as session:
        # 检查用户名是否存在
        result = await session.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )

        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            status="active",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """获取当前用户信息."""
    return current_user
