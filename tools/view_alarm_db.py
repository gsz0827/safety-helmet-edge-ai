import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config_loader import load_config
from src.alarm_database import AlarmDatabase


def main():
    config = load_config(os.path.join(PROJECT_ROOT, "config.yaml"))

    db = AlarmDatabase(config)

    alarms = db.get_recent_alarms(limit=20)

    print(f"最近 {len(alarms)} 条告警记录：")

    for alarm in alarms:
        print(
            f"[{alarm['id']}] "
            f"{alarm['timestamp']} | "
            f"{alarm['device_id']} | "
            f"{alarm['model_type']} | "
            f"{alarm['event']} | "
            f"conf={alarm['confidence']} | "
            f"{alarm['image_path']}"
        )


if __name__ == "__main__":
    main()