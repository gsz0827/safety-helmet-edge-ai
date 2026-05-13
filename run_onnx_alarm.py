import time

from src.config_loader import load_config
from src.camera_stream import CameraStream
from src.onnx_detector import OnnxDetector
from src.mqtt_publisher import MqttPublisher
from src.alarm_manager import AlarmManager
from src.alarm_database import AlarmDatabase
from src.visualizer import Visualizer


def main():
    config = load_config("config.yaml")

    camera = CameraStream(config)
    detector = OnnxDetector(config)
    mqtt_publisher = MqttPublisher(config)
    alarm_database = AlarmDatabase(config)
    alarm_manager = AlarmManager(config, mqtt_publisher, alarm_database)
    visualizer = Visualizer()

    mqtt_publisher.connect()
    camera.open()

    print("模块化 ONNX Runtime 安全帽违规告警系统已启动。按 q 退出。")

    frame_count = 0
    fps_start_time = time.time()
    current_fps = 0.0

    try:
        while True:
            frame = camera.read()

            if frame is None:
                print("读取视频帧失败。")
                break

            detections, inference_time_ms = detector.detect(frame)

            annotated_frame = frame.copy()
            annotated_frame = visualizer.draw_detections(annotated_frame, detections)
            annotated_frame = visualizer.draw_status(
                annotated_frame,
                current_fps,
                inference_time_ms
            )

            alarm_manager.handle(
                annotated_frame,
                detections,
                model_type="onnxruntime_modular"
            )

            frame_count += 1
            elapsed = time.time() - fps_start_time

            if elapsed >= 1.0:
                current_fps = frame_count / elapsed
                frame_count = 0
                fps_start_time = time.time()

            visualizer.show(
                "Modular ONNX Runtime Helmet Alarm System",
                annotated_frame
            )

            if visualizer.should_quit():
                break

    finally:
        camera.release()
        mqtt_publisher.close()
        visualizer.close()
        print("系统已退出。")


if __name__ == "__main__":
    main()