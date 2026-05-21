def test_create_list_handle_and_statistics_alarm(client):
    payload = {
        "device_id": "edge_ai_test_001",
        "camera_id": "cam_test_001",
        "event_type": "no_helmet",
        "confidence": 0.92,
        "image_url": "storage/alarm_images/test.jpg",
        "bbox_json": "[100,120,240,360]",
        "inference_time_ms": 23.5,
        "fps": 30,
    }

    response = client.post("/api/v1/alarms", json=payload)

    assert response.status_code == 200

    alarm = response.json()["data"]
    alarm_id = alarm["id"]

    assert alarm["event_type"] == "no_helmet"
    assert alarm["status"] == "pending"

    response = client.get("/api/v1/alarms")

    assert response.status_code == 200
    assert response.json()["data"]["total"] >= 1

    response = client.get(f"/api/v1/alarms/{alarm_id}")

    assert response.status_code == 200
    assert response.json()["data"]["id"] == alarm_id

    response = client.patch(
        f"/api/v1/alarms/{alarm_id}/handle",
        json={
            "handler": "tester",
            "remark": "测试处理完成",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "handled"
    assert response.json()["data"]["handler"] == "tester"

    response = client.get("/api/v1/alarms/statistics")

    assert response.status_code == 200

    statistics = response.json()["data"]
    assert statistics["total"] >= 1
    assert "no_helmet" in statistics["by_event_type"]
