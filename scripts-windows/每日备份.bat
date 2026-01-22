@echo off
chcp 65001 >nul

REM 切换到项目根目录
cd /d "%~dp0.."

echo ========================================
echo   每日数据备份
echo ========================================
echo.

REM 检查并创建配置文件（如果不存在）
if not exist "config\config.json" (
    if exist "config\config.example.json" (
        echo 正在创建配置文件...
        if not exist "config" mkdir config
        copy "config\config.example.json" "config\config.json" >nul
        echo [OK] 配置文件已创建
        echo.
    )
)

REM 检查虚拟环境
if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
) else if exist "python-portable\python.exe" (
    set PYTHON_EXE=python-portable\python.exe
) else (
    set PYTHON_EXE=python
)

REM 执行备份
echo 正在备份...
echo.
"%PYTHON_EXE%" backup_daily.py

if errorlevel 1 (
    echo.
    echo [错误] 备份失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo   备份完成！
echo   位置: backups\当前日期\
echo ========================================
echo.
pause
