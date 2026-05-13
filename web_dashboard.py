import os
import csv
import io
from flask import Flask, send_from_directory, render_template_string, request, redirect, url_for, Response
from src.config_loader import load_config
from src.alarm_database import AlarmDatabase


config = load_config("config.yaml")

ALARM_DIR = config["alarm"]["alarm_dir"]
DASHBOARD_HOST = config.get("dashboard", {}).get("host", "127.0.0.1")
DASHBOARD_PORT = config.get("dashboard", {}).get("port", 5000)
DASHBOARD_AUTO_REFRESH_SECONDS = config.get("dashboard", {}).get("auto_refresh_seconds", 5)

alarm_database = AlarmDatabase(config)

app = Flask(__name__)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>安全帽违规告警看板</title>
    <style>
        body {
            font-family: Arial, "Microsoft YaHei", sans-serif;
            margin: 30px;
            background: #f5f6fa;
            color: #222;
        }

        h1 {
            margin-bottom: 10px;
        }

        .top-dashboard {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 480px;
            gap: 18px;
            margin: 20px 0;
            align-items: stretch;
        }

        .left-dashboard {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 16px;
            min-width: 0;
            height: 100%;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
            margin: 0;
            align-content: start;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 18px;
            min-height: 96px;
            box-sizing: border-box;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .card-title {
            color: #666;
            font-size: 14px;
            margin-bottom: 8px;
        }

        .card-value {
            font-size: 24px;
            font-weight: bold;
        }

        .chart-box {
            background: white;
            border-radius: 12px;
            padding: 18px 22px;
            margin: 0;
            box-sizing: border-box;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .chart-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 12px;
        }

        .bar-chart {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            align-items: end;
            gap: 6px;
            height: 105px;
            border-bottom: 1px solid #ddd;
            padding: 10px 4px 0 4px;
        }

        .bar-item {
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
        }

        .bar {
            width: 22px;
            min-height: 4px;
            background: #1677ff;
            border-radius: 6px 6px 0 0;
        }

        .bar-count {
            font-size: 13px;
            margin-bottom: 6px;
            color: #333;
        }

        .bar-date {
            font-size: 12px;
            color: #666;
            margin-top: 6px;
        }

        @media (max-width: 1300px) {
            .top-dashboard {
                grid-template-columns: 1fr;
            }

            .cards {
                grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            }
        }

        .filter-box {
            background: white;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            align-self: stretch;
        }

        .filter-form {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: nowrap;
        }

        .filter-item {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
        }

        .filter-item label {
            color: #333;
            font-size: 14px;
        }

        .filter-item input,
        .filter-item select {
            height: 34px;
            padding: 6px 10px;
            border: 1px solid #dcdfe6;
            border-radius: 8px;
            box-sizing: border-box;
            background: white;
            font-size: 14px;
        }

        .filter-item select[name="event"] {
            width: 82px;
        }

        .filter-item input[name="model_type"] {
            width: 145px;
        }

        .filter-item input[name="min_conf"] {
            width: 78px;
        }

        .filter-item input[name="limit"] {
            width: 70px;
        }

        .filter-item select[name="status"] {
            width: 82px;
        }

        .filter-actions {
            margin-left: auto;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            white-space: nowrap;
        }

        .filter-button {
            height: 34px;
            padding: 0 16px;
            border: none;
            border-radius: 8px;
            background: #1677ff;
            color: white;
            cursor: pointer;
            font-size: 14px;
        }

        .filter-link {
            height: 34px;
            padding: 0 10px;
            border-radius: 8px;
            color: #1677ff;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            font-size: 14px;
        }

        .filter-link:hover {
            background: #f0f6ff;
        }

        .filter-export {
            background: #f0f6ff;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        th, td {
            padding: 12px;
            border-bottom: 1px solid #eee;
            text-align: left;
            vertical-align: middle;
        }

        th {
            background: #20232a;
            color: white;
        }

        tr:hover {
            background: #f0f2f5;
        }

        .tag {
            padding: 4px 8px;
            background: #ff4d4f;
            color: white;
            border-radius: 6px;
            font-size: 13px;
        }

        .latest-row td {
            background: #fff7e6;
        }

        .latest-badge {
            display: inline-block;
            margin-left: 8px;
            padding: 2px 6px;
            background: #fa8c16;
            color: white;
            border-radius: 6px;
            font-size: 12px;
        }

        .refresh-info {
            color: #666;
            font-size: 13px;
            margin-top: -4px;
            margin-bottom: 12px;
        }

        .status-pending {
            color: #ff4d4f;
            font-weight: bold;
        }

        .status-handled {
            color: #52c41a;
            font-weight: bold;
        }

        .action-form {
            display: inline-block;
            margin: 0;
        }

        .action-input {
            width: 100px;
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 6px;
        }

        .action-button {
            padding: 6px 10px;
            border: none;
            border-radius: 6px;
            background: #1677ff;
            color: white;
            cursor: pointer;
        }

        .action-button-secondary {
            background: #666;
        }

        img {
            max-width: 220px;
            max-height: 140px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }

        .empty {
            padding: 30px;
            background: white;
            border-radius: 10px;
        }
    </style>
</head>

<body>
    <h1>安全帽违规告警看板</h1>

    {% if auto_refresh_seconds > 0 %}
    <div class="refresh-info">
        页面每 {{ auto_refresh_seconds }} 秒自动刷新一次，用于实时显示最新告警。
    </div>
    {% endif %}

    <div class="top-dashboard">
        <div class="left-dashboard">
            <div class="cards">
                <div class="card">
                    <div class="card-title">告警总数</div>
                    <div class="card-value">{{ summary.total_count }}</div>
                </div>

                <div class="card">
                    <div class="card-title">今日告警</div>
                    <div class="card-value">{{ summary.today_count }}</div>
                </div>

                <div class="card">
                    <div class="card-title">平均置信度</div>
                    <div class="card-value">{{ summary.avg_confidence }}</div>
                </div>

                <div class="card">
                    <div class="card-title">最新告警时间</div>
                    <div class="card-value" style="font-size:16px;">{{ summary.latest_time }}</div>
                </div>

                <div class="card">
                    <div class="card-title">未处理告警</div>
                    <div class="card-value">{{ summary.pending_count }}</div>
                </div>

                <div class="card">
                    <div class="card-title">已处理告警</div>
                    <div class="card-value">{{ summary.handled_count }}</div>
                </div>
            </div>

            <div class="filter-box">
                <form method="get" class="filter-form">
                    <div class="filter-item">
                        <label>事件：</label>
                        <select name="event">
                            <option value="" {% if not filters.event %}selected{% endif %}>全部</option>
                            <option value="no_helmet" {% if filters.event == "no_helmet" %}selected{% endif %}>no_helmet</option>
                        </select>
                    </div>

                    <div class="filter-item">
                        <label>模型类型：</label>
                        <input type="text" name="model_type" value="{{ filters.model_type }}" placeholder="onnxruntime_modular">
                    </div>

                    <div class="filter-item">
                        <label>最低置信度：</label>
                        <input type="text" name="min_conf" value="{{ filters.min_conf }}" placeholder="0.5">
                    </div>

                    <div class="filter-item">
                        <label>显示条数：</label>
                        <input type="number" name="limit" value="{{ filters.limit }}" min="1" max="500">
                    </div>

                    <div class="filter-item">
                        <label>状态：</label>
                        <select name="status">
                            <option value="" {% if not filters.status %}selected{% endif %}>全部</option>
                            <option value="pending" {% if filters.status == "pending" %}selected{% endif %}>未处理</option>
                            <option value="handled" {% if filters.status == "handled" %}selected{% endif %}>已处理</option>
                        </select>
                    </div>

                    <div class="filter-actions">
                        <button type="submit" class="filter-button">筛选</button>
                        <a href="/" class="filter-link">重置</a>
                        <a href="{{ export_url }}" class="filter-link filter-export">导出 CSV</a>
                    </div>
                </form>
            </div>
        </div>

        <div class="chart-box">
            <div class="chart-title">最近 7 天告警趋势</div>

            {% set max_count = daily_counts | map(attribute='count') | max %}
            {% if max_count == 0 %}
                {% set max_count = 1 %}
            {% endif %}

            <div class="bar-chart">
                {% for item in daily_counts %}
                <div class="bar-item">
                    <div class="bar-count">{{ item.count }}</div>
                    <div class="bar" style="height: {{ (item.count / max_count * 70) | int }}px;"></div>
                    <div class="bar-date">{{ item.date[5:] }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    {% if alarms %}
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>时间</th>
                <th>设备 ID</th>
                <th>模型类型</th>
                <th>事件</th>
                <th>置信度</th>
                <th>状态</th>
                <th>告警截图</th>
                <th>操作</th>
            </tr>
        </thead>

        <tbody>
            {% for alarm in alarms %}
            <tr class="{% if alarm.id == latest_alarm_id %}latest-row{% endif %}">
                <td>
                    <a href="/alarm/{{ alarm.id }}">{{ alarm.id }}</a>
                    {% if alarm.id == latest_alarm_id %}
                        <span class="latest-badge">最新</span>
                    {% endif %}
                </td>
                <td>{{ alarm.timestamp }}</td>
                <td>{{ alarm.device_id }}</td>
                <td>{{ alarm.model_type }}</td>
                <td><span class="tag">{{ alarm.event }}</span></td>
                <td>{{ alarm.confidence }}</td>

                <td>
                    {% if alarm.status == "handled" %}
                        <span class="status-handled">已处理</span>
                    {% else %}
                        <span class="status-pending">未处理</span>
                    {% endif %}
                </td>

                <td>
                    {% if alarm.image_file %}
                    <a href="/alarm-image/{{ alarm.image_file }}" target="_blank">
                        <img src="/alarm-image/{{ alarm.image_file }}">
                    </a>
                    {% else %}
                    无图片
                    {% endif %}
                </td>

                <td>
                    {% if alarm.status != "handled" %}
                    <form method="post" action="/handle/{{ alarm.id }}" class="action-form">
                        <input type="text" name="remark" placeholder="备注" class="action-input">
                        <button type="submit" class="action-button">确认处理</button>
                    </form>
                    {% else %}
                    <div style="font-size: 13px; color: #666; margin-bottom: 6px;">
                        {{ alarm.handled_at or "" }}
                    </div>
                    <form method="post" action="/pending/{{ alarm.id }}" class="action-form">
                        <button type="submit" class="action-button action-button-secondary">恢复未处理</button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div class="empty">
        暂无符合条件的告警记录。
    </div>
    {% endif %}

{% if auto_refresh_seconds > 0 %}
<script>
    setTimeout(function () {
        window.location.reload();
    }, {{ auto_refresh_seconds }} * 1000);
</script>
{% endif %}
</body>
</html>
"""

DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>告警详情</title>
    <style>
        body {
            font-family: Arial, "Microsoft YaHei", sans-serif;
            margin: 30px;
            background: #f5f6fa;
            color: #222;
        }

        .container {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            max-width: 1100px;
            margin: 0 auto;
        }

        h1 {
            margin-top: 0;
        }

        .info-grid {
            display: grid;
            grid-template-columns: 160px 1fr;
            gap: 12px;
            margin-bottom: 20px;
        }

        .label {
            color: #666;
            font-weight: bold;
        }

        .value {
            color: #222;
        }

        .status-pending {
            color: #ff4d4f;
            font-weight: bold;
        }

        .status-handled {
            color: #52c41a;
            font-weight: bold;
        }

        img {
            max-width: 100%;
            border-radius: 10px;
            border: 1px solid #ddd;
            margin-top: 12px;
        }

        .actions {
            margin-top: 24px;
        }

        .actions input {
            padding: 8px;
            width: 240px;
            border: 1px solid #ccc;
            border-radius: 6px;
        }

        .actions button {
            padding: 8px 14px;
            border: none;
            border-radius: 6px;
            background: #1677ff;
            color: white;
            cursor: pointer;
        }

        .secondary {
            background: #666 !important;
        }

        a {
            color: #1677ff;
            text-decoration: none;
        }

        .back {
            display: inline-block;
            margin-bottom: 16px;
        }
    </style>
</head>

<body>
    <div class="container">
        <a class="back" href="/">← 返回告警看板</a>

        <h1>告警详情 #{{ alarm.id }}</h1>

        <div class="info-grid">
            <div class="label">告警时间</div>
            <div class="value">{{ alarm.timestamp }}</div>

            <div class="label">设备 ID</div>
            <div class="value">{{ alarm.device_id }}</div>

            <div class="label">模型类型</div>
            <div class="value">{{ alarm.model_type }}</div>

            <div class="label">事件类型</div>
            <div class="value">{{ alarm.event }}</div>

            <div class="label">置信度</div>
            <div class="value">{{ alarm.confidence }}</div>

            <div class="label">状态</div>
            <div class="value">
                {% if alarm.status == "handled" %}
                    <span class="status-handled">已处理</span>
                {% else %}
                    <span class="status-pending">未处理</span>
                {% endif %}
            </div>

            <div class="label">处理时间</div>
            <div class="value">{{ alarm.handled_at or "-" }}</div>

            <div class="label">处理人</div>
            <div class="value">{{ alarm.handler or "-" }}</div>

            <div class="label">备注</div>
            <div class="value">{{ alarm.remark or "-" }}</div>

            <div class="label">图片路径</div>
            <div class="value">{{ alarm.image_path }}</div>

            <div class="label">创建时间</div>
            <div class="value">{{ alarm.created_at }}</div>
        </div>

        {% if image_file %}
        <h2>告警截图</h2>
        <a href="/alarm-image/{{ image_file }}" target="_blank">
            <img src="/alarm-image/{{ image_file }}">
        </a>
        {% endif %}

        <div class="actions">
            {% if alarm.status != "handled" %}
            <form method="post" action="/handle/{{ alarm.id }}">
                <input type="text" name="remark" placeholder="填写处理备注">
                <button type="submit">确认处理</button>
            </form>
            {% else %}
            <form method="post" action="/pending/{{ alarm.id }}">
                <button type="submit" class="secondary">恢复未处理</button>
            </form>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

def parse_float(value):
    if value is None or value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value, default=100):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@app.route("/")
def index():
    event = request.args.get("event", "").strip()
    model_type = request.args.get("model_type", "").strip()
    status = request.args.get("status", "").strip()
    min_conf_raw = request.args.get("min_conf", "").strip()
    limit_raw = request.args.get("limit", "100").strip()

    min_conf = parse_float(min_conf_raw)
    limit = parse_int(limit_raw, default=100)

    if limit <= 0:
        limit = 100

    if limit > 500:
        limit = 500

    alarms = alarm_database.get_alarms_filtered(
        event=event,
        model_type=model_type,
        status=status,
        min_conf=min_conf,
        limit=limit
    )

    for alarm in alarms:
        image_path = alarm.get("image_path", "")
        image_file = os.path.basename(image_path.replace("\\", "/"))
        alarm["image_file"] = image_file

    summary = alarm_database.get_summary()
    daily_counts = alarm_database.get_daily_counts(days=7)
    latest_alarm_id = alarms[0]["id"] if alarms else None

    filters = {
        "event": event,
        "model_type": model_type,
        "status": status,
        "min_conf": min_conf_raw,
        "limit": limit
    }

    export_url = url_for("export_csv", **request.args)

    return render_template_string(
        HTML_TEMPLATE,
        alarms=alarms,
        summary=summary,
        daily_counts=daily_counts,
        filters=filters,
        export_url=export_url,
        latest_alarm_id=latest_alarm_id,
        auto_refresh_seconds=DASHBOARD_AUTO_REFRESH_SECONDS
    )


@app.route("/handle/<int:alarm_id>", methods=["POST"])
def handle_alarm(alarm_id):
    remark = request.form.get("remark", "").strip()

    alarm_database.handle_alarm(
        alarm_id,
        handler="admin",
        remark=remark
    )

    return redirect(url_for("alarm_detail", alarm_id=alarm_id))


@app.route("/alarm/<int:alarm_id>")
def alarm_detail(alarm_id):
    alarm = alarm_database.get_alarm_by_id(alarm_id)

    if alarm is None:
        return "告警记录不存在", 404

    image_path = alarm.get("image_path", "")
    image_file = os.path.basename(image_path.replace("\\", "/"))

    return render_template_string(
        DETAIL_TEMPLATE,
        alarm=alarm,
        image_file=image_file
    )


@app.route("/pending/<int:alarm_id>", methods=["POST"])
def pending_alarm(alarm_id):
    alarm_database.mark_pending(alarm_id)

    return redirect(url_for("alarm_detail", alarm_id=alarm_id))


@app.route("/export-csv")
def export_csv():
    event = request.args.get("event", "").strip()
    model_type = request.args.get("model_type", "").strip()
    status = request.args.get("status", "").strip()
    min_conf_raw = request.args.get("min_conf", "").strip()
    limit_raw = request.args.get("limit", "500").strip()

    min_conf = parse_float(min_conf_raw)
    limit = parse_int(limit_raw, default=500)

    if limit <= 0:
        limit = 500

    if limit > 5000:
        limit = 5000

    alarms = alarm_database.get_alarms_filtered(
        event=event,
        model_type=model_type,
        status=status,
        min_conf=min_conf,
        limit=limit
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id",
        "timestamp",
        "device_id",
        "model_type",
        "event",
        "confidence",
        "status",
        "handled_at",
        "handler",
        "remark",
        "image_path",
        "created_at"
    ])

    for alarm in alarms:
        writer.writerow([
            alarm.get("id", ""),
            alarm.get("timestamp", ""),
            alarm.get("device_id", ""),
            alarm.get("model_type", ""),
            alarm.get("event", ""),
            alarm.get("confidence", ""),
            alarm.get("status", ""),
            alarm.get("handled_at", ""),
            alarm.get("handler", ""),
            alarm.get("remark", ""),
            alarm.get("image_path", ""),
            alarm.get("created_at", "")
        ])

    csv_content = "\ufeff" + output.getvalue()

    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=alarm_records.csv"
        }
    )


@app.route("/alarm-image/<filename>")
def alarm_image(filename):
    return send_from_directory(ALARM_DIR, filename)


if __name__ == "__main__":
    print("安全帽违规告警看板启动中...")
    print(f"浏览器打开：http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=False)