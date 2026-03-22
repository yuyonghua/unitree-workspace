#!/bin/bash
# Go2 巡检仿真系统 - 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  Go2 巡检仿真系统"
echo "============================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查依赖
echo "[1/3] 检查依赖..."
python3 -c "import mujoco" 2>/dev/null || {
    echo "提示: 正在安装依赖..."
    pip3 install -r requirements.txt
}

# 创建地图存储目录
echo "[2/3] 创建存储目录..."
mkdir -p storage/maps storage/exports

# 启动服务
echo "[3/3] 启动Web服务..."
echo ""
echo "访问地址: http://localhost:8000"
echo "按 Ctrl+C 停止服务"
echo ""

python3 web/app.py
