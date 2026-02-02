@echo off
chcp 65001 >nul
echo ========================================
echo 安装 MCP Server 依赖
echo ========================================
echo.

echo [1/2] 安装 Python 依赖...
pip install mcp>=0.9.0 playwright>=1.40.0
if %errorlevel% neq 0 (
    echo 错误：依赖安装失败
    pause
    exit /b 1
)

echo.
echo [2/2] 创建截图目录...
if not exist screenshots mkdir screenshots

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo MCP Server 使用系统 Edge 浏览器，无需下载 Chromium
echo.
echo 配置文件已创建：.kiro/settings/mcp.json
echo 重启 Kiro 即可使用
echo.
pause
