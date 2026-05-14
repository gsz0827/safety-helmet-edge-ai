import os
import cv2
import time
import json


class AlarmManager:
    def __init__(self, config, mqtt_publisher=None, alarm_database=None):
        self.device_id = config["device"]["device_id"]

        alarm_config = config["alarm"]
        self.alarm_class_name = alarm_config["alarm_class_name"]
        self.alarm_cooldown = alarm_config["alarm_cooldown"]
        self.alarm_confirm_frames = alarm_config.get("alarm_confirm_frames", 1)
        self.alarm_dir = alarm_config["alarm_dir"]
        self.alarm_log_file = alarm_config["alarm_log_file"]

        self.mqtt_publisher = mqtt_publisher
        self.alarm_database = alarm_database

        # 多摄像头状态：每个 camera_id 独立维护冷却时间和连续帧计数
        self.last_alarm_time_map = {}
        self.alarm_frame_count_map = {}

        os.makedirs(self.alarm_dir, exist_ok=True)

    def check_alarm(self, detections):
        has_alarm = False
        max_conf = 0.0

        for det in detections:
            if det["class_name"] == self.alarm_class_name:
                has_alarm = True
                max_conf = max(max_conf, det["confidence"])

        return has_alarm, max_conf

    def should_alarm(self, camera_id):
        current_time = time.time()
        last_alarm_time = self.last_alarm_time_map.get(camera_id, 0)

        if current_time - last_alarm_time >= self.alarm_cooldown:
            self.last_alarm_time_map[camera_id] = current_time
            return True

        return False

    def handle(
        self,
        frame,
        detections,
        model_type="onnxruntime",
        camera_id="cam_01",
        camera_name="default",
        source_url="",
        inference_time_ms=0.0,
        fps=0.0,
    ):
        has_alarm, max_conf = self.check_alarm(detections)

        if has_alarm:
            self.alarm_frame_count_map[camera_id] = (
                self.alarm_frame_count_map.get(camera_id, 0) + 1
            )
        else:
            self.alarm_frame_count_map[camera_id] = 0
            return None

        current_count = self.alarm_frame_count_map.get(camera_id, 0)

        if current_count < self.alarm_confirm_frames:
            print(
                f"[{camera_id} - {camera_name}] 检测到 {self.alarm_class_name}，"
                f"连续帧数 {current_count}/{self.alarm_confirm_frames}"
            )
            return None

        if not self.should_alarm(camera_id):
            return None

        self.alarm_frame_count_map[camera_id] = 0

        timestamp_file = time.strftime("%Y%m%d_%H%M%S")
        timestamp_text = time.strftime("%Y-%m-%d %H:%M:%S")

        image_name = (
            f"{model_type}_{camera_id}_{self.alarm_class_name}_alarm_{timestamp_file}.jpg"
        )
        image_path = os.path.join(self.alarm_dir, image_name)

        cv2.imwrite(image_path, frame)

        alarm_info = {
            "device_id": self.device_id,
            "camera_id": camera_id,
            "camera_name": camera_name,
            "source_url": source_url,
            "model_type": model_type,
            "event": self.alarm_class_name,
            "confidence": round(max_conf, 4),
            "image_path": image_path,
            "timestamp": timestamp_text,
            "inference_time_ms": round(float(inference_time_ms), 2),
            "fps": round(float(fps), 2),
        }

        print("\n发现未戴安全帽违规：")
        print(json.dumps(alarm_info, ensure_ascii=False, indent=2))

        with open(self.alarm_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(alarm_info, ensure_ascii=False) + "\n")

        if self.alarm_database is not None:
            self.alarm_database.insert_alarm(alarm_info)

        if self.mqtt_publisher is not None:
            self.mqtt_publisher.publish(alarm_info)

        return alarm_info