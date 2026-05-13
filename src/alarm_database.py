import sqlite3
from datetime import datetime


class AlarmDatabase:
    def __init__(self, config):
        db_config = config.get("database", {})

        self.enable = db_config.get("enable", True)
        self.db_path = db_config.get("db_path", "alarm_records.db")

        if self.enable:
            self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alarm_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    model_type TEXT,
                    event TEXT,
                    confidence REAL,
                    image_path TEXT,
                    timestamp TEXT,
                    created_at TEXT,
                    status TEXT DEFAULT 'pending',
                    handled_at TEXT,
                    handler TEXT,
                    remark TEXT
                )
                """
            )

            conn.commit()

        # 表创建完成后，再检查旧数据库是否缺少新字段
        self.ensure_columns()

        print(f"告警数据库已初始化: {self.db_path}")

    def insert_alarm(self, alarm_info):
        if not self.enable:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO alarm_records (
                    device_id,
                    model_type,
                    event,
                    confidence,
                    image_path,
                    timestamp,
                    created_at,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alarm_info.get("device_id", ""),
                    alarm_info.get("model_type", ""),
                    alarm_info.get("event", ""),
                    alarm_info.get("confidence", 0.0),
                    alarm_info.get("image_path", ""),
                    alarm_info.get("timestamp", ""),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "pending"
                )
            )

            conn.commit()

    def get_recent_alarms(self, limit=100):
        if not self.enable:
            return []

        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    device_id,
                    model_type,
                    event,
                    confidence,
                    image_path,
                    timestamp,
                    created_at
                FROM alarm_records
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )

            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def count_alarms(self):
        if not self.enable:
            return 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM alarm_records")
            count = cursor.fetchone()[0]

        return count
    
    def get_alarms_filtered(self, event="", model_type="", status="", min_conf=None, limit=100):
        if not self.enable:
            return []

        query = """
            SELECT
                id,
                device_id,
                model_type,
                event,
                confidence,
                image_path,
                timestamp,
                created_at,
                status,
                handled_at,
                handler,
                remark
            FROM alarm_records
            WHERE 1 = 1
        """

        params = []

        if event:
            query += " AND event = ?"
            params.append(event)

        if model_type:
            query += " AND model_type = ?"
            params.append(model_type)

        if status:
            query += " AND status = ?"
            params.append(status)

        if min_conf is not None:
            query += " AND confidence >= ?"
            params.append(min_conf)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_summary(self):
        if not self.enable:
            return {
                "total_count": 0,
                "today_count": 0,
                "pending_count": 0,
                "handled_count": 0,
                "avg_confidence": 0,
                "latest_time": ""
            }

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM alarm_records")
            total_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM alarm_records
                WHERE date(timestamp) = date('now', 'localtime')
                """
            )
            today_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM alarm_records WHERE status = 'pending'")
            pending_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM alarm_records WHERE status = 'handled'")
            handled_count = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(confidence) FROM alarm_records")
            avg_confidence = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT timestamp
                FROM alarm_records
                ORDER BY id DESC
                LIMIT 1
                """
            )

            row = cursor.fetchone()
            latest_time = row[0] if row else ""

            return {
                "total_count": total_count,
                "today_count": today_count,
                "pending_count": pending_count,
                "handled_count": handled_count,
                "avg_confidence": round(avg_confidence or 0, 4),
                "latest_time": latest_time
            }

    def get_daily_counts(self, days=7):
        if not self.enable:
            return []

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    date(timestamp) AS alarm_date,
                    COUNT(*) AS alarm_count
                FROM alarm_records
                WHERE date(timestamp) >= date('now', 'localtime', ?)
                GROUP BY date(timestamp)
                ORDER BY alarm_date ASC
                """,
                (f"-{days - 1} days",)
            )

            rows = cursor.fetchall()

        count_map = {row[0]: row[1] for row in rows}

        from datetime import datetime, timedelta

        today = datetime.now().date()
        result = []

        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")

            result.append({
                "date": day_str,
                "count": count_map.get(day_str, 0)
            })

        return result

    def ensure_columns(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("PRAGMA table_info(alarm_records)")
            existing_columns = [row[1] for row in cursor.fetchall()]

            new_columns = {
                "status": "TEXT DEFAULT 'pending'",
                "handled_at": "TEXT",
                "handler": "TEXT",
                "remark": "TEXT"
            }

            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    cursor.execute(
                        f"ALTER TABLE alarm_records ADD COLUMN {column_name} {column_type}"
                    )

            conn.commit()

    def handle_alarm(self, alarm_id, handler="admin", remark=""):
        if not self.enable:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE alarm_records
                SET
                    status = ?,
                    handled_at = ?,
                    handler = ?,
                    remark = ?
                WHERE id = ?
                """,
                (
                    "handled",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    handler,
                    remark,
                    alarm_id
                )
            )

            conn.commit()

            return cursor.rowcount > 0

    def mark_pending(self, alarm_id):
        if not self.enable:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE alarm_records
                SET
                    status = 'pending',
                    handled_at = NULL,
                    handler = NULL,
                    remark = NULL
                WHERE id = ?
                """,
                (alarm_id,)
            )

            conn.commit()

            return cursor.rowcount > 0

    def get_alarm_by_id(self, alarm_id):
        if not self.enable:
            return None

        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    device_id,
                    model_type,
                    event,
                    confidence,
                    image_path,
                    timestamp,
                    created_at,
                    status,
                    handled_at,
                    handler,
                    remark
                FROM alarm_records
                WHERE id = ?
                """,
                (alarm_id,)
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)