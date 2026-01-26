@echo off
chcp 65001 >nul

REM 保存当前目录并切换到项目根目录
pushd "%~dp0.."

echo ========================================
echo   Daily Data Backup
echo ========================================
echo.

REM 检查并创建配置文件（如果不存在）
if not exist "config\config.json" (
    if exist "config\config.example.json" (
        echo Creating config file...
        if not exist "config" mkdir config
        copy "config\config.example.json" "config\config.json" >nul
        echo [OK] Config file created
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
echo Backing up...
echo.
"%PYTHON_EXE%" scripts\backup_daily.py

if errorlevel 1 (
    echo.
    echo [ERROR] Backup failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Backup completed!
echo   Location: backups\current_date\
echo ========================================
echo.

REM 恢复原始目录
popd
pause
