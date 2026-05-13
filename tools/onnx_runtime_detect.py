import cv2
import time
import numpy as np
import onnxruntime as ort


# =========================
# 配置区
# =========================

MODEL_PATH = r"runs\detect\helmet_final\weights\best.onnx"

# DroidCam 当前视频流地址，如果 IP 变化，这里要改
VIDEO_URL = "http://192.168.1.107:4747/mjpegfeed"

# 类别名称，需要与你训练时 helmet.yaml 中的类别顺序一致
CLASS_NAMES = ["helmet", "no_helmet"]

INPUT_SIZE = 640
CONF_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45


# =========================
# 图像预处理：letterbox
# =========================

def letterbox(image, new_shape=640, color=(114, 114, 114)):
    """
    保持原图宽高比，将图像缩放并填充到 new_shape x new_shape。
    返回：
    - padded image
    - 缩放比例 ratio
    - padding 偏移量 dw, dh
    """
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
    """
    OpenCV BGR 图像 -> ONNX 输入张量
    """
    img, scale, pad_x, pad_y = letterbox(frame, INPUT_SIZE)

    # BGR 转 RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # HWC -> CHW
    img = img.transpose(2, 0, 1)

    # uint8 -> float32, 归一化到 0~1
    img = img.astype(np.float32) / 255.0

    # 增加 batch 维度：1 x 3 x 640 x 640
    img = np.expand_dims(img, axis=0)

    return img, scale, pad_x, pad_y


# =========================
# 后处理
# =========================

def xywh_to_xyxy(box):
    """
    将中心点格式 xywh 转为左上右下 xyxy
    """
    x, y, w, h = box

    x1 = x - w / 2
    y1 = y - h / 2
    x2 = x + w / 2
    y2 = y + h / 2

    return [x1, y1, x2, y2]


def postprocess(output, original_shape, scale, pad_x, pad_y):
    """
    解析 YOLOv8 ONNX 输出，返回最终检测框。
    返回格式：
    [
        {
            "class_id": int,
            "class_name": str,
            "confidence": float,
            "box": [x1, y1, x2, y2]
        }
    ]
    """
    # output 常见形状：
    # 1 x (4 + num_classes) x 8400
    # 也可能是 1 x 8400 x (4 + num_classes)
    predictions = output[0]

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

        # YOLO 输出是基于 640x640 letterbox 图像的 xywh
        x1, y1, x2, y2 = xywh_to_xyxy(box)

        # 去掉 padding，再除以缩放比例，映射回原图
        x1 = (x1 - pad_x) / scale
        y1 = (y1 - pad_y) / scale
        x2 = (x2 - pad_x) / scale
        y2 = (y2 - pad_y) / scale

        # 限制边界
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

    # OpenCV NMSBoxes 需要 xywh 格式
    indices = cv2.dnn.NMSBoxes(
        boxes,
        scores,
        CONF_THRESHOLD,
        IOU_THRESHOLD
    )

    detections = []

    if len(indices) > 0:
        for i in indices.flatten():
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

        label = f"{class_name} {confidence:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.putText(
            frame,
            label,
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    return frame


# =========================
# 主程序
# =========================

def main():
    print("正在加载 ONNX 模型...")
    print("Model:", MODEL_PATH)

    providers = ["CPUExecutionProvider"]

    session = ort.InferenceSession(
        MODEL_PATH,
        providers=providers
    )

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    print("ONNX Runtime providers:", session.get_providers())
    print("Input name:", input_name)
    print("Output name:", output_name)

    cap = cv2.VideoCapture(VIDEO_URL)

    if not cap.isOpened():
        print("无法打开视频流，请检查 DroidCam 地址是否正确。")
        return

    print("ONNX Runtime 实时检测启动成功，按 q 退出。")

    frame_count = 0
    fps_start_time = time.time()
    current_fps = 0.0

    while True:
        ret, frame = cap.read()

        if not ret:
            print("读取视频帧失败。")
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

        frame = draw_detections(frame, detections)

        frame_count += 1
        elapsed = time.time() - fps_start_time

        if elapsed >= 1.0:
            current_fps = frame_count / elapsed
            frame_count = 0
            fps_start_time = time.time()

        info_text = f"FPS: {current_fps:.2f} | Inference: {inference_time_ms:.2f} ms"

        cv2.putText(
            frame,
            info_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        cv2.imshow("ONNX Runtime Helmet Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("程序已退出。")


if __name__ == "__main__":
    main()