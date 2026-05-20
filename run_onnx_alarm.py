import time

from edge.config_loader import load_config
from edge.multi_camera_manager import MultiCameraManager
from edge.onnx_detector import OnnxDetector
from edge.mqtt_publisher import MqttPublisher
from edge.alarm_manager import AlarmManager
from edge.alarm_database import AlarmDatabase
from edge.visualizer import Visualizer


def main():
    config = load_config("config.yaml")

    camera_manager = MultiCameraManager(config)
    detector = OnnxDetector(config)
    mqtt_publisher = MqttPublisher(config)
    alarm_database = AlarmDatabase(config)
    alarm_manager = AlarmManager(config, mqtt_publisher, alarm_database)
    visualizer = Visualizer()

    mqtt_publisher.connect()
    camera_manager.open_all()

    print("多摄像头 ONNX Runtime 安全帽违规告警系统已启动。按 q 退出。")

    frame_count_map = {}
    fps_start_time_map = {}
    current_fps_map = {}

    for camera in camera_manager.cameras:
        frame_count_map[camera.camera_id] = 0
        fps_start_time_map[camera.camera_id] = time.time()
        current_fps_map[camera.camera_id] = 0.0

    try:
        while True:
            frame_items = camera_manager.read_all()

            if not frame_items:
                print("所有摄像头当前帧读取失败，等待下一轮读取。")
                time.sleep(0.1)
                continue

            for item in frame_items:
                camera_id = item["camera_id"]
                camera_name = item["camera_name"]
                source_url = item["source_url"]
                frame = item["frame"]

                detections, inference_time_ms = detector.detect(frame)

                annotated_frame = frame.copy()
                annotated_frame = visualizer.draw_detections(
                    annotated_frame,
                    detections,
                )

                frame_count_map[camera_id] += 1
                elapsed = time.time() - fps_start_time_map[camera_id]

                if elapsed >= 1.0:
                    current_fps_map[camera_id] = frame_count_map[camera_id] / elapsed
                    frame_count_map[camera_id] = 0
                    fps_start_time_map[camera_id] = time.time()

                current_fps = current_fps_map[camera_id]

                annotated_frame = visualizer.draw_status(
                    annotated_frame,
                    current_fps,
                    inference_time_ms,
                )

                alarm_manager.handle(
                    annotated_frame,
                    detections,
                    model_type="onnxruntime_multi_camera",
                    camera_id=camera_id,
                    camera_name=camera_name,
                    source_url=source_url,
                    inference_time_ms=inference_time_ms,
                    fps=current_fps,
                )

                window_name = f"Helmet Alarm - {camera_id} - {camera_name}"
                visualizer.show(window_name, annotated_frame)

            if visualizer.should_quit():
                break

    finally:
        camera_manager.release_all()
        mqtt_publisher.close()
        visualizer.close()
        print("系统已退出。")


if __name__ == "__main__":
    main()