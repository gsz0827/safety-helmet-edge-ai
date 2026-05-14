# start_mobile_camera_ngrok.ps1
# 一键启动 Flask + ngrok 多手机摄像头采集

# 设置输出 UTF-8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001

# 激活虚拟环境
$venvPath = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "激活虚拟环境..."
    & $venvPath
} else {
    Write-Host "未找到虚拟环境，请先创建 venv"
    exit
}

# ----------------------------
# 启动 Flask 服务
# ----------------------------
Write-Host "`n启动 Flask 服务..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python web_mobile_camera.py"

Start-Sleep -Seconds 5  # 等待 Flask 服务启动

# ----------------------------
# 启动 ngrok
# ----------------------------
$ngrokExe = "ngrok"  # 如果 ngrok 在 PATH
# 如果 ngrok.exe 在本地路径，改成：$ngrokExe = 'C:\path\to\ngrok.exe'

Write-Host "`n启动 ngrok 公网隧道..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$ngrokExe http 5443"

Write-Host "`nngrok 启动完成，请查看 ngrok 控制台输出的 HTTPS 地址"
Write-Host "手机访问示例: https://xxxx-xxxx.ngrok-free.app/capture/cam_01"
Write-Host "或 https://xxxx-xxxx.ngrok-free.app/monitor 查看多摄像头监控"
Write-Host "`n双击此脚本即可启动 Flask + ngrok"