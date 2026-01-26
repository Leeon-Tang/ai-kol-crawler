#!/bin/bash

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Daily Data Backup"
echo "========================================"
echo ""

# 检查并创建配置文件（如果不存在）
if [ ! -f "config/config.json" ]; then
    if [ -f "config/config.example.json" ]; then
        echo "Creating config file..."
        mkdir -p config
        cp "config/config.example.json" "config/config.json"
        echo "[OK] Config file created"
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
echo "Backing up..."
echo ""
$PYTHON_EXE scripts/backup_daily.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Backup failed"
    exit 1
fi

echo ""
echo "========================================"
echo "  Backup completed!"
echo "  Location: backups/current_date/"
echo "========================================"
echo ""
