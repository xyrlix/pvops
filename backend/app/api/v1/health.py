"""健康检查接口."""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("")
async def health_check() -> dict[str, str]:
    """健康检查."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ping")
async def ping() -> dict[str, str]:
    """简单 ping 测试."""
    return {"message": "pong"}
