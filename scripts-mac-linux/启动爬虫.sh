#!/bin/bash

# AI KOL Crawler - Auto Start Script for Mac/Linux
# Requires Python 3.8+

set -e

# 切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "  AI KOL Crawler System - Auto Start"
echo "  For Mac/Linux"
echo "========================================"
echo ""

VENV_DIR="$SCRIPT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"

# ============================================
# Step 1: Check Python
# ============================================
echo "[Step 1/5] Checking Python environment..."
echo ""

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python not found!"
    echo ""
    echo "Please install Python 3.8+:"
    echo "  Mac: brew install python3"
    echo "  Ubuntu: sudo apt-get install python3 python3-pip python3-venv"
    echo ""
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo "[OK] Python $PYTHON_VERSION found"
echo ""

# ============================================
# Step 2: Create virtual environment
# ============================================
echo "[Step 2/5] Configuring virtual environment..."
echo ""

if [ -f "$VENV_PYTHON" ]; then
    echo "[OK] Virtual environment exists"
else
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    if [ ! -f "$VENV_PYTHON" ]; then
        echo "[ERROR] Virtual environment creation failed!"
        exit 1
    fi
    
    echo "[OK] Virtual environment created"
fi

echo ""

# ============================================
# Step 3: Install dependencies
# ============================================
echo "[Step 3/5] Installing dependencies..."
echo ""
echo "This may take a few minutes..."
echo ""

source "$VENV_DIR/bin/activate"

pip install -r "$SCRIPT_DIR/requirements.txt" --quiet --disable-pip-version-check

if [ $? -ne 0 ]; then
    echo "[WARNING] Some dependencies may have failed to install"
else
    echo "[OK] All dependencies installed"
fi

echo ""

# ============================================
# Step 4: Initialize directories and config
# ============================================
echo "[Step 4/5] Initializing system..."
echo ""

mkdir -p "$SCRIPT_DIR/data"
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/exports"
mkdir -p "$SCRIPT_DIR/config"

# 检查并创建配置文件
if [ ! -f "$SCRIPT_DIR/config/config.json" ]; then
    if [ -f "$SCRIPT_DIR/config/config.example.json" ]; then
        echo "Creating config file..."
        cp "$SCRIPT_DIR/config/config.example.json" "$SCRIPT_DIR/config/config.json"
        echo "[OK] Config file created from example"
    else
        echo "[ERROR] Config example file not found: config/config.example.json"
        exit 1
    fi
else
    echo "[OK] Config file exists"
fi

# 检查并执行数据库迁移
echo "[INFO] Checking database migration..."
python -c "from storage.migrations.migration_v2 import migrate; migrate()"
if [ $? -ne 0 ]; then
    echo "[WARNING] Database migration check failed, but system will continue"
else
    echo "[OK] Database check completed"
fi
echo ""

echo "[OK] System initialization completed"
echo ""

# ============================================
# Step 5: Start the application
# ============================================
echo "[Step 5/5] Starting Web Interface..."
echo ""

# Find available port
PORT=8501
PORT_FOUND=0

while [ $PORT -le 8510 ]; do
    if ! lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PORT_FOUND=1
        break
    fi
    echo "[WARNING] Port $PORT is already in use"
    PORT=$((PORT + 1))
done

if [ $PORT_FOUND -eq 0 ]; then
    echo ""
    echo "[ERROR] No available port found (8501-8510)"
    echo ""
    echo "Possible solutions:"
    echo "1. Close other Streamlit applications"
    echo "2. Restart computer"
    echo "3. Wait a few minutes and try again"
    echo ""
    exit 1
fi

echo "========================================"
echo "  System Ready!"
echo "  Starting Web Interface..."
echo "========================================"
echo ""
echo "Browser will open: http://localhost:$PORT"
echo ""
echo "Do NOT close this window!"
echo ""

cd "$SCRIPT_DIR"
python -m streamlit run app.py --server.port $PORT --server.headless false

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Startup failed!"
    echo ""
    echo "Possible solutions:"
    echo "1. Close applications using ports 8501-8510"
    echo "2. Restart computer"
    echo "3. Delete venv folder and try again"
    echo "4. Contact technical support"
    echo ""
    read -p "Press Enter to exit..."
fi
