@echo off
chcp 65001 >nul 2>&1
title 数据库迁移和修复工具
color 0B

cd /d "%~dp0.."

echo.
echo ========================================
echo   数据库迁移和修复工具
echo ========================================
echo.

set VENV_PYTHON=%~dp0..\venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo [错误] 虚拟环境不存在
    echo 请先运行 "启动爬虫.bat" 初始化系统
    echo.
    pause
    exit /b 1
)

echo [Step 1/3] 执行数据库结构迁移...
echo.
"%VENV_PYTHON%" scripts\migrate_database.py
echo.

echo [Step 2/3] 执行时区迁移...
echo.
"%VENV_PYTHON%" -c "import sys; sys.path.insert(0, 'backend'); from storage.migrations.migration_timezone import check_and_migrate_if_needed; check_and_migrate_if_needed(silent=False)"
echo.

echo [Step 3/3] 验证数据库...
echo.
"%VENV_PYTHON%" -c "import sys; sys.path.insert(0, 'backend'); from storage.database import Database; db = Database(); db.connect(); print('[OK] 数据库连接成功'); db.close()"
echo.

echo ========================================
echo   数据库迁移和修复完成！
echo ========================================
echo.
pause
