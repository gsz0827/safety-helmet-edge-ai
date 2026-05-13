import json
import uuid
import paho.mqtt.client as mqtt


class MqttPublisher:
    def __init__(self, config):
        mqtt_config = config["mqtt"]

        self.enable = mqtt_config["enable"]
        self.broker_host = mqtt_config["broker_host"]
        self.broker_port = mqtt_config["broker_port"]
        self.topic = mqtt_config["topic"]

        self.client_id = f"onnx_alarm_pub_{uuid.uuid4().hex[:8]}"
        self.client = None

    def connect(self):
        if not self.enable:
            print("MQTT 未启用。")
            return

        try:
            try:
                self.client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION2,
                    client_id=self.client_id,
                    protocol=mqtt.MQTTv311
                )
            except AttributeError:
                self.client = mqtt.Client(
                    client_id=self.client_id,
                    protocol=mqtt.MQTTv311
                )

            self.client.connect(
                self.broker_host,
                self.broker_port,
                keepalive=60
            )

            self.client.loop_start()

            print("MQTT 发布端已连接")
            print("Broker:", self.broker_host)
            print("Topic:", self.topic)

        except Exception as e:
            print("MQTT 连接失败，将只进行本地告警。")
            print("错误信息:", e)
            self.client = None

    def publish(self, alarm_info):
        if not self.enable or self.client is None:
            return False

        payload = json.dumps(alarm_info, ensure_ascii=False)

        result = self.client.publish(
            self.topic,
            payload=payload,
            qos=1
        )

        result.wait_for_publish(timeout=5)

        if result.is_published():
            print("MQTT 告警已确认发布")
            return True

        print("MQTT 告警可能未成功发布")
        return False

    def close(self):
        if self.client is not None:
            self.client.loop_stop()
            self.client.disconnect()
            print("MQTT 发布端已断开")