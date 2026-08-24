#!/bin/bash
# ============================================================
# 西班牙语背单词 App —— macOS 一键启动脚本
# 双击即可：建虚拟环境 → 装依赖 → 找空闲端口 → 打开浏览器 → 启动服务
# ============================================================

cd "$(dirname "$0")"

# ---------- 检测 python3 ----------
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 python3，请先安装 Python 3.9+。"
    echo "   推荐：brew install python3"
    read -p "按回车退出..."
    exit 1
fi

# ---------- 创建虚拟环境 ----------
if [ ! -d ".venv" ]; then
    echo "📦 首次运行，正在创建虚拟环境..."
    python3 -m venv .venv
fi

# ---------- 激活虚拟环境 ----------
source .venv/bin/activate

# ---------- 安装依赖 ----------
pip install --upgrade pip -q
pip install -r requirements.txt -q

# ---------- 寻找空闲端口（从 8000 起） ----------
PORT=8000
while lsof -i :$PORT &> /dev/null; do
    PORT=$((PORT + 1))
done
echo "🚀 启动服务：http://localhost:$PORT"

# ---------- 打开浏览器 ----------
open "http://localhost:$PORT"

# ---------- 启动 uvicorn ----------
python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
