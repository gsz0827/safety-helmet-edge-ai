@echo off
chcp 65001 >nul

REM =====================================================
REM 一键启动 Web 看板 + ngrok，并自动打开公网 URL
REM =====================================================

REM 切换到项目根目录：scripts 的上一级
cd /d "%~dp0.."

set "PROJECT_DIR=%CD%"
set "VENV_PY=%PROJECT_DIR%\venv\Scripts\python.exe"
set "NGROK_PORT=5000"

REM 优先使用系统 PATH 里的 ngrok
set "NGROK_EXE=ngrok"

REM 如果 WindowsApps 下存在 ngrok，则使用这个路径
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\ngrok.exe" (
    set "NGROK_EXE=%LOCALAPPDATA%\Microsoft\WindowsApps\ngrok.exe"
)

echo 当前项目目录：%PROJECT_DIR%
echo.

if not exist "%VENV_PY%" (
    echo [错误] 未找到虚拟环境：%VENV_PY%
    echo 请先在项目根目录执行：
    echo python -m venv venv
    echo .\venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b
)

if not exist "%PROJECT_DIR%\web_dashboard.py" (
    echo [错误] 未找到文件：%PROJECT_DIR%\web_dashboard.py
    pause
    exit /b
)

echo 启动 Web 看板...
start "Web Dashboard" cmd /k ""%VENV_PY%" "%PROJECT_DIR%\web_dashboard.py""

echo 等待 Web 服务启动...
timeout /t 5 /nobreak >nul

echo 启动 ngrok 公网隧道...
start "ngrok Tunnel" powershell -NoExit -ExecutionPolicy Bypass -Command "& { $ngrok='%NGROK_EXE%'; Start-Process -FilePath $ngrok -ArgumentList 'http %NGROK_PORT%'; Start-Sleep -Seconds 5; try { $tunnels = Invoke-RestMethod 'http://127.0.0.1:4040/api/tunnels'; $url = $tunnels.tunnels[0].public_url; Write-Host 'ngrok 公网访问地址:' $url; Start-Process $url } catch { Write-Host '未能自动获取 ngrok 地址，请确认 ngrok 已安装、已登录并正常启动。'; Write-Host $_ } }"

echo.
echo =====================================================
echo Web 看板和 ngrok 已启动。
echo 如果浏览器没有自动打开，请查看 ngrok 窗口里的 Forwarding 地址。
echo =====================================================

pause