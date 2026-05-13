import cv2
import time
import json
import os
import uuid
import yaml
from ultralytics import YOLO
import paho.mqtt.client as mqtt

# =========================
# 读取配置文件
# =========================

CONFIG_PATH = "config.yaml"


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config(CONFIG_PATH)


# =========================
# 基本配置
# =========================

DEVICE_ID = config["device"]["device_id"]

MODEL_PATH = config["model"]["model_path"]
VIDEO_URL = config["video"]["video_url"]

ALARM_CLASS_NAME = config["alarm"]["alarm_class_name"]
ALARM_COOLDOWN = config["alarm"]["alarm_cooldown"]
ALARM_DIR = config["alarm"]["alarm_dir"]
ALARM_LOG_FILE = config["alarm"]["alarm_log_file"]

CONF_THRESHOLD = config["detect"]["conf_threshold"]

# =========================
# MQTT 配置
# =========================

MQTT_ENABLE = config["mqtt"]["enable"]
BROKER_HOST = config["mqtt"]["broker_host"]
BROKER_PORT = config["mqtt"]["broker_port"]
MQTT_TOPIC = config["mqtt"]["topic"]

MQTT_CLIENT_ID = f"helmet_alarm_pub_{uuid.uuid4().hex[:8]}"


def create_mqtt_client():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID,
        protocol=mqtt.MQTTv311
    )

    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    print("MQTT 发布端已连接。")
    print("Broker:", BROKER_HOST)
    print("Topic:", MQTT_TOPIC)

    return client


def publish_alarm(client, alarm_info):
    payload = json.dumps(alarm_info, ensure_ascii=False)

    result = client.publish(
        MQTT_TOPIC,
        payload=payload,
        qos=1
    )

    result.wait_for_publish(timeout=5)

    if result.is_published():
        print("MQTT 告警已确认发布。")
    else:
        print("MQTT 告警可能未成功发布。")


# =========================
# 初始化
# =========================

os.makedirs(ALARM_DIR, exist_ok=True)

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_URL)

if not cap.isOpened():
    print("无法打开 DroidCam 视频流，请检查 VIDEO_URL。")
    exit()

mqtt_client = None

if MQTT_ENABLE:
    try:
        mqtt_client = create_mqtt_client()
    except Exception as e:
        print("MQTT 连接失败，系统将只进行本地告警。")
        print("错误信息:", e)
        mqtt_client = None

last_alarm_time = 0

print("安全帽违规告警系统已启动。按 q 退出。")
print("模型类别：", model.names)

# =========================
# 主循环
# =========================

while True:
    ret, frame = cap.read()

    if not ret:
        print("读取视频帧失败。")
        break

    results = model.predict(
        frame,
        conf=CONF_THRESHOLD,
        verbose=False
    )

    result = results[0]
    annotated_frame = result.plot()

    has_no_helmet = False
    max_conf = 0.0

    for box in result.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        class_name = model.names[cls_id]

        if class_name == ALARM_CLASS_NAME:
            has_no_helmet = True
            max_conf = max(max_conf, conf)

    current_time = time.time()

    if has_no_helmet and current_time - last_alarm_time >= ALARM_COOLDOWN:
        last_alarm_time = current_time

        timestamp_file = time.strftime("%Y%m%d_%H%M%S")
        timestamp_text = time.strftime("%Y-%m-%d %H:%M:%S")

        image_name = f"no_helmet_alarm_{timestamp_file}.jpg"
        image_path = os.path.join(ALARM_DIR, image_name)

        cv2.imwrite(image_path, annotated_frame)

        alarm_info = {
            "device_id": DEVICE_ID,
            "event": "no_helmet",
            "confidence": round(max_conf, 4),
            "image_path": image_path,
            "timestamp": timestamp_text
        }

        print("\n发现未戴安全帽违规：")
        print(json.dumps(alarm_info, ensure_ascii=False, indent=2))

        with open(ALARM_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(alarm_info, ensure_ascii=False) + "\n")

        if mqtt_client is not None:
            publish_alarm(mqtt_client, alarm_info)

    cv2.imshow("Helmet Violation Alarm System", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# =========================
# 释放资源
# =========================

cap.release()
cv2.destroyAllWindows()

if mqtt_client is not None:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

print("系统已退出。")