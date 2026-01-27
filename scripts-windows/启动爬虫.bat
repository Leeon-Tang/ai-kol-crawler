@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title AI KOL Crawler - Auto Start
color 0A

REM 切换到项目根目录
cd /d "%~dp0.."

echo.
echo ========================================
echo   AI KOL爬虫系统 - 自动启动
echo   无需安装Python
echo ========================================
echo.

REM Set variables
set PYTHON_VERSION=3.12.0
set PYTHON_DIR=%~dp0..\python-portable
set PYTHON_EXE=%PYTHON_DIR%\python.exe
set VENV_DIR=%~dp0..\venv
set VENV_PYTHON=%VENV_DIR%\Scripts\python.exe

REM ============================================
REM Step 1: Check or download portable Python
REM ============================================
echo [Step 1/5] Checking Python environment...
echo.

if exist "%PYTHON_EXE%" (
    echo [OK] Portable Python found
    goto :skip_python_download
)

echo [INFO] Portable Python not found
echo [INFO] Downloading Python %PYTHON_VERSION% portable version...
echo [INFO] First run may take a few minutes
echo.

REM Download Python embeddable
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set PYTHON_ZIP=%~dp0..\python.zip

echo Downloading from python.org...
powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_ZIP%' -UseBasicParsing } catch { exit 1 }"

if not exist "%PYTHON_ZIP%" (
    echo [ERROR] Download failed!
    echo.
    echo Please download manually:
    echo 1. Visit: https://www.python.org/downloads/
    echo 2. Download "Windows embeddable package (64-bit)"
    echo 3. Extract to: %PYTHON_DIR%
    echo.
    pause
    exit /b 1
)

echo [OK] Download completed
echo.

REM Extract Python
echo Extracting Python...
powershell -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"
del "%PYTHON_ZIP%" >nul 2>&1

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Extraction failed!
    pause
    exit /b 1
)

echo [OK] Python extracted successfully
echo.

REM Configure Python to enable pip
echo Configuring Python...
set PTH_FILE=%PYTHON_DIR%\python312._pth
if exist "%PTH_FILE%" (
    (
        echo python312.zip
        echo .
        echo import site
    ) > "%PTH_FILE%"
)

REM Download and install pip
echo Installing pip...
set GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py
set GET_PIP_FILE=%~dp0..\get-pip.py

powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GET_PIP_URL%' -OutFile '%GET_PIP_FILE%' -UseBasicParsing"
"%PYTHON_EXE%" "%GET_PIP_FILE%" --no-warn-script-location
del "%GET_PIP_FILE%" >nul 2>&1

echo [OK] Python configuration completed
echo.

:skip_python_download

REM ============================================
REM Step 2: Create virtual environment
REM ============================================
echo [Step 2/5] Configuring virtual environment...
echo.

if exist "%VENV_PYTHON%" (
    echo [OK] Virtual environment exists
    goto :skip_venv_create
)

echo Creating virtual environment...
"%PYTHON_EXE%" -m pip install virtualenv --quiet
"%PYTHON_EXE%" -m virtualenv "%VENV_DIR%" --quiet

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment creation failed!
    pause
    exit /b 1
)

echo [OK] Virtual environment created
echo.

:skip_venv_create

REM ============================================
REM Step 3: Install dependencies
REM ============================================
echo [Step 3/5] Installing dependencies...
echo.
echo This may take a few minutes...
echo.

"%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt --quiet --disable-pip-version-check

if errorlevel 1 (
    echo [WARNING] Some dependencies may have failed to install
) else (
    echo [OK] All dependencies installed
)
echo.

REM ============================================
REM Step 4: Initialize directories and config
REM ============================================
echo [Step 4/5] Initializing system...
echo.

if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports
if not exist "config" mkdir config

REM 检查并创建配置文件
if not exist "config\config.json" (
    if exist "config\config.example.json" (
        echo Creating config file...
        copy "config\config.example.json" "config\config.json" >nul
        echo [OK] Config file created from example
    ) else (
        echo [ERROR] Config example file not found: config\config.example.json
        pause
        exit /b 1
    )
) else (
    echo [OK] Config file exists
)

REM 检查并执行数据库迁移
echo [INFO] Checking database migration...
"%VENV_PYTHON%" -c "from storage.migrations.migration_v2 import migrate; migrate()"
if errorlevel 1 (
    echo [WARNING] Database migration check failed, but system will continue
) else (
    echo [OK] Database check completed
)

REM 检查并执行时区迁移
echo [INFO] Checking timezone migration...
"%VENV_PYTHON%" -c "from storage.migrations.migration_timezone import check_and_migrate_if_needed; check_and_migrate_if_needed(silent=False)"
if errorlevel 1 (
    echo [WARNING] Timezone migration check failed, but system will continue
) else (
    echo [OK] Timezone check completed
)
echo.

echo [OK] System initialization completed
echo.

REM ============================================
REM Step 5: Start the application
REM ============================================
echo [Step 5/5] Starting Web Interface...
echo.

REM Find available port
set PORT=8501
set PORT_FOUND=0

:check_port
netstat -ano | findstr "LISTENING" | findstr ":%PORT% " >nul 2>&1
if errorlevel 1 (
    set PORT_FOUND=1
    goto :port_found
)

echo [WARNING] Port %PORT% is already in use
set /a PORT+=1

if %PORT% gtr 8510 (
    echo.
    echo [ERROR] No available port found (8501-8510)
    echo.
    echo Possible solutions:
    echo 1. Close other Streamlit applications
    echo 2. Restart computer
    echo 3. Wait a few minutes and try again
    echo.
    pause
    exit /b 1
)

goto :check_port

:port_found
if %PORT_FOUND% equ 0 (
    echo [ERROR] Unable to find available port
    pause
    exit /b 1
)

echo ========================================
echo   System Ready!
echo   Starting Web Interface...
echo ========================================
echo.
echo Browser will open: http://localhost:%PORT%
echo.
echo Do NOT close this window!
echo.

REM Start Streamlit
"%VENV_PYTHON%" -m streamlit run app.py --server.port %PORT% --server.headless false

if errorlevel 1 (
    echo.
    echo [ERROR] Startup failed!
    echo.
    echo Possible solutions:
    echo 1. Close applications using ports 8501-8510
    echo 2. Restart computer
    echo 3. Delete python-portable and venv folders and try again
    echo 4. Contact technical support
    echo.
    pause
)
