# web_mobile_camera.py
import os
from flask import Flask, render_template, Response, request
import cv2
import threading
import base64
import numpy as np
import sys
from werkzeug.middleware.proxy_fix import ProxyFix
import io

# ------------------------------
# 修复中文输出
# ------------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ------------------------------
# Flask 模板目录
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
app = Flask(__name__, template_folder=TEMPLATES_DIR)

# 处理 ngrok 或代理请求
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ------------------------------
# 多摄像头共享字典
# ------------------------------
frames = {}
lock = threading.Lock()

# ------------------------------
# Capture 页面（手机摄像头采集）
# ------------------------------
@app.route("/capture/<camera_id>")
def capture(camera_id):
    """
    手机打开此页面，调用摄像头上传视频帧
    """
    return render_template("capture.html", camera_id=camera_id)

# ------------------------------
# 手机上传视频帧接口
# ------------------------------
@app.route("/api/camera/<camera_id>/frame", methods=["POST"])
def upload_frame(camera_id):
    """
    手机每隔一帧上传一次 JPEG
    """
    data = request.form.get("image", "")
    if not data:
        return "no image", 400
    try:
        img_bytes = base64.b64decode(data.split(",")[1])
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        with lock:
            frames[camera_id] = img
        return "ok"
    except Exception as e:
        print(f"[ERROR] 上传摄像头帧失败: {e}")
        return "error", 500

# ------------------------------
# 输出实时 MJPEG 视频流
# ------------------------------
def generate(camera_id):
    while True:
        with lock:
            frame = frames.get(camera_id)
        if frame is None:
            # 如果没有帧，则显示空白黑色图像
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route("/camera/<camera_id>")
def stream(camera_id):
    return Response(generate(camera_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ------------------------------
# Monitor 页面（查看所有摄像头）
# ------------------------------
@app.route("/monitor")
def monitor():
    with lock:
        cam_ids = list(frames.keys())
    if not cam_ids:
        # 刚启动没有摄像头上传，默认显示 cam_01
        cam_ids = ["cam_01"]
    return render_template("monitor.html", cam_ids=cam_ids)

# ------------------------------
# 启动 Flask 服务
# ------------------------------
if __name__ == "__main__":
    # host 0.0.0.0 可被 ngrok 或局域网访问
    # threaded=True 支持多线程
    app.run(host="0.0.0.0", port=5443, debug=True, threaded=True)