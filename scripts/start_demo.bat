@echo off
REM 切换到批处理文件所在目录（项目根目录）
cd /d %~dp0

start "MQTT Subscriber" cmd /k ".\venv\Scripts\python.exe mqtt_subscriber.py"

timeout /t 3

start "Web Dashboard" cmd /k ".\venv\Scripts\python.exe web_dashboard.py"

timeout /t 3

start "Helmet Alarm System" cmd /k ".\venv\Scripts\python.exe run_onnx_alarm.py"