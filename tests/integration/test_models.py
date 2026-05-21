def test_create_list_active_and_activate_model(client):
    payload_v1 = {
        "name": "helmet-yolov8n",
        "version": "v1.0.0-test",
        "framework": "onnxruntime",
        "model_path": "runs/detect/helmet_final/weights/best.onnx",
        "input_size": 640,
        "precision": 0.924,
        "recall": 0.866,
        "map50": 0.936,
        "latency_ms": 23.5,
        "is_active": True,
    }

    response = client.post("/api/v1/models", json=payload_v1)

    assert response.status_code == 200

    model_v1 = response.json()["data"]
    assert model_v1["is_active"] is True

    response = client.get("/api/v1/models/active")

    assert response.status_code == 200
    assert response.json()["data"]["version"] == "v1.0.0-test"

    payload_v2 = {
        "name": "helmet-yolov8n",
        "version": "v1.1.0-test",
        "framework": "onnxruntime",
        "model_path": "runs/detect/helmet_v1_1/weights/best.onnx",
        "input_size": 640,
        "precision": 0.931,
        "recall": 0.872,
        "map50": 0.941,
        "latency_ms": 22.8,
        "is_active": False,
    }

    response = client.post("/api/v1/models", json=payload_v2)

    assert response.status_code == 200

    model_v2 = response.json()["data"]

    response = client.patch(f"/api/v1/models/{model_v2['id']}/activate")

    assert response.status_code == 200
    assert response.json()["data"]["is_active"] is True

    response = client.get("/api/v1/models")

    assert response.status_code == 200
    assert response.json()["data"]["total"] >= 2
