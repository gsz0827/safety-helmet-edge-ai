def test_inference_status(client):
    response = client.get("/api/v1/inference/status")

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["model_loaded"] is False
    assert data["edge_config_path"] == "config.yaml"
    assert "load_error" in data
