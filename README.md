# 光伏运维智能体（PVOps）

> 面向新能源资产运营商的 AI 运营决策平台

## 项目简介

本项目是一个光伏运维智能体系统，支持：

- 光伏场站数据采集与监控
- 统一设备资产与拓扑管理
- 指标计算与健康度评估
- AI 辅助诊断与工单闭环
- 储能充放电策略优化（二期）
- 电力交易与虚拟电厂（三期）

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 PC/H5 | Vue 3 + Vite + TypeScript + Element Plus + ECharts |
| 后端 | FastAPI（Python 3.11+） |
| 时序数据库 | TDengine 3.x / SQLite fallback |
| 业务数据库 | PostgreSQL 16 / SQLite fallback |
| 缓存/队列 | Redis 7 + Celery |
| MQTT | Mosquitto |
| 协议适配 | Modbus TCP/RTU + Simulator + 可扩展厂家云 API |
| 部署 | Docker Compose + Cloudflare Tunnel |

## 项目结构

```
pvops/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── protocols/    # 协议适配层（Modbus/Simulator/...）
│   │   ├── collector/    # 边缘采集器 + 本地队列
│   │   ├── repositories/ # 时序仓库抽象（SQLite/TDengine）
│   │   └── ...
├── frontend/         # Vue 3 前端
├── simulator/        # 设备数据模拟器
├── deploy/           # Docker Compose 部署配置
├── scripts/          # 采集器、sanity 检查等脚本
└── docs/             # 项目文档
```

## 快速启动

### 方式一：Docker Compose（推荐，生产/完整开发环境）

```bash
cd pvops
cp .env.example .env

# 构建前端静态文件
cd frontend
npm install
npm run build
cd ..

# 启动完整服务
docker compose -f deploy/docker-compose.yml up -d
```

访问：

- 前端：http://localhost:8000
- 后端 API：http://localhost:8000/api/v1
- API 文档：http://localhost:8000/docs

### 方式二：本地 SQLite 开发（无 Docker，最小依赖）

```bash
cd backend

# 已安装依赖时直接启动；否则：
# pip install -r requirements.txt

export TSDB_BACKEND=sqlite
export DATABASE_URL=sqlite+aiosqlite:///./pvops.db

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

前端：

```bash
cd frontend
npm install
npm run build   # 或 npm run dev 进行热重载开发
```

## AI Copilot 与知识库

### 大模型配置

支持任何 OpenAI 兼容接口（OpenAI / DeepSeek / Kimi / Qwen / MiniMax 等）：

```bash
# .env 示例
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

未配置 API Key 时，AI 对话会返回友好提示，前端仍可正常交互。

### 知识库

- 上传入口：`POST /api/v1/kb/documents`（支持 txt / docx / pdf）
- 向量存储默认使用 PGVector（Docker Compose 环境），本地开发自动 fallback 到 SQLite 关键词检索
- 问答入口：`POST /api/v1/kb/ask` 或 `/api/v1/chat`

### AI Copilot 前端

- 全局右下角悬浮入口
- 电站详情页、告警中心、诊断报告页可一键带入上下文

## 数据采集

### 1. 协议适配

设备协议在 `backend/app/protocols/` 中配置：

- `simulator`：本地模拟数据，无设备时演示用
- `modbus_tcp`：Modbus TCP，支持可配置寄存器映射
- `modbus_rtu`：Modbus RTU（串口）

### 2. 边缘采集器

独立运行采集器：

```bash
cd pvops
PYTHONPATH=backend:. python3 scripts/collector.py --station-id 1 --interval 5
```

采集器特性：

- 按电站-设备配置轮询
- 失败数据写入本地 SQLite 队列，恢复后自动补发
- 支持逆变器、气象站、关口表设备类型

### 3. 模拟器（旧接口仍兼容）

```bash
cd simulator
PYTHONPATH=../backend:. python3 run_simulator.py \
  --base-url http://localhost:8000 \
  --station-id 1 --inverter-id INV001 --interval 5 --demo-mode
```

## 开发模式

前端热重载：

```bash
cd frontend
npm run dev
```

后端热重载：

```bash
cd backend
export TSDB_BACKEND=sqlite
export DATABASE_URL=sqlite+aiosqlite:///./pvops.db
python3 -m uvicorn app.main:app --reload
```

## 测试

```bash
# 后端单元测试（需要 pytest）
cd backend
pytest

# 本地 sanity 检查（不依赖 pytest）
cd ..
PYTHONPATH=backend:. python3 scripts/sanity_check.py

# 前端构建检查
cd frontend
npm run build
```

## 部署

```bash
cd deploy
./update.sh
```

详细说明见 [deploy/README.md](deploy/README.md)。

## 开发文档

- [实施总方案](docs/光伏运维智能体-实施总方案-终版.md)
- [MVP 差距与 Roadmap](docs/MVP功能差距与Roadmap.md)
- [部署说明](deploy/README.md)

## 开发流程

1. 从 `develop` 切出 `feature/xxx` 分支
2. 开发完成后提交 PR 到 `develop`
3. CI 通过 + Code Review 后合并
4. 每 2 周从 `develop` 合并到 `main` 发布版本

## 许可证

[待定]
