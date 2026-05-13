import cv2
import time
from src.config_loader import load_config
from src.onnx_detector import OnnxDetector


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


config = load_config("config.yaml")

video_url = config["video"]["video_url"]

detector = OnnxDetector(config)

cap = cv2.VideoCapture(video_url)

if not cap.isOpened():
    print("无法打开视频流，请检查 config.yaml 中的 video_url。")
    exit()

print("ONNX Detector 模块测试启动成功，按 q 退出。")

frame_count = 0
fps_start_time = time.time()
current_fps = 0.0

while True:
    ret, frame = cap.read()

    if not ret:
        print("读取视频帧失败。")
        break

    detections, inference_time_ms = detector.detect(frame)

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

    cv2.imshow("Test ONNX Detector Module", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("测试结束。")