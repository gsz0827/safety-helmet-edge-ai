import cv2
import time
import json
import os
import uuid
import yaml
import numpy as np
import onnxruntime as ort
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
INPUT_SIZE = config["model"]["input_size"]
CLASS_NAMES = config["model"]["class_names"]

VIDEO_URL = config["video"]["video_url"]

CONF_THRESHOLD = config["detect"]["conf_threshold"]
IOU_THRESHOLD = config["detect"]["iou_threshold"]

ALARM_CLASS_NAME = config["alarm"]["alarm_class_name"]
ALARM_COOLDOWN = config["alarm"]["alarm_cooldown"]
ALARM_DIR = config["alarm"]["alarm_dir"]
ALARM_LOG_FILE = config["alarm"]["alarm_log_file"]

os.makedirs(ALARM_DIR, exist_ok=True)


# =========================
# MQTT 配置
# =========================

MQTT_ENABLE = config["mqtt"]["enable"]
BROKER_HOST = config["mqtt"]["broker_host"]
BROKER_PORT = config["mqtt"]["broker_port"]
MQTT_TOPIC = config["mqtt"]["topic"]

MQTT_CLIENT_ID = f"onnx_alarm_pub_{uuid.uuid4().hex[:8]}"


def create_mqtt_client():
    try:
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv311
        )
    except AttributeError:
        client = mqtt.Client(
            client_id=MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv311
        )

    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    print("MQTT 发布端已连接")
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
        print("MQTT 告警已确认发布")
    else:
        print("MQTT 告警可能未成功发布")


# =========================
# 图像预处理
# =========================

def letterbox(image, new_shape=640, color=(114, 114, 114)):
    h, w = image.shape[:2]

    scale = min(new_shape / h, new_shape / w)

    new_w = int(round(w * scale))
    new_h = int(round(h * scale))

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    dw = new_shape - new_w
    dh = new_shape - new_h

    dw /= 2
    dh /= 2

    top = int(round(dh - 0.1))
    bottom = int(round(dh + 0.1))
    left = int(round(dw - 0.1))
    right = int(round(dw + 0.1))

    padded = cv2.copyMakeBorder(
        resized,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=color
    )

    return padded, scale, left, top


def preprocess(frame):
    img, scale, pad_x, pad_y = letterbox(frame, INPUT_SIZE)

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.transpose(2, 0, 1)
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)

    return img, scale, pad_x, pad_y


# =========================
# 后处理
# =========================

def xywh_to_xyxy(box):
    x, y, w, h = box

    x1 = x - w / 2
    y1 = y - h / 2
    x2 = x + w / 2
    y2 = y + h / 2

    return [x1, y1, x2, y2]


def postprocess(output, original_shape, scale, pad_x, pad_y):
    predictions = output

    if predictions.ndim == 3:
        predictions = predictions[0]

    expected_dim = 4 + len(CLASS_NAMES)

    if predictions.shape[0] == expected_dim:
        predictions = predictions.T
    elif predictions.shape[1] == expected_dim:
        pass
    else:
        raise ValueError(f"Unexpected ONNX output shape: {predictions.shape}")

    boxes = []
    scores = []
    class_ids = []

    original_h, original_w = original_shape[:2]

    for pred in predictions:
        box = pred[:4]
        class_scores = pred[4:]

        class_id = int(np.argmax(class_scores))
        confidence = float(class_scores[class_id])

        if confidence < CONF_THRESHOLD:
            continue

        x1, y1, x2, y2 = xywh_to_xyxy(box)

        x1 = (x1 - pad_x) / scale
        y1 = (y1 - pad_y) / scale
        x2 = (x2 - pad_x) / scale
        y2 = (y2 - pad_y) / scale

        x1 = max(0, min(original_w - 1, x1))
        y1 = max(0, min(original_h - 1, y1))
        x2 = max(0, min(original_w - 1, x2))
        y2 = max(0, min(original_h - 1, y2))

        w = x2 - x1
        h = y2 - y1

        if w <= 0 or h <= 0:
            continue

        boxes.append([int(x1), int(y1), int(w), int(h)])
        scores.append(confidence)
        class_ids.append(class_id)

    indices = cv2.dnn.NMSBoxes(
        boxes,
        scores,
        CONF_THRESHOLD,
        IOU_THRESHOLD
    )

    detections = []

    if len(indices) > 0:
        for i in np.array(indices).flatten():
            x, y, w, h = boxes[i]
            class_id = class_ids[i]
            confidence = scores[i]

            detections.append({
                "class_id": class_id,
                "class_name": CLASS_NAMES[class_id],
                "confidence": confidence,
                "box": [x, y, x + w, y + h]
            })

    return detections


# =========================
# 可视化
# =========================

def draw_detections(frame, detections):
    for det in detections:
        x1, y1, x2, y2 = det["box"]
        class_name = det["class_name"]
        confidence = det["confidence"]

        if class_name == "no_helmet":
            color = (0, 0, 255)
        else:
            color = (0, 255, 0)

        label = f"{class_name} {confidence:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        cv2.putText(
            frame,
            label,
            (x1, max(25, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

    return frame


# =========================
# 告警逻辑
# =========================

def handle_alarm(frame, detections, last_alarm_time, mqtt_client):
    has_no_helmet = False
    max_conf = 0.0

    for det in detections:
        if det["class_name"] == ALARM_CLASS_NAME:
            has_no_helmet = True
            max_conf = max(max_conf, det["confidence"])

    current_time = time.time()

    if not has_no_helmet:
        return last_alarm_time

    if current_time - last_alarm_time < ALARM_COOLDOWN:
        return last_alarm_time

    timestamp_file = time.strftime("%Y%m%d_%H%M%S")
    timestamp_text = time.strftime("%Y-%m-%d %H:%M:%S")

    image_name = f"onnx_no_helmet_alarm_{timestamp_file}.jpg"
    image_path = os.path.join(ALARM_DIR, image_name)

    cv2.imwrite(image_path, frame)

    alarm_info = {
        "device_id": DEVICE_ID,
        "model_type": "onnxruntime",
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

    return current_time


# =========================
# 主程序
# =========================

def main():
    print("正在加载 ONNX 模型...")
    print("Model:", MODEL_PATH)

    session = ort.InferenceSession(
        MODEL_PATH,
        providers=["CPUExecutionProvider"]
    )

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    print("ONNX Runtime providers:", session.get_providers())
    print("Input name:", input_name)
    print("Output name:", output_name)

    mqtt_client = None

    if MQTT_ENABLE:
        try:
            mqtt_client = create_mqtt_client()
        except Exception as e:
            print("MQTT 连接失败，系统将只进行本地告警")
            print("错误信息:", e)
            mqtt_client = None

    cap = cv2.VideoCapture(VIDEO_URL)

    if not cap.isOpened():
        print("无法打开视频流，请检查 DroidCam 地址是否正确")
        return

    print("ONNX Runtime 违规告警系统启动成功，按 q 退出")

    last_alarm_time = 0
    frame_count = 0
    fps_start_time = time.time()
    current_fps = 0.0

    while True:
        ret, frame = cap.read()

        if not ret:
            print("读取视频帧失败")
            break

        input_tensor, scale, pad_x, pad_y = preprocess(frame)

        infer_start = time.perf_counter()

        outputs = session.run(
            [output_name],
            {input_name: input_tensor}
        )

        infer_end = time.perf_counter()

        inference_time_ms = (infer_end - infer_start) * 1000

        detections = postprocess(
            outputs[0],
            frame.shape,
            scale,
            pad_x,
            pad_y
        )

        annotated_frame = draw_detections(frame.copy(), detections)

        last_alarm_time = handle_alarm(
            annotated_frame,
            detections,
            last_alarm_time,
            mqtt_client
        )

        frame_count += 1
        elapsed = time.time() - fps_start_time

        if elapsed >= 1.0:
            current_fps = frame_count / elapsed
            frame_count = 0
            fps_start_time = time.time()

        info_text = f"FPS: {current_fps:.2f} | Inference: {inference_time_ms:.2f} ms"

        cv2.putText(
            annotated_frame,
            info_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        cv2.imshow("ONNX Runtime Helmet Alarm System", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    if mqtt_client is not None:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

    print("系统已退出")


if __name__ == "__main__":
    main()