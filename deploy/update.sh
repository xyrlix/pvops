#!/bin/bash
set -e

# 光伏运维智能体升级脚本

echo "=== PVOps 升级脚本 ==="

cd /opt/pvops || {
  echo "错误：未找到 /opt/pvops 目录"
  exit 1
}

echo "1. 拉取最新代码..."
git pull origin main

echo "2. 构建前端..."
cd frontend
npm install
npm run build
cd ..

echo "3. 构建镜像..."
cd deploy
docker compose build

echo "4. 停止旧服务..."
docker compose down

echo "5. 启动新服务..."
docker compose up -d

echo "6. 执行数据库迁移..."
docker compose exec backend alembic upgrade head

echo "7. 健康检查..."
sleep 5
curl -f http://localhost:8000/api/v1/health || {
  echo "错误：健康检查失败"
  exit 1
}

echo "=== 升级完成 ==="
