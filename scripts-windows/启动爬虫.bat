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
echo [步骤 1/5] 检查Python环境...
echo.

if exist "%PYTHON_EXE%" (
    echo [OK] 已找到便携式Python
    goto :skip_python_download
)

echo [信息] 未找到便携式Python
echo [信息] 正在下载Python %PYTHON_VERSION% 便携版...
echo [信息] 首次运行需要几分钟
echo.

REM Download Python embeddable
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set PYTHON_ZIP=%~dp0..\python.zip

echo 正在从python.org下载...
powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_ZIP%' -UseBasicParsing } catch { exit 1 }"

if not exist "%PYTHON_ZIP%" (
    echo [错误] 下载失败！
    echo.
    echo 请手动下载：
    echo 1. 访问: https://www.python.org/downloads/
    echo 2. 下载 "Windows embeddable package (64-bit)"
    echo 3. 解压到: %PYTHON_DIR%
    echo.
    pause
    exit /b 1
)

echo [OK] 下载完成
echo.

REM Extract Python
echo 正在解压Python...
powershell -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"
del "%PYTHON_ZIP%" >nul 2>&1

if not exist "%PYTHON_EXE%" (
    echo [错误] 解压失败！
    pause
    exit /b 1
)

echo [OK] Python解压成功
echo.

REM Configure Python to enable pip
echo 正在配置Python...
set PTH_FILE=%PYTHON_DIR%\python312._pth
if exist "%PTH_FILE%" (
    (
        echo python312.zip
        echo .
        echo import site
    ) > "%PTH_FILE%"
)

REM Download and install pip
echo 正在安装pip...
set GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py
set GET_PIP_FILE=%~dp0..\get-pip.py

powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GET_PIP_URL%' -OutFile '%GET_PIP_FILE%' -UseBasicParsing"
"%PYTHON_EXE%" "%GET_PIP_FILE%" --no-warn-script-location
del "%GET_PIP_FILE%" >nul 2>&1

echo [OK] Python配置完成
echo.

:skip_python_download

REM ============================================
REM Step 2: Create virtual environment
REM ============================================
echo [步骤 2/5] 配置虚拟环境...
echo.

if exist "%VENV_PYTHON%" (
    echo [OK] 虚拟环境已存在
    goto :skip_venv_create
)

echo 正在创建虚拟环境...
"%PYTHON_EXE%" -m pip install virtualenv --quiet
"%PYTHON_EXE%" -m virtualenv "%VENV_DIR%" --quiet

if not exist "%VENV_PYTHON%" (
    echo [错误] 虚拟环境创建失败！
    pause
    exit /b 1
)

echo [OK] 虚拟环境创建完成
echo.

:skip_venv_create

REM ============================================
REM Step 3: Install dependencies
REM ============================================
echo [步骤 3/5] 安装依赖包...
echo.
echo 这可能需要几分钟...
echo.

"%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt --quiet --disable-pip-version-check

if errorlevel 1 (
    echo [警告] 部分依赖包可能安装失败
) else (
    echo [OK] 所有依赖包安装完成
)
echo.

REM ============================================
REM Step 4: Initialize directories
REM ============================================
echo [步骤 4/5] 初始化系统...
echo.

if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports

echo [OK] 目录准备完成
echo.

REM ============================================
REM Step 5: Start the application
REM ============================================
echo [步骤 5/5] 启动Web界面...
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

echo [警告] 端口 %PORT% 已被占用
set /a PORT+=1

if %PORT% gtr 8510 (
    echo.
    echo [错误] 未找到可用端口 (8501-8510)
    echo.
    echo 可能的解决方案:
    echo 1. 关闭其他Streamlit应用
    echo 2. 重启电脑
    echo 3. 等待几分钟后重试
    echo.
    pause
    exit /b 1
)

goto :check_port

:port_found
if %PORT_FOUND% equ 0 (
    echo [错误] 无法找到可用端口
    pause
    exit /b 1
)

echo ========================================
echo   系统就绪！
echo   正在启动Web界面...
echo ========================================
echo.
echo 浏览器将打开: http://localhost:%PORT%
echo.
echo 请勿关闭此窗口！
echo.

REM Start Streamlit
"%VENV_PYTHON%" -m streamlit run app.py --server.port %PORT% --server.headless false

if errorlevel 1 (
    echo.
    echo [错误] 启动失败！
    echo.
    echo 可能的解决方案:
    echo 1. 关闭占用8501-8510端口的应用
    echo 2. 重启电脑
    echo 3. 删除python-portable和venv文件夹后重试
    echo 4. 联系技术支持
    echo.
    pause
)
