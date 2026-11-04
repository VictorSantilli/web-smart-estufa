from app.api.routes import health as health_route


def test_health_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["environment"] == "test"


def test_health_degraded_when_database_down(client, monkeypatch):
    monkeypatch.setattr(health_route, "ping_database", lambda: False)
    response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"


def test_unknown_api_route_returns_standard_error(client):
    response = client.get("/api/nao-existe")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "not_found"


def test_security_headers(client):
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_openapi_available(client):
    assert client.get("/api/openapi.json").status_code == 200


def test_ping_database_logs_cause_without_url(monkeypatch, caplog):
    from app.database import session as db_session

    class _Broken:
        def connect(self):
            raise RuntimeError("Login failed for user 'app_web'")

    monkeypatch.setattr(db_session, "get_engine", lambda: _Broken())
    with caplog.at_level("WARNING", logger="app.database.session"):
        assert db_session.ping_database() is False
    assert "RuntimeError: Login failed for user 'app_web'" in caplog.text
