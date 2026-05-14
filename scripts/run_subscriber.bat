@echo off
chcp 65001 >nul

REM 切换到项目根目录：scripts 的上一级
cd /d "%~dp0.."

if not exist ".\venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境：.\venv\Scripts\python.exe
    echo 请先在项目根目录创建 venv 并安装依赖。
    pause
    exit /b
)

if not exist ".\mqtt_subscriber.py" (
    echo [错误] 未找到文件：.\mqtt_subscriber.py
    pause
    exit /b
)

.\venv\Scripts\python.exe mqtt_subscriber.py

pause