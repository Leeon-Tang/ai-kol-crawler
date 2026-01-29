#!/bin/bash

echo "========================================"
echo "数据库修复工具"
echo "========================================"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 检测Python环境
if [ -f "venv/bin/python" ]; then
    echo "使用虚拟环境Python..."
    venv/bin/python scripts/fix_database.py
elif command -v python3 &> /dev/null; then
    echo "使用系统Python3..."
    python3 scripts/fix_database.py
elif command -v python &> /dev/null; then
    echo "使用系统Python..."
    python scripts/fix_database.py
else
    echo "错误: 未找到Python"
    exit 1
fi

echo ""
echo "按Enter键退出..."
read
