#!/bin/bash
# ASAR 打包/解包工具 - 一键启动脚本
# 用法: ./run_asar_gui.sh [不透明度]
# 示例: ./run_asar_gui.sh 0.85

cd "$(dirname "$0")"
OPACITY=${1:-0.9}
echo "正在启动 ASAR 打包/解包工具 (不透明度: $OPACITY)..."
python3 asar_gui.py -o "$OPACITY"
