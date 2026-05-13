import cv2
import time
from statistics import mean
from ultralytics import YOLO

VIDEO_URL = "http://192.168.1.102:4747/mjpegfeed"

MODEL_LIST = {
    "PyTorch .pt": r"runs\detect\helmet_final\weights\best.pt",
    "ONNX": r"runs\detect\helmet_final\weights\best.onnx",
}

CONF_THRESHOLD = 0.5
WARMUP_FRAMES = 20
TEST_FRAMES = 200


def open_video_stream(url, retries=5, delay=3):
    for attempt in range(1, retries + 1):
        print(f"尝试打开视频流，第 {attempt}/{retries} 次...")
        cap = cv2.VideoCapture(url)

        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("视频流打开成功。")
                return cap

        cap.release()
        print(f"视频流打开失败，等待 {delay} 秒后重试...")
        time.sleep(delay)

    return None


def benchmark(model_name, model_path):
    print(f"\n===== Testing {model_name} =====")
    print("Model:", model_path)

    model = YOLO(model_path)

    cap = open_video_stream(VIDEO_URL)

    if cap is None:
        print("无法打开视频流，请检查 DroidCam 地址或是否被其他程序占用。")
        return

    total_times = []
    inference_times = []

    frame_count = 0
    valid_count = 0

    while valid_count < TEST_FRAMES:
        ret, frame = cap.read()

        if not ret:
            print("读取视频帧失败，跳过。")
            continue

        start_time = time.perf_counter()
        results = model.predict(frame, conf=CONF_THRESHOLD, verbose=False)
        end_time = time.perf_counter()

        frame_count += 1

        if frame_count <= WARMUP_FRAMES:
            continue

        total_time_ms = (end_time - start_time) * 1000
        total_times.append(total_time_ms)

        speed_info = results[0].speed
        inference_times.append(speed_info["inference"])

        valid_count += 1

        if valid_count % 20 == 0:
            print(f"已测试 {valid_count}/{TEST_FRAMES} 帧")

    cap.release()
    time.sleep(5)

    avg_total = mean(total_times)
    avg_inference = mean(inference_times)
    fps = 1000 / avg_total

    print(f"\n{model_name} 测试结果：")
    print(f"平均端到端耗时: {avg_total:.2f} ms/frame")
    print(f"平均 inference 时间: {avg_inference:.2f} ms/frame")
    print(f"估算 FPS: {fps:.2f}")


if __name__ == "__main__":
    for name, path in MODEL_LIST.items():
        benchmark(name, path)