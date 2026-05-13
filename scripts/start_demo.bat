@echo off
cd /d D:\edge_ai_projects\YOLOV8-safety-helmet-detection

start "MQTT Subscriber" cmd /k ".\venv\Scripts\python.exe mqtt_subscriber.py"

timeout /t 3

start "Web Dashboard" cmd /k ".\venv\Scripts\python.exe web_dashboard.py"

timeout /t 3

start "Helmet Alarm System" cmd /k ".\venv\Scripts\python.exe run_onnx_alarm.py"