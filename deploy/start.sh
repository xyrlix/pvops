#!/usr/bin/env bash
# PVOps 一键启动脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 切换到项目根目录
cd "$PROJECT_DIR"

echo "🚀 PVOps 一键启动"

# 1. 检查 .env
if [ ! -f .env ]; then
  echo "📋 复制环境变量模板 .env.example -> .env"
  cp .env.example .env
  echo "⚠️  请根据实际环境编辑 .env 后再次运行本脚本"
  exit 1
fi

# 2. 构建前端（若未构建或源码有更新）
if [ ! -d "frontend/dist" ] || [ "frontend/package.json" -nt "frontend/dist" ]; then
  echo "🔧 构建前端..."
  (cd frontend && npm install && npm run build)
else
  echo "✅ 前端 dist 已存在，跳过构建（如需重新构建请删除 frontend/dist）"
fi

# 3. 启动核心服务
echo "🐳 启动 Docker Compose 核心服务..."
docker compose -f deploy/docker-compose.yml up -d

# 4. 等待 backend 健康
MAX_WAIT=60
WAITED=0
echo "⏳ 等待后端服务就绪..."
until curl -fsS http://localhost:8000/health > /dev/null 2>&1 || [ "$WAITED" -ge "$MAX_WAIT" ]; do
  sleep 2
  WAITED=$((WAITED + 2))
done

if [ "$WAITED" -ge "$MAX_WAIT" ]; then
  echo "❌ 后端未在 ${MAX_WAIT}s 内就绪，请查看日志："
  echo "   docker compose -f deploy/docker-compose.yml logs -f backend"
  exit 1
fi

echo ""
echo "🎉 PVOps 启动成功！"
echo "   Web UI:    http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   查看日志:  docker compose -f deploy/docker-compose.yml logs -f backend"
