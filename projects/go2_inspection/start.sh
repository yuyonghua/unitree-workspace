#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  Go2 巡检仿真系统"
echo "============================================"

ENV_NAME="go2-inspection"

# 检查conda环境
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到 conda"
    exit 1
fi

# 激活conda环境
echo "[1/3] 激活 conda 环境: ${ENV_NAME}"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ${ENV_NAME} || {
    echo "提示: 环境不存在，正在创建..."
    conda create -n ${ENV_NAME} python=3.10 -y
    conda activate ${ENV_NAME}
    pip install -r requirements.txt
}

# 检查依赖
echo "[2/3] 检查依赖..."
python -c "import mujoco" 2>/dev/null || {
    echo "提示: 正在安装依赖..."
    pip install -r requirements.txt
}

# 创建地图存储目录
echo "[3/3] 创建存储目录..."
mkdir -p storage/maps storage/exports

echo ""
echo "访问地址: http://localhost:8000"
echo "按 Ctrl+C 停止服务"
echo ""

python web/app.py
