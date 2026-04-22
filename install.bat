@echo off
chcp 65001 >nul
echo ========================================
echo ICP 备案查询 API - 依赖安装脚本
echo ========================================
echo.

echo [1/2] 检查 Python 版本...
python --version
if errorlevel 1 (
    echo [错误] Python 未安装或未添加到 PATH
    echo 请先安装 Python 3.9 或更高版本
    pause
    exit /b 1
)
echo.

echo [2/2] 安装依赖...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败！
    echo 请检查网络连接或手动执行安装命令:
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 下一步：
echo 1. 启动服务: python web.py
echo 2. 或运行启动脚本: run.bat
echo.
pause