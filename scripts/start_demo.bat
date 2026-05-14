@echo off
chcp 65001 >nul

REM 切换到项目根目录：scripts 的上一级
cd /d "%~dp0.."

echo 当前目录：
cd

if not exist ".\venv\Scripts\python.exe" (
    echo.
    echo [错误] 没找到虚拟环境：.\venv\Scripts\python.exe
    echo 请先在项目根目录执行：
    echo python -m venv venv
    echo .\venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b
)

start "MQTT Subscriber" cmd /k ".\venv\Scripts\python.exe mqtt_subscriber.py"

timeout /t 3 /nobreak

start "Web Dashboard" cmd /k ".\venv\Scripts\python.exe web_dashboard.py"

timeout /t 3 /nobreak

start "Helmet Alarm System" cmd /k ".\venv\Scripts\python.exe run_onnx_alarm.py"

echo.
echo 已启动 MQTT Subscriber、Web Dashboard、Helmet Alarm System
pause