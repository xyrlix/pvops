#!/usr/bin/env bash
# PVOps 一键停止脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🛑 正在停止 PVOps 服务..."
docker compose -f deploy/docker-compose.yml down "$@"
echo "✅ PVOps 已停止"
