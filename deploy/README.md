# PVOps 私有化部署指南

## 快速启动（Docker Compose）

推荐直接使用一键脚本：

```bash
cd /path/to/pvops

# 1. 复制环境变量文件并修改
cp .env.example .env

# 2. 一键启动（自动构建前端、拉取镜像、启动核心服务）
./deploy/start.sh

# 3. 访问
# Web UI: http://localhost:8000
# API Docs: http://localhost:8000/docs

# 4. 停止
./deploy/stop.sh
```

如需手动控制，也可直接操作 docker compose：

```bash
# 构建并启动核心服务（首次需要拉取镜像，约 3-5 分钟）
docker compose -f deploy/docker-compose.yml up -d

# 查看日志
docker compose -f deploy/docker-compose.yml logs -f backend

# 停止并移除容器
docker compose -f deploy/docker-compose.yml down
```

## 服务说明

| 服务 | 说明 | 默认端口 |
| --- | --- | --- |
| backend | FastAPI + 静态前端 | 8000 |
| worker | Celery 异步任务 | - |
| scheduler | Celery Beat 定时任务 | - |
| postgres | 业务数据库（用户/电站/工单/告警） | 5432 |
| tdengine | 时序数据库（逆变器/气象/电表数据） | 6030/6041 |
| redis | 缓存与消息队列 | 6379 |
| mosquitto | MQTT Broker | 1883 |
| cloudflared | Cloudflare Tunnel（可选，需要 CF_TUNNEL_TOKEN） | - |

## 关键配置项

编辑 `.env`：

```ini
# 业务数据库
DATABASE_URL=postgresql+asyncpg://pvops:pvops_password@postgres:5432/pvops

# 时序数据库后端：sqlite | tdengine
TSDB_BACKEND=tdengine

# TDengine 连接信息（需与 docker-compose 中一致）
TDENGINE_HOST=tdengine
TDENGINE_PORT=6030
TDENGINE_USER=root
TDENGINE_PASSWORD=taosdata
TDENGINE_DATABASE=pvops
```

## 本地开发（无 Docker）

如果暂时无法使用 Docker，可直接用 SQLite 作为时序与业务库：

```bash
cd pvops

# 使用 SQLite fallback
export TSDB_BACKEND=sqlite
export DATABASE_URL=sqlite+aiosqlite:///./pvops.db
export USE_MOCK_DATA=true

# 已安装依赖时直接启动；否则：pip install -r backend/requirements.txt
PYTHONPATH=backend:.:backend/.apt-libs/usr/lib/python3/dist-packages \
  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

前端构建（使用本地 Mock 数据，无需后端）：

```bash
cd frontend
cp .env.example .env
npm install
npm run build
```

前端 `.env` 关键项：

```ini
VITE_API_BASE_URL=/api/v1
# 是否使用前端 Mock 数据（不请求真实后端）
VITE_USE_MOCK_DATA=true
```

## 模拟数据 vs 真实数据

本项目支持两层 Mock/真实切换，方便演示和后续接入：

### 后端 Mock 开关

设置 `USE_MOCK_DATA=true`（默认）：

- 当 TSDB/设备表无数据时，自动返回确定性模拟数据。
- 当已有真实数据时，优先使用真实数据，仅在缺失处补齐。

接入真实数据后：

```ini
USE_MOCK_DATA=false
TSDB_BACKEND=tdengine
```

### 前端 Mock 开关

`VITE_USE_MOCK_DATA=true` 时，前端所有 API 直接走 `src/services/mockData.ts`，不请求后端。
适合纯前端演示、UI 验收或后端不可用时使用。

关闭后，前端通过 `VITE_API_BASE_URL` 请求真实后端。

### 接入真实逆变器

1. 在“设备管理”添加设备，设置 `protocol` 和 `config` 字段。
2. 支持的协议：`simulator`（模拟）、`modbus_tcp`、`modbus_rtu`。
3. 启动边缘采集器：

```bash
PYTHONPATH=backend:. python3 scripts/collector.py --station-id 1 --interval 5
```

## 采集器启动

在容器外或作为独立边缘网关运行：

```bash
PYTHONPATH=backend:. python3 scripts/collector.py --station-id 1 --interval 5
```

## TDengine 常用命令

```bash
# 进入 TDengine 容器
docker exec -it pvops-tdengine taos

# 查看数据库
SHOW DATABASES;
USE pvops;
SHOW STABLES;
SELECT * FROM inverter_data LIMIT 10;
```

## 故障排查

1. **backend 无法启动，提示等待服务失败**
   - 检查 postgres/tdengine/redis 是否健康：`docker compose ps`
   - 查看对应服务日志：`docker compose logs tdengine`

2. **TDengine 连接失败，自动 fallback 到 SQLite**
   - 检查 `TSDB_BACKEND` 是否为 `tdengine`
   - 确认 taosws 已安装：`python3 -c "import taosws"`

3. **前端页面空白**
   - 确认 `frontend/dist` 已生成
   - 检查 backend 是否能读取静态文件
