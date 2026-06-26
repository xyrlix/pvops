# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

PVOps（光伏运维智能体）是面向新能源资产运营商的 AI 运营决策平台：场站采集、设备资产、指标/健康度、AI 诊断、工单、知识库问答；后续阶段储能/电力交易。详细背景见 `README.md` 与 `docs/光伏运维智能体-实施总方案-终版.md`。开发流程：feature → develop → main，每 2 周发布。

## 常用命令

### 一键启动 / 停止（推荐）

```bash
cd /path/to/pvops
cp .env.example .env
./deploy/start.sh    # 构建前端 + docker compose up
./deploy/stop.sh     # 停止所有服务
cd deploy && ./update.sh   # 拉取最新代码并重建
```

### 后端本地开发（SQLite fallback，最小依赖）

```bash
cd backend
export TSDB_BACKEND=sqlite
export DATABASE_URL=sqlite+aiosqlite:///./pvops.db
PYTHONPATH=backend:.:backend/.apt-libs/usr/lib/python3/dist-packages \
  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

首次需 `pip install -r requirements-dev.txt`。环境缺 pytest/httpx 时，使用 `PYTHONPATH=backend:. python3 scripts/sanity_check.py` 做轻量烟囱测试（覆盖 LLM factory 与本地向量库）。

### 采集器（独立边缘网关）

```bash
PYTHONPATH=backend:. python3 scripts/collector.py --station-id 1 --interval 5
```

写入失败的载荷会自动落入 `LocalQueue`（SQLite），下一轮重试时补发。

### 模拟器（旧接口仍兼容，向后端 HTTP 推数据）

```bash
cd simulator
PYTHONPATH=../backend:. python3 run_simulator.py \
  --base-url http://localhost:8000 --station-id 1 --inverter-id INV001 --interval 5 --demo-mode
```

### 前端

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173（已配置 /api 代理到 :8000）
npm run build        # vue-tsc + vite build，产物 frontend/dist 由后端 StaticFiles 提供
npm run lint         # eslint
npm run lint:fix
npm run type-check   # vue-tsc --noEmit
npm run test:unit    # vitest run
npm run format       # prettier
```

前端 `.env`：`VITE_API_BASE_URL=/api/v1`、`VITE_USE_MOCK_DATA=true`（纯前端演示/UI 验收时打开，所有请求走 `src/services/mockData.ts`）。

### 后端测试 / 代码质量

```bash
cd backend
pytest                       # 或 pytest tests/test_xxx.py -v 运行单个文件
ruff check .
ruff format --check .
mypy app/
bandit -r app/
```

CI 在 `.github/workflows/ci.yml`：lint + type-check + 单测 + docker compose config 校验。

## 架构总览

仓库分四个进程边界：(1) FastAPI 后端 `backend/`、(2) Vue 3 前端 `frontend/`、(3) 独立采集器 `scripts/collector.py`、(4) `simulator/`。后端启动时挂载 `frontend/dist` 作为静态资源，提供 SPA fallback。

### 后端（`backend/app/`）

按职责分包；新增能力先选包：

- `api/v1/` — FastAPI 路由，每个领域一文件（`stations` / `devices` / `metrics` / `dashboard` / `alarms` / `work_orders` / `reports` / `diagnosis` / `kb` / `chat` / `simulator` / `ingest` / `auth` / `health`），`__init__.py` 汇总到 `api_router` 并以 `/api/v1` 前缀挂载（见 `main.py:198`）。
- `core/` — `config.get_settings()` 读取 `.env` 并缓存；`database.py` 暴露 `Base / AsyncSessionLocal / engine`；`security.py` 提供 JWT/密码哈希。
- `models/` — SQLAlchemy ORM：`station / device (含 inverter、string 子表) / timeseries (InverterData、WeatherData) / alarm / work_order / report / knowledge / user`。`Base.metadata.create_all` 在 `lifespan` 中执行；首次启动还会 seed 演示电站 + 3 台逆变器 + 12 组组串。
- `schemas/` — Pydantic v1 请求/响应模型（项目锁 `pydantic==1.10`，见 `requirements.txt`）。
- `services/` — 业务编排层：`metrics_service`、`alarm_service`、`work_order_service`、`diagnosis_service`、`report_service`、`knowledge_service`、`device_service`、`dashboard_service`、`mock_data`（无数据时补齐确定性 mock）。
- `repositories/` — 时序数据仓库抽象，`TimeSeriesRepository` 接口在 `base.py`。`factory.get_repository()` 按 `TSDB_BACKEND` 单例返回 `SQLiteTimeSeriesRepository` 或 `TDengineTimeSeriesRepository`。`reset_repository()` 仅供测试。
- `vectorstore/` — 知识库向量存储抽象。`factory.get_vector_store()` 优先探测 PGVector，不可用时回退 `LocalVectorStore`（SQLite 关键词检索）。
- `protocols/` — 设备协议适配器，继承 `BaseProtocolAdapter`（`base.py`）。`factory.create_adapter(protocol, device_code, config)` 支持 `simulator / modbus_tcp / modbus_rtu / mqtt_source`，加新协议只需新增文件并注册到 `factory.py`。`register_map.py` 维护 Modbus 寄存器定义。
- `collector/` — `CollectorRunner` 按 `device_type ∈ {inverter, weather_station, meter}` 轮询设备，失败数据进 `LocalQueue` 缓写。`simulator` 协议额外作为演示数据源。
- `llm/` — `factory.py` 暴露 `get_chat_llm()` / `get_embeddings()`，基于 `requests + asyncio.to_thread` 的 OpenAI 兼容客户端（OpenAI / DeepSeek / Kimi / Qwen / MiniMax）。`config.py` 内置预置 provider 默认值。未配置 Key 时返回友好提示字符串而非抛错。
- `agents/` — `diagnosis_agent`、`rag_agent`、`chat_service`，组合 LLM + 向量库 + 时序指标。
- `tasks/` — Celery worker/beat（`celery_app.py`），依赖 Redis。
- `tests/` — pytest 测试，asyncio 模式自动（见 `pyproject.toml`）。当 pytest 不可用时退化为 `scripts/sanity_check.py`。

### 前端（`frontend/src/`）

- `router/index.ts` — Vue Router，`meta.requiresAuth` 控制守卫，未登录跳 `/login`；首次进入受保护页时若未拉过用户，调 `authStore.fetchUser()`。
- `services/api.ts` — axios 实例（`baseURL: VITE_API_BASE_URL`），请求拦截注入 `Bearer ${token}`，401 自动清 token 跳登录。按域暴露 `xxxApi` 对象；几乎每个方法都内置 `USE_MOCK` 短路回 `mockData.ts`。
- `stores/` — Pinia：`auth`（token + user）、`copilot`（全局 AI 悬浮助手上下文）、`station`。
- `views/` — 一级页面，与路由一一对应：`HomeView`、`StationListView`、`StationDetailView`、`DiagnosisReportView`、`AlarmCenterView`、`WorkOrderView`、`ReportCenterView`、`KnowledgeBaseView`、`DeviceAnalysisView`、`DeviceManagementView`、`LoginView`。
- `components/` — 图表（`PowerChart`、`HeatmapChart`、`IrradiancePowerChart`、`GaugeChart`、`WaterfallChart`、`BarChart`、`DonutChart`、`BubbleChart`、`AlarmDonutChart`）和通用 UI（`DashboardLayout` 负责侧栏 + 顶栏 + 移动端抽屉；`PvCard/PvSkeleton/PvLoading/PvEmpty/PvTag` 一致化空/加载态；`AiCopilot` 全局 AI 入口）。
- `composables/`、 `types/`、 `styles/` 视具体页面需要补全。

### 部署 / 配置

- `deploy/docker-compose.yml` 编排 `backend / worker / scheduler / postgres / tdengine / redis / mosquitto / cloudflared(tunnel profile)`。
- `.env`（根目录）由 `core/config.py` 加载；关键变量：`DATABASE_URL`、`TSDB_BACKEND`、`TDENGINE_*`、`REDIS_URL`、`MQTT_*`、`LLM_*` / `EMBEDDING_*`、`USE_MOCK_DATA`、`CF_TUNNEL_TOKEN`。
- TDengine 容器失败时 `repositories/factory.py` 不会自动 fallback —— 需手动把 `TSDB_BACKEND` 改为 `sqlite`。

## 开发约定

- 后端遵循 `backend/AGENTS.md`：`from __future__ import annotations`、Pydantic v1 写法、可空字段用 `Optional[...]`、外部依赖通过 `.env` 注入；Pytest 不可用时跑 `scripts/sanity_check.py`。
- 修改时序写入路径时同时考虑 SQLite（`repositories/sqlite_repository.py`）和 TDengine（`tdengine_repository.py`）实现。
- 新增协议：实现 `BaseProtocolAdapter` → 在 `protocols/factory.py` 注册 → 在 `collector/runner.py` 的 `target_types` 中按需包含。
- 新增 API 域：在 `api/v1/<domain>.py` 暴露 router → 在 `api/v1/__init__.py` include；如需要 Mock 在 `frontend/src/services/mockData.ts` 同步添加。
- LLM/Embedding 调用统一经过 `llm/factory.py`，不要在 service 里直接 `import requests`。
- 向量存储新增数据源时实现 `VectorStore`（`vectorstore/base.py`），在 `vectorstore/factory.py` 注册并优先探测。
