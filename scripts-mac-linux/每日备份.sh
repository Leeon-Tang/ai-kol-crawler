#!/bin/bash

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  每日数据备份"
echo "========================================"
echo ""

# 检查并创建配置文件（如果不存在）
if [ ! -f "config/config.json" ]; then
    if [ -f "config/config.example.json" ]; then
        echo "正在创建配置文件..."
        mkdir -p config
        cp "config/config.example.json" "config/config.json"
        echo "[OK] 配置文件已创建"
        echo ""
    fi
fi

# 检查Python
if [ -f "venv/bin/python" ]; then
    PYTHON_EXE="venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_EXE="python3"
else
    PYTHON_EXE="python"
fi

# 执行备份
echo "正在备份..."
echo ""
$PYTHON_EXE backup_daily.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 备份失败"
    exit 1
fi

echo ""
echo "========================================"
echo "  备份完成！"
echo "  位置: backups/当前日期/"
echo "========================================"
echo ""
