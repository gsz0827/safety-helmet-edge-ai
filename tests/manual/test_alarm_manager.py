import cv2
import numpy as np
from src.config_loader import load_config
from src.mqtt_publisher import MqttPublisher
from src.alarm_manager import AlarmManager


config = load_config("config.yaml")

mqtt_publisher = MqttPublisher(config)
mqtt_publisher.connect()

alarm_manager = AlarmManager(config, mqtt_publisher)

# 创建一张测试图片
frame = np.zeros((480, 640, 3), dtype=np.uint8)

cv2.putText(
    frame,
    "test no_helmet alarm",
    (50, 240),
    cv2.FONT_HERSHEY_SIMPLEX,
    1.0,
    (0, 0, 255),
    2
)

# 模拟检测结果
detections = [
    {
        "class_name": "no_helmet",
        "confidence": 0.999,
        "box": [100, 100, 300, 300]
    }
]

alarm_info = alarm_manager.handle(
    frame,
    detections,
    model_type="test"
)

if alarm_info is not None:
    print("告警模块测试成功。")
else:
    print("没有触发告警。")

mqtt_publisher.close()