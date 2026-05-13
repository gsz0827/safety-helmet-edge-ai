@echo off
chcp 65001 >nul
REM =====================================================
REM 一键启动 Web 看板 + ngrok，并自动打开公网 URL
REM =====================================================

REM -----------------------
REM 配置路径
REM -----------------------
set PROJECT_DIR=D:\edge_ai_projects\YOLOV8-safety-helmet-detection
set VENV_PY=%PROJECT_DIR%\venv\Scripts\python.exe
set NGROK_EXE=C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps\ngrok.exe
set NGROK_PORT=5000

REM -----------------------
REM 启动 Web 看板
REM -----------------------
echo 启动 Web 看板...
start "Web Dashboard" powershell -NoExit -Command "%VENV_PY% %PROJECT_DIR%\web_dashboard.py"

REM 等待 5 秒确保 Web 服务启动
timeout /t 5 /nobreak >nul

REM -----------------------
REM 启动 ngrok 并获取公网 URL
REM -----------------------
echo 启动 ngrok 公网隧道...
start "ngrok Tunnel" powershell -NoExit -Command ^
    "$ngrokProc = Start-Process -PassThru -FilePath '%NGROK_EXE%' -ArgumentList 'http %NGROK_PORT%' ;" ^
    "Start-Sleep -Seconds 3;" ^
    "$tunnels = Invoke-RestMethod http://127.0.0.1:4040/api/tunnels;" ^
    "$url = $tunnels.tunnels[0].public_url;" ^
    "Write-Host 'ngrok 公网访问地址: ' $url;" ^
    "Start-Process $url"

echo.
echo =====================================================
echo Web 看板和 ngrok 已启动完成！
echo 公网访问地址已自动在浏览器打开。
echo =====================================================
pause