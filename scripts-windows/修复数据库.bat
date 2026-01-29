@echo off
chcp 65001 >nul
echo ========================================
echo 数据库修复工具
echo ========================================
echo.

cd /d "%~dp0\.."

if exist "python-portable\python.exe" (
    echo 使用便携版Python...
    python-portable\python.exe scripts\fix_database.py
) else if exist "venv\Scripts\python.exe" (
    echo 使用虚拟环境Python...
    venv\Scripts\python.exe scripts\fix_database.py
) else (
    echo 使用系统Python...
    python scripts\fix_database.py
)

echo.
echo 按任意键退出...
pause >nul
