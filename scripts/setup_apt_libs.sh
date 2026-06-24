#!/bin/bash
set -e

# 下载并解压 Ubuntu 系统 Python 包到本地目录
# 用于在没有 pip/sudo 的环境中运行后端

TARGET_DIR="$(pwd)/backend/.apt-libs"
mkdir -p "$TARGET_DIR"

cd /tmp

PACKAGES=(
    python3-fastapi
    python3-uvicorn
    python3-sqlalchemy
    python3-pydantic
    python3-starlette
    python3-click
    python3-h11
    python3-httptools
    python3-uvloop
    python3-wsproto
    python3-anyio
    python3-sniffio
    python3-typing-extensions
    python3-greenlet
    python3-aiosqlite
    python3-jose
    python3-passlib
    python3-bcrypt
    python3-multipart
    python3-dotenv
    python3-tz
)

echo "正在下载系统 Python 包..."
for pkg in "${PACKAGES[@]}"; do
    if apt-cache search "^$pkg$" > /dev/null 2>&1; then
        echo "下载 $pkg..."
        apt-get download "$pkg" 2>&1 | tail -1 || true
    else
        echo "跳过 $pkg（不可用）"
    fi
done

echo "正在解压到 $TARGET_DIR..."
for deb in *.deb; do
    if [ -f "$deb" ]; then
        dpkg-deb -x "$deb" "$TARGET_DIR" 2>/dev/null || true
    fi
done

echo "完成"
