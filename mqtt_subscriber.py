import json
import uuid
import paho.mqtt.client as mqtt
from src.config_loader import load_config


config = load_config("config.yaml")

mqtt_config = config["mqtt"]

BROKER_HOST = mqtt_config["broker_host"]
BROKER_PORT = mqtt_config["broker_port"]
TOPIC = mqtt_config["topic"]

CLIENT_ID = f"helmet_alarm_subscriber_{uuid.uuid4().hex[:8]}"


def on_connect(client, userdata, flags, reason_code, properties=None):
    print("MQTT 订阅端已连接。")
    print("Broker:", BROKER_HOST)
    print("订阅主题:", TOPIC)
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="ignore")

    print("\n收到 MQTT 告警消息：")
    print("Topic:", msg.topic)

    try:
        data = json.loads(payload)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(payload)


def create_client():
    try:
        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=CLIENT_ID,
            protocol=mqtt.MQTTv311
        )
    except AttributeError:
        client = mqtt.Client(
            client_id=CLIENT_ID,
            protocol=mqtt.MQTTv311
        )

    client.on_connect = on_connect
    client.on_message = on_message

    return client


def main():
    client = create_client()

    print("正在连接 MQTT Broker...")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n订阅端退出。")
        client.disconnect()


if __name__ == "__main__":
    main()