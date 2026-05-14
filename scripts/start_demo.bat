@echo off
cd /d %~dp0\..

echo ========================================
echo 安全帽违规检测看板启动中...
echo ========================================
echo.

echo 正在启动 Web Dashboard + ONNX 检测服务...
echo 看板启动后会自动打开浏览器。
echo.

.\venv\Scripts\python.exe web_dashboard.py

pause