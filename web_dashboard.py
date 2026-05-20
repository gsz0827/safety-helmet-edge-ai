import os
import csv
import io
import socket
import threading
import webbrowser
import base64
import time

import cv2
import numpy as np

from flask import (
    Flask,
    send_from_directory,
    render_template_string,
    request,
    redirect,
    url_for,
    Response,
    jsonify,
    stream_with_context,
)

from edge.config_loader import load_config
from edge.alarm_database import AlarmDatabase
from edge.onnx_detector import OnnxDetector
from edge.alarm_manager import AlarmManager
from edge.mqtt_publisher import MqttPublisher


config = load_config("config.yaml")

ALARM_DIR = config["alarm"]["alarm_dir"]
DASHBOARD_HOST = config.get("dashboard", {}).get("host", "127.0.0.1")
DASHBOARD_PORT = config.get("dashboard", {}).get("port", 5000)
DASHBOARD_AUTO_REFRESH_SECONDS = config.get("dashboard", {}).get("auto_refresh_seconds", 5)

alarm_database = AlarmDatabase(config)

detector = OnnxDetector(config)
mqtt_publisher = MqttPublisher(config)
alarm_manager = AlarmManager(config, mqtt_publisher, alarm_database)

detect_lock = threading.Lock()

app = Flask(__name__)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>安全帽违规告警看板</title>

    <style>
        body {
            font-family: Arial, "Microsoft YaHei", sans-serif;
            margin: 30px;
            background: #f5f6fa;
            color: #222;
        }

        h1 {
            margin-bottom: 10px;
        }

        .top-dashboard {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 480px;
            gap: 18px;
            margin: 20px 0;
            align-items: stretch;
        }

        .left-dashboard {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 16px;
            min-width: 0;
            height: 100%;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(4, minmax(130px, 1fr));
            gap: 16px;
            margin: 0;
            align-content: start;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 18px;
            min-height: 96px;
            box-sizing: border-box;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .card-title {
            color: #666;
            font-size: 14px;
            margin-bottom: 8px;
        }

        .card-value {
            font-size: 24px;
            font-weight: bold;
        }

        .total-card {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 120px;
        }

        .total-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
        }

        .mini-trend-title {
            margin-top: 12px;
            padding-top: 8px;
            border-top: 1px solid #f0f0f0;
            color: #666;
            font-size: 12px;
        }

        .mini-trend {
            height: 38px;
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            align-items: end;
            gap: 4px;
            margin-top: 6px;
        }

        .mini-bar-item {
            height: 100%;
            display: flex;
            align-items: end;
            justify-content: center;
        }

        .mini-bar {
            width: 8px;
            min-height: 4px;
            border-radius: 999px 999px 0 0;
            background: #1677ff;
        }

        .chart-box {
            background: white;
            border-radius: 12px;
            padding: 18px 22px;
            margin: 0;
            box-sizing: border-box;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .chart-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 12px;
        }

        .bar-chart {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            align-items: end;
            gap: 6px;
            height: 105px;
            border-bottom: 1px solid #ddd;
            padding: 10px 4px 0 4px;
        }

        .bar-item {
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
        }

        .bar {
            width: 22px;
            min-height: 4px;
            background: #1677ff;
            border-radius: 6px 6px 0 0;
        }

        .bar-count {
            font-size: 13px;
            margin-bottom: 6px;
            color: #333;
        }

        .bar-date {
            font-size: 12px;
            color: #666;
            margin-top: 6px;
        }

        .filter-box {
            background: white;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            align-self: stretch;
        }

        .filter-form {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .filter-item {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
        }

        .filter-item label {
            color: #333;
            font-size: 14px;
        }

        .filter-item input,
        .filter-item select {
            height: 34px;
            padding: 6px 10px;
            border: 1px solid #dcdfe6;
            border-radius: 8px;
            box-sizing: border-box;
            background: white;
            font-size: 14px;
        }

        .filter-item select[name="event"] {
            width: 82px;
        }

        .filter-item input[name="model_type"] {
            width: 145px;
        }

        .filter-item input[name="min_conf"] {
            width: 78px;
        }

        .filter-item input[name="limit"] {
            width: 70px;
        }

        .filter-item select[name="status"] {
            width: 82px;
        }

        .filter-actions {
            margin-left: auto;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            white-space: nowrap;
        }

        .filter-button {
            height: 34px;
            padding: 0 16px;
            border: none;
            border-radius: 8px;
            background: #1677ff;
            color: white;
            cursor: pointer;
            font-size: 14px;
        }

        .filter-link {
            height: 34px;
            padding: 0 10px;
            border-radius: 8px;
            color: #1677ff;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            font-size: 14px;
        }

        .filter-link:hover {
            background: #f0f6ff;
        }

        .filter-export {
            background: #f0f6ff;
        }

        .camera-card {
            margin: 24px 0;
            padding: 18px;
            border-radius: 12px;
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .camera-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            flex-wrap: nowrap;
        }

        .camera-title {
            font-size: 16px;
            font-weight: bold;
            white-space: nowrap;
            flex-shrink: 0;
        }

        .camera-actions {
            display: flex;
            gap: 6px;
            flex-wrap: nowrap;
            justify-content: flex-end;
            min-width: 0;
        }

        .camera-actions button {
            padding: 7px 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            background: #1677ff;
            color: white;
            font-size: 13px;
            white-space: nowrap;
        }

        .camera-actions button.secondary {
            background: #666;
        }

        .camera-status {
            margin-bottom: 12px;
            color: #555;
            font-size: 14px;
        }

        .camera-status:empty {
            display: none;
        }

        .camera-status.ok {
            color: #15803d;
            font-weight: bold;
        }

        .camera-status.error {
            color: #d93025;
            font-weight: bold;
        }

        .camera-preview-wrap {
            width: 100%;
            max-width: 900px;
            min-height: 220px;
            border-radius: 12px;
            background: #111827;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            color: #d1d5db;
        }

        .camera-video-layer {
            position: relative;
            display: none;
            width: 100%;
        }

        #cameraPreview {
            width: 100%;
            max-height: 520px;
            background: #111827;
            display: block;
        }

        #detectCanvas {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }

        #cameraPlaceholder {
            padding: 24px;
            text-align: center;
            color: #d1d5db;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        th, td {
            padding: 12px;
            border-bottom: 1px solid #eee;
            text-align: left;
            vertical-align: middle;
        }

        th {
            background: #20232a;
            color: white;
            font-weight: normal;
        }

        tr:hover {
            background: #fafafa;
        }

        a {
            color: #1677ff;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        .status-pending {
            color: #ff4d4f;
            font-weight: bold;
        }

        .status-handled {
            color: #52c41a;
            font-weight: bold;
        }

        .latest-badge {
            display: inline-block;
            margin-left: 6px;
            padding: 2px 6px;
            border-radius: 999px;
            background: #ff4d4f;
            color: white;
            font-size: 12px;
        }

        .thumb {
            max-width: 220px;
            max-height: 140px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }

        .action-form {
            display: inline-block;
            margin: 0;
        }

        .action-input {
            width: 100px;
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 6px;
        }

        .action-button {
            padding: 6px 10px;
            border: none;
            border-radius: 6px;
            background: #1677ff;
            color: white;
            cursor: pointer;
        }

        .action-button-secondary {
            background: #666;
        }

        .empty {
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }


        .overview-layout {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 460px;
            grid-template-rows: auto auto;
            gap: 18px;
            margin: 20px 0 24px 0;
            align-items: stretch;
        }

        .overview-left-top {
            grid-column: 1;
            grid-row: 1;
        }

        .overview-left-bottom {
            grid-column: 1;
            grid-row: 2;
        }

        .overview-chart {
            display: none;
        }

        .overview-camera {
            grid-column: 2;
            grid-row: 1 / span 2;
            margin: 0;
            padding: 16px;
            display: flex;
            flex-direction: column;
        }

        .overview-camera .camera-preview-wrap {
            width: 100%;
            max-width: 100%;
            min-height: 260px;
            flex: 1;
        }

        .overview-camera #cameraPreview {
            width: 100%;
            max-height: 420px;
        }

        #alarmTableContent {
            margin-top: 18px;
        }

        @media (max-width: 1500px) {
            .overview-layout {
                grid-template-columns: 1fr;
                grid-template-rows: auto;
            }

            .overview-left-top,
            .overview-left-bottom,
            .overview-chart,
            .overview-camera {
                grid-column: 1;
                grid-row: auto;
            }

            .cards {
                grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            }
        }

        @media (max-width: 900px) {
            body {
                margin: 16px;
            }

            .cards {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .filter-form {
                align-items: stretch;
            }

            .filter-actions {
                margin-left: 0;
            }
        }
    </style>
</head>

<body>
    <h1>安全帽违规告警看板</h1>
    <div class="overview-layout">
        <div id="dashboardContent" style="display: contents;">
        <div class="overview-left-top">
            <div class="cards">
                <div class="card total-card">
                    <div class="total-card-header">
                        <div>
                            <div class="card-title">告警总数</div>
                            <div class="card-value">{{ summary.total_count }}</div>
                        </div>
                    </div>

                    <div class="mini-trend-title">最近7天趋势</div>

                    <div class="mini-trend">
                        {% for item in daily_counts %}
                        <div class="mini-bar-item" title="{{ item.date }}：{{ item.count }}">
                            <div class="mini-bar" style="height: {{ (item.count / max_daily_count * 34) | int + 4 }}px;"></div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">今日告警</div>
                    <div class="card-value">{{ summary.today_count }}</div>
                </div>

                <div class="card">
                    <div class="card-title">最新告警时间</div>
                    <div class="card-value" style="font-size:16px;">{{ summary.latest_time }}</div>
                </div>

                <div class="card">
                    <div class="card-title">未处理告警</div>
                    <div class="card-value">{{ summary.pending_count }}</div>
                </div>
            </div>
        </div>

        <div class="overview-left-bottom">
            <div class="filter-box">
                <form method="get" class="filter-form">
                    <div class="filter-item">
                        <label>事件：</label>
                        <select name="event">
                            <option value="" {% if not filters.event %}selected{% endif %}>全部</option>
                            <option value="no_helmet" {% if filters.event == "no_helmet" %}selected{% endif %}>no_helmet</option>
                        </select>
                    </div>

                    <div class="filter-item">
                        <label>模型类型：</label>
                        <input type="text" name="model_type" value="{{ filters.model_type }}" placeholder="onnxruntime_modular">
                    </div>

                    <div class="filter-item">
                        <label>最低置信度：</label>
                        <input type="text" name="min_conf" value="{{ filters.min_conf }}" placeholder="0.5">
                    </div>

                    <div class="filter-item">
                        <label>显示条数：</label>
                        <input type="number" name="limit" value="{{ filters.limit }}" min="1" max="500">
                    </div>

                    <div class="filter-item">
                        <label>状态：</label>
                        <select name="status">
                            <option value="" {% if not filters.status %}selected{% endif %}>全部</option>
                            <option value="pending" {% if filters.status == "pending" %}selected{% endif %}>未处理</option>
                            <option value="handled" {% if filters.status == "handled" %}selected{% endif %}>已处理</option>
                        </select>
                    </div>

                    <div class="filter-actions">
                        <button type="submit" class="filter-button">筛选</button>
                        <a class="filter-link" href="/">重置</a>
                        <a class="filter-link filter-export" href="{{ export_url }}">导出CSV</a>
                    </div>
                </form>
            </div>
        </div>
        </div>

    <section class="camera-card overview-camera">
        <div class="camera-header">
            <div class="camera-title">实时画面采集</div>

            <div class="camera-actions">
                <button type="button" onclick="openCamera()">打开摄像头</button>
                <button type="button" onclick="switchCamera()">切换摄像头</button>
                <button type="button" class="secondary" onclick="closeCamera()">关闭摄像头</button>
            </div>
        </div>

        <div id="cameraStatus" class="camera-status"></div>

        <div id="detectStatus" class="camera-status"></div>

        <div class="camera-preview-wrap">
            <div id="cameraPlaceholder">
                当前没有摄像头画面。
            </div>

            <div class="camera-video-layer">
                <video id="cameraPreview" autoplay playsinline muted></video>
                <canvas id="detectCanvas"></canvas>
            </div>
        </div>
    </section>
    </div>

    <div id="alarmTableContent">
    {% if alarms %}
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>时间</th>
                <th>设备ID</th>
                <th>模型类型</th>
                <th>事件</th>
                <th>置信度</th>
                <th>状态</th>
                <th>告警截图</th>
                <th>操作</th>
            </tr>
        </thead>

        <tbody>
            {% for alarm in alarms %}
            <tr>
                <td>
                    <a href="{{ url_for('alarm_detail', alarm_id=alarm.id) }}">{{ alarm.id }}</a>
                    {% if alarm.id == latest_alarm_id %}
                    <span class="latest-badge">最新</span>
                    {% endif %}
                </td>

                <td>{{ alarm.timestamp }}</td>
                <td>{{ alarm.device_id }}</td>
                <td>{{ alarm.model_type }}</td>
                <td>{{ alarm.event }}</td>
                <td>{{ alarm.confidence }}</td>

                <td>
                    {% if alarm.status == "handled" %}
                    <span class="status-handled">已处理</span>
                    {% else %}
                    <span class="status-pending">未处理</span>
                    {% endif %}
                </td>

                <td>
                    {% if alarm.image_file %}
                    <a href="{{ url_for('alarm_image', filename=alarm.image_file) }}" target="_blank">
                        <img class="thumb" src="{{ url_for('alarm_image', filename=alarm.image_file) }}">
                    </a>
                    {% else %}
                    无图片
                    {% endif %}
                </td>

                <td>
                    {% if alarm.status != "handled" %}
                    <form method="post" action="{{ url_for('handle_alarm', alarm_id=alarm.id) }}" class="action-form">
                        <input type="text" name="remark" placeholder="备注" class="action-input">
                        <button type="submit" class="action-button">确认处理</button>
                    </form>
                    {% else %}
                    <div style="font-size:13px;color:#666;margin-bottom:6px;">
                        {{ alarm.handled_at or "" }}
                    </div>

                    <form method="post" action="{{ url_for('pending_alarm', alarm_id=alarm.id) }}" class="action-form">
                        <button type="submit" class="action-button action-button-secondary">恢复未处理</button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class="empty">
        暂无符合条件的告警记录。
    </div>
    {% endif %}
    </div>

    <script>
        let cameraStream = null;
        let cameraRunning = false;
        let detectTimer = null;
        let detecting = false;

        // 默认后置摄像头：environment
        // 前置摄像头：user
        let currentFacingMode = "environment";

        async function openCamera() {
            const video = document.getElementById("cameraPreview");
            const status = document.getElementById("cameraStatus");
            const placeholder = document.getElementById("cameraPlaceholder");
            const videoLayer = document.querySelector(".camera-video-layer");
            const detectStatus = document.getElementById("detectStatus");

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                status.innerText = "当前页面无法访问摄像头。请确认你使用的是HTTPS地址，例如 https://局域网IP:5000。手机浏览器通常不允许HTTP页面调用摄像头。";
                status.className = "camera-status error";
                return;
            }

            try {
                // 先关闭旧摄像头，避免切换时被占用
                if (cameraStream) {
                    cameraStream.getTracks().forEach(function(track) {
                        track.stop();
                    });
                    cameraStream = null;
                }

                cameraStream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: {
                            ideal: currentFacingMode
                        },
                        width: {
                            ideal: 1280
                        },
                        height: {
                            ideal: 720
                        }
                    },
                    audio: false
                });

                video.srcObject = cameraStream;
                videoLayer.style.display = "block";
                placeholder.style.display = "none";
                cameraRunning = true;

                if (currentFacingMode === "environment") {
                    status.innerText = "摄像头已打开：当前为后置摄像头。";
                } else {
                    status.innerText = "摄像头已打开：当前为前置摄像头。";
                }

                status.className = "camera-status ok";

                detectStatus.innerText = "检测已启动，正在调用后端ONNX模型。";
                detectStatus.className = "camera-status ok";

                startDetectLoop();

            } catch (error) {
                videoLayer.style.display = "none";
                placeholder.style.display = "block";
                cameraRunning = false;

                if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
                    status.innerText = "无法打开摄像头：当前设备没有可用摄像头，或没有找到指定方向的摄像头。";
                } else if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
                    status.innerText = "无法打开摄像头：你拒绝了浏览器摄像头权限。";
                } else if (error.name === "NotReadableError") {
                    status.innerText = "无法打开摄像头：摄像头可能正被其他程序占用。";
                } else {
                    status.innerText = "无法打开摄像头：" + error.message;
                }

                status.className = "camera-status error";
            }
        }

        async function switchCamera() {
            if (currentFacingMode === "environment") {
                currentFacingMode = "user";
            } else {
                currentFacingMode = "environment";
            }

            if (cameraRunning) {
                stopDetectLoop();
                await openCamera();
            } else {
                const status = document.getElementById("cameraStatus");

                if (currentFacingMode === "environment") {
                    status.innerText = "已切换为后置摄像头，点击“打开摄像头”后生效。";
                } else {
                    status.innerText = "已切换为前置摄像头，点击“打开摄像头”后生效。";
                }

                status.className = "camera-status";
            }
        }

        function closeCamera() {
            const video = document.getElementById("cameraPreview");
            const status = document.getElementById("cameraStatus");
            const placeholder = document.getElementById("cameraPlaceholder");
            const videoLayer = document.querySelector(".camera-video-layer");
            const detectStatus = document.getElementById("detectStatus");
            const canvas = document.getElementById("detectCanvas");
            const ctx = canvas.getContext("2d");

            stopDetectLoop();

            if (cameraStream) {
                cameraStream.getTracks().forEach(function(track) {
                    track.stop();
                });
                cameraStream = null;
            }

            video.srcObject = null;
            videoLayer.style.display = "none";
            placeholder.style.display = "block";
            cameraRunning = false;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            status.innerText = "摄像头已关闭。";
            status.className = "camera-status";

            detectStatus.innerText = "检测未启动。";
            detectStatus.className = "camera-status";
        }

        function startDetectLoop() {
            stopDetectLoop();

            detectTimer = setInterval(function () {
                detectCurrentFrame();
            }, 1000);
        }

        function stopDetectLoop() {
            if (detectTimer) {
                clearInterval(detectTimer);
                detectTimer = null;
            }

            detecting = false;
        }

        async function detectCurrentFrame() {
            if (!cameraRunning || detecting) {
                return;
            }

            const video = document.getElementById("cameraPreview");
            const detectStatus = document.getElementById("detectStatus");

            if (!video.videoWidth || !video.videoHeight) {
                return;
            }

            detecting = true;

            const captureCanvas = document.createElement("canvas");
            captureCanvas.width = video.videoWidth;
            captureCanvas.height = video.videoHeight;

            const captureCtx = captureCanvas.getContext("2d");
            captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

            const imageData = captureCanvas.toDataURL("image/jpeg", 0.95);

            try {
                const response = await fetch("/api/detect-frame", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        image: imageData
                    })
                });

                const result = await response.json();

                if (!result.ok) {
                    detectStatus.innerText = "检测失败：" + result.message;
                    detectStatus.className = "camera-status error";
                    detecting = false;
                    return;
                }

                drawDetections(result.detections, video.videoWidth, video.videoHeight);

                let text = "检测中，推理耗时：" + result.inference_time_ms + " ms";
                if (result.alarm) {
                    text += "；发现未戴安全帽违规，已写入告警记录。";
                }

                detectStatus.innerText = text;
                detectStatus.className = result.alarm ? "camera-status error" : "camera-status ok";

            } catch (error) {
                detectStatus.innerText = "检测请求失败：" + error.message;
                detectStatus.className = "camera-status error";
            }

            detecting = false;
        }

        function drawDetections(detections, sourceWidth, sourceHeight) {
            const video = document.getElementById("cameraPreview");
            const canvas = document.getElementById("detectCanvas");
            const ctx = canvas.getContext("2d");

            canvas.width = sourceWidth;
            canvas.height = sourceHeight;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            detections.forEach(function(det) {
                const box = det.box;
                const x1 = box[0];
                const y1 = box[1];
                const x2 = box[2];
                const y2 = box[3];

                const className = det.class_name;
                const confidence = Number(det.confidence).toFixed(2);

                ctx.lineWidth = 3;
                ctx.strokeStyle = className === "no_helmet" ? "red" : "lime";
                ctx.fillStyle = className === "no_helmet" ? "red" : "lime";

                ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

                const label = className + " " + confidence;

                ctx.font = "20px Arial";
                const textWidth = ctx.measureText(label).width;

                ctx.fillRect(x1, Math.max(0, y1 - 26), textWidth + 12, 26);

                ctx.fillStyle = "white";
                ctx.fillText(label, x1 + 6, Math.max(20, y1 - 7));
            });
        }

        let latestAlarmId = Number("{{ latest_alarm_id }}") || 0;

        async function refreshDashboardContent() {
            try {
                const response = await fetch("/dashboard-content" + window.location.search, {
                    cache: "no-store"
                });

                const html = await response.text();

                const temp = document.createElement("div");
                temp.innerHTML = html;

                const replaceBlock = function(selector) {
                    const newBlock = temp.querySelector(selector);
                    const oldBlock = document.querySelector(selector);

                    if (newBlock && oldBlock) {
                        oldBlock.replaceWith(newBlock);
                    }
                };

                replaceBlock(".overview-left-top");
                replaceBlock(".overview-left-bottom");

                const newAlarmTable = temp.querySelector("table, .empty");
                const alarmTableContent = document.getElementById("alarmTableContent");

                if (newAlarmTable && alarmTableContent) {
                    alarmTableContent.innerHTML = "";
                    alarmTableContent.appendChild(newAlarmTable);
                }
            } catch (error) {
                console.log("局部更新告警看板失败：", error);
            }
        }

        function startAlarmEventListener() {
            if (!window.EventSource) {
                console.log("当前浏览器不支持 EventSource，无法启用新告警实时更新。");
                return;
            }

            const eventSource = new EventSource("/alarm-events?last_id=" + latestAlarmId);

            eventSource.addEventListener("new_alarm", function(event) {
                const newAlarmId = Number(event.data);

                if (newAlarmId > latestAlarmId) {
                    latestAlarmId = newAlarmId;
                    refreshDashboardContent();
                }
            });

            eventSource.onerror = function() {
                console.log("新告警监听连接异常，浏览器会自动尝试重连。");
            };
        }

        startAlarmEventListener();
    </script>
</body>
</html>
"""

DASHBOARD_CONTENT_TEMPLATE = """
        <div class="overview-left-top">
            <div class="cards">
                <div class="card total-card">
                    <div class="total-card-header">
                        <div>
                            <div class="card-title">告警总数</div>
                            <div class="card-value">{{ summary.total_count }}</div>
                        </div>
                    </div>

                    <div class="mini-trend-title">最近7天趋势</div>

                    <div class="mini-trend">
                        {% for item in daily_counts %}
                        <div class="mini-bar-item" title="{{ item.date }}：{{ item.count }}">
                            <div class="mini-bar" style="height: {{ (item.count / max_daily_count * 34) | int + 4 }}px;"></div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">今日告警</div>
                    <div class="card-value">{{ summary.today_count }}</div>
                </div>

                <div class="card">
                    <div class="card-title">最新告警时间</div>
                    <div class="card-value" style="font-size:16px;">{{ summary.latest_time }}</div>
                </div>

                <div class="card">
                    <div class="card-title">未处理告警</div>
                    <div class="card-value">{{ summary.pending_count }}</div>
                </div>
            </div>
        </div>

        <div class="overview-left-bottom">
            <div class="filter-box">
                <form method="get" class="filter-form">
                    <div class="filter-item">
                        <label>事件：</label>
                        <select name="event">
                            <option value="" {% if not filters.event %}selected{% endif %}>全部</option>
                            <option value="no_helmet" {% if filters.event == "no_helmet" %}selected{% endif %}>no_helmet</option>
                        </select>
                    </div>

                    <div class="filter-item">
                        <label>模型类型：</label>
                        <input type="text" name="model_type" value="{{ filters.model_type }}" placeholder="onnxruntime_modular">
                    </div>

                    <div class="filter-item">
                        <label>最低置信度：</label>
                        <input type="text" name="min_conf" value="{{ filters.min_conf }}" placeholder="0.5">
                    </div>

                    <div class="filter-item">
                        <label>显示条数：</label>
                        <input type="number" name="limit" value="{{ filters.limit }}" min="1" max="500">
                    </div>

                    <div class="filter-item">
                        <label>状态：</label>
                        <select name="status">
                            <option value="" {% if not filters.status %}selected{% endif %}>全部</option>
                            <option value="pending" {% if filters.status == "pending" %}selected{% endif %}>未处理</option>
                            <option value="handled" {% if filters.status == "handled" %}selected{% endif %}>已处理</option>
                        </select>
                    </div>

                    <div class="filter-actions">
                        <button type="submit" class="filter-button">筛选</button>
                        <a class="filter-link" href="/">重置</a>
                        <a class="filter-link filter-export" href="{{ export_url }}">导出CSV</a>
                    </div>
                </form>
            </div>
        </div>

    {% if alarms %}
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>时间</th>
                <th>设备ID</th>
                <th>模型类型</th>
                <th>事件</th>
                <th>置信度</th>
                <th>状态</th>
                <th>告警截图</th>
                <th>操作</th>
            </tr>
        </thead>

        <tbody>
            {% for alarm in alarms %}
            <tr>
                <td>
                    <a href="{{ url_for('alarm_detail', alarm_id=alarm.id) }}">{{ alarm.id }}</a>
                    {% if alarm.id == latest_alarm_id %}
                    <span class="latest-badge">最新</span>
                    {% endif %}
                </td>

                <td>{{ alarm.timestamp }}</td>
                <td>{{ alarm.device_id }}</td>
                <td>{{ alarm.model_type }}</td>
                <td>{{ alarm.event }}</td>
                <td>{{ alarm.confidence }}</td>

                <td>
                    {% if alarm.status == "handled" %}
                    <span class="status-handled">已处理</span>
                    {% else %}
                    <span class="status-pending">未处理</span>
                    {% endif %}
                </td>

                <td>
                    {% if alarm.image_file %}
                    <a href="{{ url_for('alarm_image', filename=alarm.image_file) }}" target="_blank">
                        <img class="thumb" src="{{ url_for('alarm_image', filename=alarm.image_file) }}">
                    </a>
                    {% else %}
                    无图片
                    {% endif %}
                </td>

                <td>
                    {% if alarm.status != "handled" %}
                    <form method="post" action="{{ url_for('handle_alarm', alarm_id=alarm.id) }}" class="action-form">
                        <input type="text" name="remark" placeholder="备注" class="action-input">
                        <button type="submit" class="action-button">确认处理</button>
                    </form>
                    {% else %}
                    <div style="font-size:13px;color:#666;margin-bottom:6px;">
                        {{ alarm.handled_at or "" }}
                    </div>

                    <form method="post" action="{{ url_for('pending_alarm', alarm_id=alarm.id) }}" class="action-form">
                        <button type="submit" class="action-button action-button-secondary">恢复未处理</button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class="empty">
        暂无符合条件的告警记录。
    </div>
    {% endif %}
"""


DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>告警详情</title>

    <style>
        body {
            font-family: Arial, "Microsoft YaHei", sans-serif;
            margin: 30px;
            background: #f5f6fa;
            color: #222;
        }

        .container {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            max-width: 1100px;
            margin: 0 auto;
        }

        h1 {
            margin-top: 0;
        }

        .info-grid {
            display: grid;
            grid-template-columns: 160px 1fr;
            gap: 12px;
            margin-bottom: 20px;
        }

        .label {
            color: #666;
            font-weight: bold;
        }

        .value {
            color: #222;
        }

        .status-pending {
            color: #ff4d4f;
            font-weight: bold;
        }

        .status-handled {
            color: #52c41a;
            font-weight: bold;
        }

        img {
            max-width: 100%;
            border-radius: 10px;
            border: 1px solid #ddd;
            margin-top: 12px;
        }

        .actions {
            margin-top: 24px;
        }

        .actions input {
            padding: 8px;
            width: 240px;
            border: 1px solid #ccc;
            border-radius: 6px;
        }

        .actions button {
            padding: 8px 14px;
            border: none;
            border-radius: 6px;
            background: #1677ff;
            color: white;
            cursor: pointer;
        }

        .secondary {
            background: #666 !important;
        }

        a {
            color: #1677ff;
            text-decoration: none;
        }

        .back {
            display: inline-block;
            margin-bottom: 16px;
        }
    </style>
</head>

<body>
    <div class="container">
        <a class="back" href="/">←返回告警看板</a>

        <h1>告警详情#{{ alarm.id }}</h1>

        <div class="info-grid">
            <div class="label">告警时间</div>
            <div class="value">{{ alarm.timestamp }}</div>

            <div class="label">设备ID</div>
            <div class="value">{{ alarm.device_id }}</div>

            <div class="label">模型类型</div>
            <div class="value">{{ alarm.model_type }}</div>

            <div class="label">事件类型</div>
            <div class="value">{{ alarm.event }}</div>

            <div class="label">置信度</div>
            <div class="value">{{ alarm.confidence }}</div>

            <div class="label">状态</div>
            <div class="value">
                {% if alarm.status == "handled" %}
                <span class="status-handled">已处理</span>
                {% else %}
                <span class="status-pending">未处理</span>
                {% endif %}
            </div>

            <div class="label">处理时间</div>
            <div class="value">{{ alarm.handled_at or "-" }}</div>

            <div class="label">处理人</div>
            <div class="value">{{ alarm.handler or "-" }}</div>

            <div class="label">备注</div>
            <div class="value">{{ alarm.remark or "-" }}</div>

            <div class="label">图片路径</div>
            <div class="value">{{ alarm.image_path }}</div>

            <div class="label">创建时间</div>
            <div class="value">{{ alarm.created_at }}</div>
        </div>

        {% if image_file %}
        <h2>告警截图</h2>
        <a href="{{ url_for('alarm_image', filename=image_file) }}" target="_blank">
            <img src="{{ url_for('alarm_image', filename=image_file) }}">
        </a>
        {% endif %}

        <div class="actions">
            {% if alarm.status != "handled" %}
            <form method="post" action="{{ url_for('handle_alarm', alarm_id=alarm.id) }}">
                <input type="text" name="remark" placeholder="备注">
                <button type="submit">确认处理</button>
            </form>
            {% else %}
            <form method="post" action="{{ url_for('pending_alarm', alarm_id=alarm.id) }}">
                <button type="submit" class="secondary">恢复未处理</button>
            </form>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


def parse_float(value):
    if value is None or value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value, default=100):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        return lan_ip
    except Exception:
        return "127.0.0.1"


def open_browser(url):
    try:
        webbrowser.open(url)
    except Exception:
        pass


def build_dashboard_context():
    event = request.args.get("event", "").strip()
    model_type = request.args.get("model_type", "").strip()
    status = request.args.get("status", "").strip()
    min_conf_raw = request.args.get("min_conf", "").strip()
    limit_raw = request.args.get("limit", "100").strip()

    min_conf = parse_float(min_conf_raw)
    limit = parse_int(limit_raw, default=100)

    if limit <= 0:
        limit = 100

    if limit > 500:
        limit = 500

    alarms = alarm_database.get_alarms_filtered(
        event=event,
        model_type=model_type,
        status=status,
        min_conf=min_conf,
        limit=limit,
    )

    for alarm in alarms:
        image_path = alarm.get("image_path", "")
        image_file = os.path.basename(image_path.replace("\\", "/"))
        alarm["image_file"] = image_file

    summary = alarm_database.get_summary()
    daily_counts = alarm_database.get_daily_counts(days=7)

    count_list = [item.get("count", 0) for item in daily_counts]
    max_daily_count = max(count_list) if count_list else 1

    if max_daily_count <= 0:
        max_daily_count = 1

    latest_alarm_id = alarms[0]["id"] if alarms else 0

    filters = {
        "event": event,
        "model_type": model_type,
        "status": status,
        "min_conf": min_conf_raw,
        "limit": limit,
    }

    export_url = url_for("export_csv", **request.args)

    return {
        "alarms": alarms,
        "summary": summary,
        "daily_counts": daily_counts,
        "max_daily_count": max_daily_count,
        "filters": filters,
        "export_url": export_url,
        "latest_alarm_id": latest_alarm_id,
        "auto_refresh_seconds": DASHBOARD_AUTO_REFRESH_SECONDS,
    }


@app.route("/")
def index():
    context = build_dashboard_context()
    return render_template_string(HTML_TEMPLATE, **context)


@app.route("/dashboard-content")
def dashboard_content():
    context = build_dashboard_context()
    return render_template_string(DASHBOARD_CONTENT_TEMPLATE, **context)


@app.route("/alarm-events")
def alarm_events():
    last_id_raw = request.args.get("last_id", "0")

    try:
        last_id = int(last_id_raw)
    except ValueError:
        last_id = 0

    @stream_with_context
    def event_stream():
        nonlocal last_id

        while True:
            latest = alarm_database.get_alarms_filtered(limit=1)
            latest_id = latest[0]["id"] if latest else 0

            if latest_id > last_id:
                last_id = latest_id
                yield f"event: new_alarm\ndata: {latest_id}\n\n"

            time.sleep(1)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/detect-frame", methods=["POST"])
def detect_frame():
    data = request.get_json(silent=True) or {}
    image_data = data.get("image", "")

    if not image_data:
        return jsonify({
            "ok": False,
            "message": "没有收到图像数据"
        }), 400

    try:
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        image_bytes = base64.b64decode(image_data)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({
                "ok": False,
                "message": "图像解码失败"
            }), 400

        with detect_lock:
            detections, inference_time_ms = detector.detect(frame)

        annotated_frame = frame.copy()

        for det in detections:
            x1, y1, x2, y2 = det["box"]
            class_name = det["class_name"]
            confidence = det["confidence"]

            color = (0, 0, 255) if class_name == "no_helmet" else (0, 255, 0)

            cv2.rectangle(
                annotated_frame,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                color,
                2,
            )

            label = f"{class_name} {confidence:.2f}"

            cv2.putText(
                annotated_frame,
                label,
                (int(x1), max(20, int(y1) - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        alarm_info = alarm_manager.handle(
            annotated_frame,
            detections,
            model_type="web_dashboard_camera",
        )

        return jsonify({
            "ok": True,
            "detections": detections,
            "inference_time_ms": round(inference_time_ms, 2),
            "alarm": alarm_info,
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "message": str(e),
        }), 500


@app.route("/handle/<int:alarm_id>", methods=["POST"])
def handle_alarm(alarm_id):
    remark = request.form.get("remark", "").strip()

    alarm_database.handle_alarm(
        alarm_id,
        handler="admin",
        remark=remark,
    )

    return redirect(url_for("alarm_detail", alarm_id=alarm_id))


@app.route("/alarm/<int:alarm_id>")
def alarm_detail(alarm_id):
    alarm = alarm_database.get_alarm_by_id(alarm_id)

    if alarm is None:
        return "告警记录不存在", 404

    image_path = alarm.get("image_path", "")
    image_file = os.path.basename(image_path.replace("\\", "/"))

    return render_template_string(
        DETAIL_TEMPLATE,
        alarm=alarm,
        image_file=image_file,
    )


@app.route("/pending/<int:alarm_id>", methods=["POST"])
def pending_alarm(alarm_id):
    alarm_database.mark_pending(alarm_id)
    return redirect(url_for("alarm_detail", alarm_id=alarm_id))


@app.route("/export-csv")
def export_csv():
    event = request.args.get("event", "").strip()
    model_type = request.args.get("model_type", "").strip()
    status = request.args.get("status", "").strip()
    min_conf_raw = request.args.get("min_conf", "").strip()
    limit_raw = request.args.get("limit", "500").strip()

    min_conf = parse_float(min_conf_raw)
    limit = parse_int(limit_raw, default=500)

    if limit <= 0:
        limit = 500

    if limit > 5000:
        limit = 5000

    alarms = alarm_database.get_alarms_filtered(
        event=event,
        model_type=model_type,
        status=status,
        min_conf=min_conf,
        limit=limit,
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id",
        "timestamp",
        "device_id",
        "model_type",
        "event",
        "confidence",
        "status",
        "handled_at",
        "handler",
        "remark",
        "image_path",
        "created_at",
    ])

    for alarm in alarms:
        writer.writerow([
            alarm.get("id", ""),
            alarm.get("timestamp", ""),
            alarm.get("device_id", ""),
            alarm.get("model_type", ""),
            alarm.get("event", ""),
            alarm.get("confidence", ""),
            alarm.get("status", ""),
            alarm.get("handled_at", ""),
            alarm.get("handler", ""),
            alarm.get("remark", ""),
            alarm.get("image_path", ""),
            alarm.get("created_at", ""),
        ])

    csv_content = "\ufeff" + output.getvalue()

    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=alarm_records.csv"
        },
    )


@app.route("/alarm-image/<filename>")
def alarm_image(filename):
    return send_from_directory(ALARM_DIR, filename)


if __name__ == "__main__":
    local_url = f"https://127.0.0.1:{DASHBOARD_PORT}"
    lan_ip = get_lan_ip()
    lan_url = f"https://{lan_ip}:{DASHBOARD_PORT}"

    print("安全帽违规告警看板启动中...")
    print(f"本机访问地址：{local_url}")
    print(f"局域网访问地址：{lan_url}")
    print("注意：手机访问摄像头必须使用 HTTPS。")
    print("如果浏览器提示证书不安全，这是本地测试证书导致的，开发测试时可以继续访问。")

    mqtt_publisher.connect()

    threading.Timer(1.0, open_browser, args=(local_url,)).start()

    try:
        app.run(
            host=DASHBOARD_HOST,
            port=DASHBOARD_PORT,
            debug=False,
            ssl_context="adhoc",
        )
    finally:
        mqtt_publisher.close()