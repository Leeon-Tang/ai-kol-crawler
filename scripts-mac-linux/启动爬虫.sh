#!/bin/bash

# AI KOL Crawler - Auto Start Script for Mac/Linux
# Requires Python 3.8+

set -e

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "  AI KOL爬虫系统 - 自动启动"
echo "  适用于 Mac/Linux"
echo "========================================"
echo ""

VENV_DIR="$SCRIPT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"

# ============================================
# Step 1: Check Python
# ============================================
echo "[步骤 1/5] 检查Python环境..."
echo ""

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "[错误] 未找到Python！"
    echo ""
    echo "请安装Python 3.8+:"
    echo "  Mac: brew install python3"
    echo "  Ubuntu: sudo apt-get install python3 python3-pip python3-venv"
    echo ""
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo "[OK] 已找到Python $PYTHON_VERSION"
echo ""

# ============================================
# Step 2: Create virtual environment
# ============================================
echo "[步骤 2/5] 配置虚拟环境..."
echo ""

if [ -f "$VENV_PYTHON" ]; then
    echo "[OK] 虚拟环境已存在"
else
    echo "正在创建虚拟环境..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    if [ ! -f "$VENV_PYTHON" ]; then
        echo "[错误] 虚拟环境创建失败！"
        exit 1
    fi
    
    echo "[OK] 虚拟环境创建完成"
fi

echo ""

# ============================================
# Step 3: Install dependencies
# ============================================
echo "[步骤 3/5] 安装依赖包..."
echo ""
echo "这可能需要几分钟..."
echo ""

source "$VENV_DIR/bin/activate"

pip install -r "$SCRIPT_DIR/requirements.txt" --quiet --disable-pip-version-check

if [ $? -ne 0 ]; then
    echo "[警告] 部分依赖包可能安装失败"
else
    echo "[OK] 所有依赖包安装完成"
fi

echo ""

# ============================================
# Step 4: Initialize directories and config
# ============================================
echo "[步骤 4/5] 初始化系统..."
echo ""

mkdir -p "$SCRIPT_DIR/data"
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/exports"
mkdir -p "$SCRIPT_DIR/config"

# 检查并创建配置文件
if [ ! -f "$SCRIPT_DIR/config/config.json" ]; then
    if [ -f "$SCRIPT_DIR/config/config.example.json" ]; then
        echo "正在创建配置文件..."
        cp "$SCRIPT_DIR/config/config.example.json" "$SCRIPT_DIR/config/config.json"
        echo "[OK] 配置文件已从示例创建"
    else
        echo "[错误] 未找到配置示例文件 config/config.example.json"
        exit 1
    fi
else
    echo "[OK] 配置文件已存在"
fi

echo "[OK] 系统初始化完成"
echo ""

# ============================================
# Step 5: Start the application
# ============================================
echo "[步骤 5/5] 启动Web界面..."
echo ""

# Find available port
PORT=8501
PORT_FOUND=0

while [ $PORT -le 8510 ]; do
    if ! lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PORT_FOUND=1
        break
    fi
    echo "[警告] 端口 $PORT 已被占用"
    PORT=$((PORT + 1))
done

if [ $PORT_FOUND -eq 0 ]; then
    echo ""
    echo "[错误] 未找到可用端口 (8501-8510)"
    echo ""
    echo "可能的解决方案:"
    echo "1. 关闭其他Streamlit应用"
    echo "2. 重启电脑"
    echo "3. 等待几分钟后重试"
    echo ""
    exit 1
fi

echo "========================================"
echo "  系统就绪！"
echo "  正在启动Web界面..."
echo "========================================"
echo ""
echo "浏览器将打开: http://localhost:$PORT"
echo ""
echo "请勿关闭此窗口！"
echo ""

cd "$SCRIPT_DIR"
python -m streamlit run app.py --server.port $PORT --server.headless false

if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 启动失败！"
    echo ""
    echo "可能的解决方案:"
    echo "1. 关闭占用8501-8510端口的应用"
    echo "2. 重启电脑"
    echo "3. 删除venv文件夹后重试"
    echo "4. 联系技术支持"
    echo ""
    read -p "按Enter键退出..."
fi
