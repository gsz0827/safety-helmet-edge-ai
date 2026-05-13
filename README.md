# # 基于 YOLOv8 + ONNX Runtime + MQTT 的模块化安全帽违规告警系统

## 1. 项目简介

本项目实现了一个基于 YOLOv8、ONNX Runtime 和 MQTT 的模块化安全帽违规告警系统。系统使用 DroidCam 将手机摄像头作为实时视频输入，通过自训练 YOLOv8 模型完成 `helmet` / `no_helmet` 两类目标检测。

项目进一步提供**模块化 Web 看板**，支持局域网访问，并可通过 Windows 批处理脚本一键启动 Web 看板 + MQTT 订阅端 + ONNX 告警系统。此外，可选择使用 ngrok 将局域网端口映射到公网，便于外网访问。

当检测到未佩戴安全帽行为时，系统会自动保存告警截图、写入 JSONL 告警日志，并通过 MQTT 将告警 JSON 发布到指定 Topic，由订阅端实时接收。

在基础 YOLOv8 推理流程之外，项目进一步将 PyTorch `.pt` 模型导出为 ONNX 格式，并基于 ONNX Runtime 实现独立推理流程，手动完成图像预处理、模型推理、YOLOv8 输出解析、NMS 后处理和告警上传。同时，项目通过 `config.yaml` 统一管理模型路径、视频流地址、检测阈值、告警参数和 MQTT 配置，并将系统拆分为 Camera、Detector、AlarmManager、MqttPublisher、Visualizer 等模块，形成了较完整的边缘 AI + AIoT 工程化闭环。

---

## 2. 项目功能

- 使用 YOLOv8 训练安全帽检测模型
- 支持 `helmet` / `no_helmet` 两类目标检测
- 支持 DroidCam 手机摄像头实时视频流输入
- 支持实时检测结果可视化
- 检测到 `no_helmet` 时自动触发告警
- 自动保存违规告警截图
- 自动记录 JSONL 格式告警日志
- 支持 MQTT 发布告警信息
- 支持 MQTT 订阅端实时接收告警消息
- 支持将模型导出为 ONNX 格式并基于 ONNX Runtime 进行部署测试
- 支持独立 ONNX Runtime 推理脚本，手动完成预处理、推理、后处理和 NMS
- 支持通过 `config.yaml` 管理模型路径、视频流地址、检测阈值、告警参数和 MQTT 配置
- 提供 Windows 批处理脚本，一键启动 Web 看板 + MQTT + ONNX 告警系统
- Web 看板支持局域网访问，手机或同网络设备可直接访问
- 可选 ngrok 公网映射，自动生成公网访问 URL
- 支持独立 ONNX Runtime 推理脚本，手动完成图像预处理、模型推理、YOLOv8 输出解析、NMS 后处理和告警上传
- Web 看板显示实时告警，并可筛选、导出 CSV

---

## 3. 系统架构

```text
DroidCam 手机摄像头
        ↓
HTTP MJPEG 视频流
        ↓
OpenCV 读取视频帧
        ↓
YOLOv8 安全帽检测模型
        ↓
检测 helmet / no_helmet
        ↓
违规事件判断
        ↓
保存告警截图
        ↓
写入 alarm_log.jsonl
        ↓
MQTT 发布告警 JSON
        ↓
MQTT 订阅端接收告警
        ↓
Web 看板显示实时告警
        ↓
批处理脚本一键启动系统
```

---

## 4. 技术栈

| 模块 | 技术 |
|---|---|
| 编程语言 | Python |
| 目标检测 | YOLOv8 / Ultralytics |
| 模型部署 | ONNX / ONNX Runtime |
| 图像处理 | OpenCV |
| 配置管理 | YAML / PyYAML |
| 数据集格式 | Pascal VOC XML / YOLO TXT |
| 视频输入 | DroidCam / MJPEG Stream |
| 消息通信 | MQTT |
| MQTT 客户端 | paho-mqtt |
| 告警格式 | JSON / JSONL |
| 运行环境 | Windows + Python 虚拟环境 |

---

## 5. 项目目录结构

```text
YOLOV8-safety-helmet-detection/
├── src/
│   ├── __init__.py
│   ├── config_loader.py
│   ├── camera_stream.py
│   ├── onnx_detector.py
│   ├── alarm_manager.py
│   ├── mqtt_publisher.py
│   └── visualizer.py
├── tools/
│   ├── speed_test.py
│   └── onnx_runtime_detect.py
├── legacy/
│   ├── helmet_alarm_system.py
│   └── onnx_runtime_alarm_mqtt.py
├── tests/
│   └── manual/
│       ├── test_config.py
│       ├── test_mqtt_publisher.py
│       ├── test_alarm_manager.py
│       └── test_onnx_detector.py
├── scripts/
│   ├── run_subscriber.bat
│   ├── run_alarm.bat
│   ├── run_speed_test.bat
│   └── start_demo.bat
├── docs/
│   └── images/
│       ├── realtime_detection.png
│       ├── alarm_result.png
│       └── mqtt_alarm.png
├── config.yaml
├── helmet.yaml
├── voc_to_yolo.py
├── split_dataset.py
├── mqtt_subscriber.py
├── run_onnx_alarm.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 6. 环境安装

### 6.1 创建 Python 虚拟环境

在项目根目录下执行：

```powershell
python -m venv venv
```

如果使用 PowerShell 无法正常激活虚拟环境，可以不激活，直接使用虚拟环境中的 Python 解释器运行项目：

```powershell
.\venv\Scripts\python.exe
```

### 6.2 安装项目依赖

本项目依赖已统一写入 `requirements.txt`，安装时执行：

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

如果下载速度较慢，可以使用清华源：

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 6.3 检查环境是否安装成功

安装完成后，可以运行以下命令检查 YOLO 和 MQTT 相关库是否可用：

```powershell
.\venv\Scripts\python.exe -c "from ultralytics import YOLO; print('ultralytics ok')"
```

```powershell
.\venv\Scripts\python.exe -c "import paho.mqtt.client as mqtt; print('mqtt ok')"
```

如果终端分别输出：

```text
ultralytics ok
mqtt ok
```

说明环境安装成功。

---

## 7. 数据集准备

本项目使用安全帽检测数据集，原始标注格式为 Pascal VOC XML。

原始数据整理为：

```text
dataset/
├── images/
│   ├── hard_hat_workers0.png
│   ├── hard_hat_workers1.png
│   └── ...
└── annotations/
    ├── hard_hat_workers0.xml
    ├── hard_hat_workers1.xml
    └── ...
```

图片文件和 XML 标注文件需要保持主文件名一致，例如：

```text
hard_hat_workers0.png  对应  hard_hat_workers0.xml
```

---

## 8. 数据格式转换

将 Pascal VOC XML 标注转换为 YOLO 格式：

```powershell
.\venv\Scripts\python.exe voc_to_yolo.py
```

转换完成后，会生成：

```text
dataset/yolo_labels/
```

---

## 9. 划分训练集和验证集

运行：

```powershell
.\venv\Scripts\python.exe split_dataset.py
```

划分完成后，数据集结构为：

```text
dataset/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

本项目中训练集和验证集数量约为：

```text
train images: 4000
val images: 1000
train labels: 4000
val labels: 1000
```

---

## 10. 模型训练

### 10.1 小规模测试训练

```powershell
.\venv\Scripts\yolo.exe detect train model=yolov8n.pt data=helmet.yaml epochs=3 imgsz=640 batch=4 device=cpu
```

### 10.2 正式训练

```powershell
.\venv\Scripts\yolo.exe detect train model=yolov8n.pt data=helmet.yaml epochs=30 imgsz=640 batch=4 device=cpu project=runs\detect name=helmet_final
```

训练完成后，模型保存在：

```text
runs/detect/helmet_final/weights/best.pt
```

---

## 11. 模型验证

```powershell
.\venv\Scripts\yolo.exe detect val model=runs\detect\helmet_final\weights\best.pt data=helmet.yaml
```

验证结果会输出 Precision、Recall、mAP50、mAP50-95 等指标。

验证结果如下：
                   all       1000       4935      0.924      0.866      0.936      0.614
                helmet        902       3659      0.962      0.887      0.964      0.635
             no_helmet        192       1276      0.886      0.844      0.908      0.593

---

## 12. 图片检测测试

```powershell
.\venv\Scripts\yolo.exe detect predict model=runs\detect\helmet_final\weights\best.pt source=dataset\images\val save=True conf=0.5
```

检测结果会保存在：

```text
runs/detect/predict/
```

---

## 13. 实时视频流检测

本项目使用 DroidCam 将手机摄像头作为视频输入。

DroidCam 视频流地址示例：

```text
http://192.168.1.102:4747/mjpegfeed
```

运行实时检测：

```powershell
.\venv\Scripts\yolo.exe detect predict model=runs\detect\helmet_final\weights\best.pt source="http://192.168.1.102:4747/mjpegfeed" show=True conf=0.5
```

注意：DroidCam 的 IP 地址可能会因为重新连接 Wi-Fi 而变化。如果 IP 变化，需要修改 `source` 中的视频流地址。

---

## 14. ONNX 模型导出与部署测试

为了提高模型的跨平台部署能力，本项目将训练得到的 PyTorch 权重文件 `best.pt` 导出为 ONNX 格式，并使用 ONNX Runtime 进行部署测试。

### 14.1 导出 ONNX 模型

```powershell
.\venv\Scripts\yolo.exe export model=runs\detect\helmet_final\weights\best.pt format=onnx imgsz=640 simplify=True
```

导出完成后，生成 ONNX 模型文件：

```text
runs/detect/helmet_final/weights/best.onnx
```

### 14.2 ONNX 实时视频流检测

```powershell
.\venv\Scripts\yolo.exe detect predict model=runs\detect\helmet_final\weights\best.onnx source="http://192.168.1.102:4747/mjpegfeed" show=True conf=0.5
```

测试中，ONNX 模型能够正常读取 DroidCam 实时视频流，并完成 `helmet` / `no_helmet` 检测。

### 14.3 PyTorch 与 ONNX 推理速度对比

测试环境：

- CPU：Intel Core i5-14600KF
- 输入源：DroidCam MJPEG 实时视频流
- 输入分辨率：640 × 480
- 置信度阈值：0.5
- 测试帧数：200 帧
- 预热帧数：20 帧

| 模型格式 | 推理后端 | 平均端到端耗时 | 平均 inference 时间 | 估算 FPS |
|---|---|---:|---:|---:|
| `best.pt` | PyTorch | 27.82 ms/frame | 26.23 ms/frame | 35.94 |
| `best.onnx` | ONNX Runtime CPUExecutionProvider | 23.63 ms/frame | 19.99 ms/frame | 42.31 |

测试结果表明，在当前 CPU 环境下，ONNX Runtime 版本相比 PyTorch `.pt` 版本具有更低的推理延迟。其中，平均 inference 时间由 26.23 ms/frame 降低到 19.99 ms/frame，推理速度提升约 23.8%。

通过 ONNX 导出，模型具备了更好的跨平台部署能力，便于后续在 ONNX Runtime、C++、Jetson、树莓派或其他边缘设备上进行推理部署。

### 14.4 独立 ONNX Runtime 实时检测

除了使用 Ultralytics 的 `yolo.exe` 命令运行 ONNX 模型外，本项目进一步实现了独立 ONNX Runtime 推理脚本：

```powershell
.\venv\Scripts\python.exe tools\onnx_runtime_detect.py

该脚本不依赖 Ultralytics 的高层 model.predict() 接口，而是手动完成以下流程：

OpenCV 读取 DroidCam 视频流
        ↓
letterbox 图像预处理
        ↓
ONNX Runtime InferenceSession 加载模型
        ↓
执行 ONNX 推理
        ↓
解析 YOLOv8 输出
        ↓
NMS 后处理
        ↓
绘制检测框并显示 FPS / inference 时间

该部分用于验证 ONNX 模型在独立推理环境下的可部署性，为后续迁移到 C++、Jetson、树莓派等边缘设备提供基础。

---

## 15. 配置文件说明

项目支持通过 `config.yaml` 统一管理运行参数，包括模型路径、视频流地址、检测阈值、告警参数和 MQTT 配置，避免在 Python 代码中硬编码参数。

`config.yaml` 示例：

```yaml
device:
  device_id: edge_ai_001

model:
  model_path: runs/detect/helmet_final/weights/best.onnx
  input_size: 640
  class_names:
    - helmet
    - no_helmet

video:
  video_url: http://192.168.1.107:4747/mjpegfeed

detect:
  conf_threshold: 0.5
  iou_threshold: 0.45

alarm:
  alarm_class_name: no_helmet
  alarm_cooldown: 5
  alarm_dir: alarm_results
  alarm_log_file: alarm_log.jsonl

mqtt:
  enable: true
  broker_host: broker.emqx.io
  broker_port: 1883
  topic: edge_ai/miaoqinfang/device001/alarm
```

当 DroidCam 的 IP 地址发生变化时，只需要修改：

```yaml
video:
  video_url: http://新的IP:4747/mjpegfeed
```

无需再修改 `run_onnx_alarm.py`、`mqtt_subscriber.py` 或其他 Python 源码。配置文件化后，模型路径、检测阈值、告警冷却时间和 MQTT Topic 等参数都可以集中管理，提高了项目的可维护性。

---

## 16. 本地违规告警系统

本项目最终主程序为：

```powershell
.\venv\Scripts\python.exe run_onnx_alarm.py
```

该版本采用模块化工程结构，主要模块如下：

| 模块 | 作用 |
|---|---|
| `config_loader.py` | 读取 `config.yaml` 配置文件 |
| `camera_stream.py` | 读取 DroidCam MJPEG 视频流 |
| `onnx_detector.py` | ONNX Runtime 推理、图像预处理、YOLOv8 输出解析和 NMS 后处理 |
| `alarm_manager.py` | 违规判断、告警冷却、截图保存和 JSONL 日志记录 |
| `mqtt_publisher.py` | MQTT 告警发布 |
| `visualizer.py` | 检测框绘制、FPS 和推理时间显示 |

当检测到 `no_helmet` 时，系统会：

1. 保存告警截图到 `alarm_results/`
2. 写入告警日志 `alarm_log.jsonl`
3. 打印告警 JSON
4. 通过 MQTT 发布告警消息

告警 JSON 示例：

```json
{
  "device_id": "edge_ai_001",
  "model_type": "onnxruntime_modular",
  "event": "no_helmet",
  "confidence": 0.6881,
  "image_path": "alarm_results\\onnxruntime_modular_no_helmet_alarm_20260509_094902.jpg",
  "timestamp": "2026-05-09 09:49:02"
}
```

`legacy/` 目录中保留了早期单文件版本，便于对比项目从脚本式实现到模块化工程实现的演进过程。

---

## 17. MQTT 告警上传

### 17.1 MQTT 配置

项目中使用公共 MQTT Broker：

```text
broker.emqx.io
```

默认 Topic：

```text
edge_ai/device001/alarm
```

为了避免公共 Broker 上的 Topic 冲突，建议改成更唯一的 Topic，例如：

```text
edge_ai/miaoqinfang/device001/alarm
```

注意：发布端和订阅端的 Topic 必须完全一致。

---

### 17.2 启动 MQTT 订阅端

打开一个新的 PowerShell 窗口，运行：

```powershell
.\venv\Scripts\python.exe mqtt_subscriber.py
```

订阅端启动后，会等待接收告警消息。

---

### 17.3 启动模块化告警系统发布端

再打开另一个 PowerShell 窗口，运行：

```powershell
.\venv\Scripts\python.exe run_onnx_alarm.py

---

## 18. 一键运行脚本

为了方便项目演示，项目提供了 Windows 批处理脚本：

| 脚本 | 作用 |
|---|---|
| `scripts/run_subscriber.bat` | 启动 MQTT 订阅端 |
| `scripts/run_alarm.bat` | 启动模块化 ONNX Runtime 告警系统 |
| `scripts/run_speed_test.bat` | 运行 `.pt` 与 `.onnx` 推理速度对比 |
| `scripts/start_demo.bat` | 一键启动 MQTT 订阅端 + ONNX 告警系统 + Web 看板 |
| `scripts/run_dashboard.bat` | 单独启动 Web 看板（局域网访问） |
| `scripts/start_dashboard_ngrok_auto.bat` | 一键启动 Web 看板 + ngrok 公网访问（自动打开浏览器 URL） |

> 备注：局域网访问时可使用 `run_dashboard.bat`；需要公网访问时可使用 `start_dashboard_ngrok_auto.bat`。

演示时可以直接运行：

```bat
scripts\start_demo.bat

---

## 19. 运行效果

### 19.1 实时检测效果

在实时视频流中，系统能够检测画面中的安全帽或未佩戴安全帽目标。

建议在此处插入实时检测截图：

```markdown
![实时检测效果](docs/images/realtime_detection.png)
```

---

### 19.2 告警截图

检测到未戴安全帽后，系统会保存告警截图。

建议在此处插入告警截图：

```markdown
![告警截图](docs/images/alarm_result.png)
```

---

### 19.3 MQTT 告警接收效果

订阅端成功收到告警 JSON。

建议在此处插入 MQTT 订阅端截图：

```markdown
![MQTT 告警接收](docs/images/mqtt_alarm.png)
```

---

## 20. 项目亮点

- 完成从数据集处理、模型训练到实时部署的完整流程
- 使用 YOLOv8 实现安全帽和未佩戴安全帽检测
- 使用 DroidCam 构建低成本实时视频输入方案
- 实现违规事件判断，而不是单纯目标检测
- 支持告警截图保存和 JSONL 日志记录
- 支持 MQTT 告警上传，具备 AIoT 系统雏形
- 具备后续部署到 Jetson、树莓派等边缘设备的扩展能力
- 支持 `config.yaml` 配置文件，统一管理模型路径、视频流地址、检测阈值、告警参数和 MQTT Topic
- 完成 PyTorch `.pt` 到 ONNX 模型导出，并基于 ONNX Runtime 完成部署测试
- 实现独立 ONNX Runtime 推理脚本，手动完成图像预处理、模型推理、YOLOv8 输出解析、NMS 后处理和告警上传

---

## 21. 常见问题

### 21.1 DroidCam 浏览器能打开，但 YOLO 打不开

优先使用：

```text
http://手机IP:4747/mjpegfeed
```

而不是：

```text
http://手机IP:4747/video
```

---

### 21.2 DroidCam IP 变化

DroidCam 的 IP 地址可能会因为重新连接 Wi-Fi、重启手机或重启路由器而变化。

如果手机 IP 从：

```text
192.168.1.102

变成：
192.168.1.107

只需要修改 config.yaml 中的：
video:
  video_url: http://192.168.1.107:4747/mjpegfeed

对于直接使用 yolo.exe detect predict 的临时测试命令，也需要同步修改命令中的 source 地址。

---

### 21.3 误检较多

可以提高置信度阈值：

```text
conf=0.5
conf=0.6
```

在 `helmet_alarm_system.py` 中可以修改：

```python
CONF_THRESHOLD = 0.5
```

---

### 21.4 MQTT 订阅端收不到消息

检查：

1. `mqtt_subscriber.py` 是否正在运行
2. 发布端和订阅端的 Topic 是否完全一致
3. 网络是否能访问 `broker.emqx.io`
4. 告警系统是否真的检测到了 `no_helmet`

---

## 22. 后续优化方向

- 使用 C++ + ONNX Runtime 重写推理端，提高部署工程化程度
- 将 ONNX 模型进一步转换为 TensorRT Engine，在 NVIDIA Jetson 平台上进行加速部署
- 部署到 Jetson / 树莓派 / RK3588 等边缘设备
- 增加 Web 前端展示告警记录
- 将告警信息保存到数据库
- 支持多摄像头输入
- 支持 RTSP 视频流输入
- 增加设备心跳和离线检测机制
- 增加 MQTT 断线重连机制
- 将本地图片路径替换为服务器图片 URL

---

## 23. 项目总结

本项目实现了一个完整的安全帽违规告警系统，从数据处理、YOLOv8 模型训练、实时视频流检测，到本地告警记录、MQTT 远程告警上传和 ONNX Runtime 部署优化，形成了较完整的边缘 AI + AIoT 应用闭环。

在原有 Ultralytics 推理流程基础上，项目进一步实现了独立 ONNX Runtime 推理与告警脚本，手动完成图像预处理、模型推理、YOLOv8 输出解析、NMS 后处理和 MQTT 告警上传，提高了系统的部署可控性和工程化程度。

该系统可以作为边缘 AI、嵌入式 AI、AIoT 和计算机视觉部署方向的项目基础，后续可以进一步部署到 Jetson、树莓派或其他边缘计算设备上。

---

## 24. Web 看板（局域网 / 公网访问）

- 局域网访问：
  - 配置 `config.yaml` 中 `dashboard.host: 0.0.0.0`
  - 使用电脑局域网 IP + 端口访问，例如 `http://192.168.1.127:5000`
- 公网访问：
  - 使用 `start_dashboard_ngrok_auto.bat` 启动
  - ngrok 自动生成公网 URL 并打开浏览器
- 功能：
  - 实时显示最新告警
  - 支持筛选告警、导出 CSV
  - 最新告警高亮显示
  - 自动刷新功能，可配置刷新间隔

  ---

  ## 25. 系统运行与部署

### 25.1 局域网部署
双击 `scripts/run_dashboard.bat` 启动 Web 看板，可在局域网内访问。

### 25.2 一键演示脚本
双击 `scripts/start_demo.bat` 启动：
- MQTT 订阅端
- ONNX 告警系统
- Web 看板（局域网）

### 25.3 公网访问
双击 `scripts/start_dashboard_ngrok_auto.bat`：
- 启动 Web 看板
- 启动 ngrok 公网访问
- 浏览器自动打开公网 URL