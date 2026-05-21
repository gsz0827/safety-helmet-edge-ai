def test_create_and_query_device(client):
    payload = {
        "device_id": "edge_ai_test_001",
        "name": "测试边缘节点",
        "location": "测试车间",
    }

    response = client.post("/api/v1/devices", json=payload)

    assert response.status_code == 200

    data = response.json()["data"]
    assert data["device_id"] == "edge_ai_test_001"
    assert data["status"] == "offline"

    response = client.get("/api/v1/devices/edge_ai_test_001")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "测试边缘节点"


def test_update_device_status(client):
    response = client.patch(
        "/api/v1/devices/edge_ai_test_001/status",
        json={"status": "online"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "online"


def test_create_and_query_camera(client):
    payload = {
        "camera_id": "cam_test_001",
        "device_id": "edge_ai_test_001",
        "name": "测试摄像头",
        "stream_url": "rtsp://example.com/test",
    }

    response = client.post("/api/v1/cameras", json=payload)

    assert response.status_code == 200

    data = response.json()["data"]
    assert data["camera_id"] == "cam_test_001"
    assert data["device_id"] == "edge_ai_test_001"
    assert data["enabled"] is True

    response = client.get("/api/v1/cameras/cam_test_001")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "测试摄像头"


def test_update_camera_status_and_enabled(client):
    response = client.patch(
        "/api/v1/cameras/cam_test_001/status",
        json={"status": "online"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "online"

    response = client.patch(
        "/api/v1/cameras/cam_test_001/enabled",
        json={"enabled": False},
    )

    assert response.status_code == 200
    assert response.json()["data"]["enabled"] is False
