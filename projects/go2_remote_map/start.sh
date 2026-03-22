#!/bin/bash
# Go2 远程遥控与建图系统 - 启动脚本
# 用法:
#   ./start.sh                           # 默认 Remote 模式 (使用 config.py 凭据)
#   ./start.sh --mode localsta --ip 10.114.97.227
#   ./start.sh --mode remote --serial B42N6000Q1496588 --user xx@xx.com --pass xxx

cd "$(dirname "$0")"

# 确保 data 目录存在
mkdir -p data

echo "========================================="
echo "  Go2 远程遥控与建图系统"
echo "========================================="
echo ""

exec python app.py "$@"
