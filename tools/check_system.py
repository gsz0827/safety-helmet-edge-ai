import os
import sys
import time
import socket
import cv2

# 获取项目根目录：tools/check_system.py 的上一级目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 把项目根目录加入 Python 搜索路径，方便导入 src
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yaml")


def print_ok(message):
    print(f"[OK] {message}")


def print_fail(message):
    print(f"[FAIL] {message}")


def print_warn(message):
    print(f"[WARN] {message}")


def check_imports():
    print("\n===== 1. 检查 Python 依赖 =====")

    packages = [
        ("cv2", "opencv-python"),
        ("numpy", "numpy"),
        ("yaml", "PyYAML"),
        ("onnxruntime", "onnxruntime"),
        ("paho.mqtt.client", "paho-mqtt"),
        ("flask", "flask"),
    ]

    all_ok = True

    for module_name, package_name in packages:
        try:
            __import__(module_name)
            print_ok(f"{package_name} 已安装")
        except ImportError:
            print_fail(f"{package_name} 未安装")
            all_ok = False

    return all_ok


def load_config():
    print("\n===== 2. 检查 config.yaml =====")

    try:
        from edge.config_loader import load_config
        config = load_config(CONFIG_PATH)
        print_ok(f"config.yaml 读取成功: {CONFIG_PATH}")
    except Exception as e:
        print_fail(f"config.yaml 读取失败: {e}")
        return None

    required_sections = [
        "device",
        "model",
        "video",
        "detect",
        "alarm",
        "mqtt",
    ]

    all_ok = True

    for section in required_sections:
        if section in config:
            print_ok(f"配置项 [{section}] 存在")
        else:
            print_fail(f"配置项 [{section}] 缺失")
            all_ok = False

    if not all_ok:
        return None

    return config


def check_model(config):
    print("\n===== 3. 检查模型文件 =====")

    model_path = config["model"]["model_path"]

    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / 1024 / 1024
        print_ok(f"模型文件存在: {model_path}")
        print_ok(f"模型大小: {size_mb:.2f} MB")
        return True

    print_fail(f"模型文件不存在: {model_path}")
    return False


def check_alarm_paths(config):
    print("\n===== 4. 检查告警目录 =====")

    alarm_dir = config["alarm"]["alarm_dir"]
    alarm_log_file = config["alarm"]["alarm_log_file"]

    try:
        os.makedirs(alarm_dir, exist_ok=True)
        print_ok(f"告警图片目录可用: {alarm_dir}")
    except Exception as e:
        print_fail(f"告警图片目录不可用: {e}")
        return False

    try:
        with open(alarm_log_file, "a", encoding="utf-8") as f:
            pass
        print_ok(f"告警日志文件可写: {alarm_log_file}")
    except Exception as e:
        print_fail(f"告警日志文件不可写: {e}")
        return False

    return True


def check_video_stream(config):
    print("\n===== 5. 检查 DroidCam 视频流 =====")

    video_url = config["video"]["video_url"]
    print("视频流地址:", video_url)

    cap = cv2.VideoCapture(video_url)

    if not cap.isOpened():
        print_fail("视频流无法打开")
        print_warn("请检查 DroidCam 手机端是否打开，以及 config.yaml 中的 video_url 是否为当前 IP")
        return False

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print_fail("视频流打开了，但无法读取画面")
        return False

    print_ok(f"视频流读取成功，画面尺寸: {frame.shape}")
    return True


def check_mqtt(config):
    print("\n===== 6. 检查 MQTT 连接 =====")

    import paho.mqtt.client as mqtt

    mqtt_config = config["mqtt"]

    if not mqtt_config.get("enable", True):
        print_warn("MQTT 当前配置为未启用")
        return True

    broker_host = mqtt_config["broker_host"]
    broker_port = mqtt_config["broker_port"]
    topic = mqtt_config["topic"]

    print("Broker:", broker_host)
    print("Port:", broker_port)
    print("Topic:", topic)

    try:
        socket.create_connection((broker_host, broker_port), timeout=5).close()
        print_ok("Broker 网络端口可连接")
    except Exception as e:
        print_fail(f"Broker 网络端口不可连接: {e}")
        return False

    try:
        try:
            client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=f"system_check_{int(time.time())}",
                protocol=mqtt.MQTTv311
            )
        except AttributeError:
            client = mqtt.Client(
                client_id=f"system_check_{int(time.time())}",
                protocol=mqtt.MQTTv311
            )

        client.connect(broker_host, broker_port, keepalive=60)
        client.disconnect()
        print_ok("MQTT 客户端连接成功")
        return True

    except Exception as e:
        print_fail(f"MQTT 客户端连接失败: {e}")
        return False


def check_dashboard_config(config):
    print("\n===== 7. 检查 Web 看板配置 =====")

    dashboard = config.get("dashboard", {})
    host = dashboard.get("host", "127.0.0.1")
    port = dashboard.get("port", 5000)

    print_ok(f"Web 看板地址: http://{host}:{port}")
    return True


def check_database(config):
    print("\n===== 8. 检查 SQLite 告警数据库 =====")

    try:
        from edge.alarm_database import AlarmDatabase

        db = AlarmDatabase(config)
        count = db.count_alarms()

        db_path = config.get("database", {}).get("db_path", "alarm_records.db")

        print_ok(f"数据库可用: {db_path}")
        print_ok(f"当前告警记录数: {count}")
        return True

    except Exception as e:
        print_fail(f"数据库检查失败: {e}")
        return False


def main():
    print("安全帽违规告警系统自检开始")

    results = []

    results.append(check_imports())

    config = load_config()

    if config is None:
        print("\n系统自检失败：config.yaml 不可用")
        return

    results.append(check_model(config))
    results.append(check_alarm_paths(config))
    results.append(check_video_stream(config))
    results.append(check_mqtt(config))
    results.append(check_dashboard_config(config))
    results.append(check_database(config))

    print("\n===== 自检结果汇总 =====")

    if all(results):
        print_ok("系统自检通过，可以启动项目演示")
    else:
        print_fail("系统自检未完全通过，请根据上面的 FAIL 信息排查")


if __name__ == "__main__":
    main()