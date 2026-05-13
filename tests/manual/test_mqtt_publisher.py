import time
from src.config_loader import load_config
from src.mqtt_publisher import MqttPublisher


config = load_config("config.yaml")

mqtt_publisher = MqttPublisher(config)
mqtt_publisher.connect()

alarm_info = {
    "device_id": config["device"]["device_id"],
    "model_type": "test",
    "event": "no_helmet",
    "confidence": 0.999,
    "image_path": "alarm_results/test_alarm.jpg",
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
}

mqtt_publisher.publish(alarm_info)
mqtt_publisher.close()