"""A database-free smoke test: no migrations must occur before IDR-002."""


def test_healthcheck(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "identity-reference-poc",
    }
