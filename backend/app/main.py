"""FastAPI 应用入口."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.migrate import run_migrations
from app.core.seed import seed_initial_data
from app.repositories import close_all_repositories, initialize_repository
from app.vectorstore import close_all_vector_stores, get_vector_store

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    # 1) 业务库 schema 由 Alembic 管理（alembic upgrade head）。
    #    任何 schema 变更都应通过 alembic revision --autogenerate 增量生成迁移，
    #    不再使用 Base.metadata.create_all。
    await run_migrations()

    # 2) 演示数据 seeding（默认开启，生产请关闭）
    if settings.seed_demo_on_startup:
        await seed_initial_data()

    # 3) 时序仓库（TDengine 不可用时自动 fallback SQLite）
    await initialize_repository()

    # 4) 向量存储（PGVector 不可用时 fallback 本地 SQLite 关键词检索）
    await get_vector_store()

    yield

    # 关闭时清理
    await close_all_repositories()
    await close_all_vector_stores()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="光伏运维智能体 API",
    lifespan=lifespan,
)

# CORS
_cors_raw = settings.cors_allow_origins.strip()
_cors_origins = ["*"] if _cors_raw in ("", "*") else [o.strip() for o in _cors_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=(_cors_origins != ["*"]),
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(api_router, prefix="/api/v1")

# 静态前端文件（SPA fallback）。
# 本地开发：frontend/dist；Docker：backend/static
possible_static_dirs = [
    Path(__file__).parent.parent.parent / "frontend" / "dist",
    Path(__file__).parent.parent / "static",
]
static_dir = next((d for d in possible_static_dirs if d.exists()), None)


if static_dir and static_dir.exists():
    # 把 dist 下的 hashed assets 用 StaticFiles 高优先级挂载（js/css/img）。
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir), check_dir=False),
            name="assets",
        )

    from fastapi import Request as _Req

    # SPA fallback：未命中的 GET 一律返回 index.html（Vue Router history 模式）。
    # 已在 /assets 下找到的文件不会被这条规则捕获（mount 优先级更高）。
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str, request: _Req):
        # /api 路径已由上面的 api_router 处理；落进来的就是真正的 404，
        # 应当返回 JSON 而非 SPA index.html。
        if full_path.startswith("api/"):
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "Not found"}, status_code=404)
        # 真实存在的 dist 根级静态文件（如 favicon.svg）原样返回
        candidate = static_dir / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        # 否则返回 index.html 让前端路由接管
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        from fastapi.responses import JSONResponse

        return JSONResponse({"detail": "frontend dist not built"}, status_code=404)


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """API 路由的 404 走 JSON 响应."""
    from fastapi.responses import JSONResponse

    return JSONResponse({"detail": "Not found"}, status_code=404)
