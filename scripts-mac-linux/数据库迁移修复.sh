#!/bin/bash

# Database Migration and Fix Script for Mac/Linux
# 数据库迁移和修复脚本

set -e

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "  数据库迁移和修复工具"
echo "========================================"
echo ""

VENV_DIR="$SCRIPT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"

# 检查虚拟环境
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] 虚拟环境不存在！"
    echo "请先运行启动脚本创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

echo "[Step 1/3] 执行数据库结构迁移..."
echo ""
python scripts/migrate_database.py
echo ""

echo "[Step 2/3] 执行时区迁移..."
echo ""
python -c "import sys; sys.path.insert(0, 'backend'); from storage.migrations.migration_timezone import check_and_migrate_if_needed; check_and_migrate_if_needed(silent=False)"
echo ""

echo "[Step 3/3] 验证数据库..."
echo ""
python -c "import sys; sys.path.insert(0, 'backend'); from storage.database import Database; db = Database(); db.connect(); print('[OK] 数据库连接成功'); db.close()"
echo ""

echo "========================================"
echo "  数据库迁移和修复完成！"
echo "========================================"
echo ""
read -p "按 Enter 键退出..."
