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
        self.last_alarm_time = 0
        self.alarm_frame_count = 0

        os.makedirs(self.alarm_dir, exist_ok=True)

    def check_alarm(self, detections):
        """
        检查当前帧是否存在 no_helmet。
        detections 格式示例：
        [
            {
                "class_name": "no_helmet",
                "confidence": 0.82,
                "box": [x1, y1, x2, y2]
            }
        ]
        """
        has_alarm = False
        max_conf = 0.0

        for det in detections:
            if det["class_name"] == self.alarm_class_name:
                has_alarm = True
                max_conf = max(max_conf, det["confidence"])

        return has_alarm, max_conf

    def should_alarm(self):
        current_time = time.time()

        if current_time - self.last_alarm_time >= self.alarm_cooldown:
            self.last_alarm_time = current_time
            return True

        return False

    def handle(self, frame, detections, model_type="onnxruntime"):
        """
        如果当前帧触发告警，则保存图片、写日志、发送 MQTT。
        """
        has_alarm, max_conf = self.check_alarm(detections)

        has_alarm, max_conf = self.check_alarm(detections)

        if has_alarm:
            self.alarm_frame_count += 1
        else:
            self.alarm_frame_count = 0
            return None

        if self.alarm_frame_count < self.alarm_confirm_frames:
            print(
                f"检测到 {self.alarm_class_name}，"
                f"连续帧数 {self.alarm_frame_count}/{self.alarm_confirm_frames}"
            )
            return None

        if not self.should_alarm():
            return None

        self.alarm_frame_count = 0

        timestamp_file = time.strftime("%Y%m%d_%H%M%S")
        timestamp_text = time.strftime("%Y-%m-%d %H:%M:%S")

        image_name = f"{model_type}_no_helmet_alarm_{timestamp_file}.jpg"
        image_path = os.path.join(self.alarm_dir, image_name)

        cv2.imwrite(image_path, frame)

        alarm_info = {
            "device_id": self.device_id,
            "model_type": model_type,
            "event": self.alarm_class_name,
            "confidence": round(max_conf, 4),
            "image_path": image_path,
            "timestamp": timestamp_text
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