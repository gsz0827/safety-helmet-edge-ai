@echo off
chcp 65001 >nul

REM 切换到项目根目录（scripts 的上一级）
cd /d "%~dp0.."

echo 当前目录：
cd

REM 检查虚拟环境
if not exist ".\venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境：.\venv\Scripts\python.exe
    echo 请先在项目根目录执行：
    echo python -m venv venv
    echo .\venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b
)

REM 检查 web_dashboard.py 是否存在
if not exist ".\web_dashboard.py" (
    echo [错误] 未找到文件：.\web_dashboard.py
    pause
    exit /b
)

REM 启动 Web 看板
.\venv\Scripts\python.exe web_dashboard.py

pause