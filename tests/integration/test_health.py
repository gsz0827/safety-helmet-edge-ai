def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "industrial-ai-safety-backend"
    assert data["env"] == "test"


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"
