from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_serves_frontend_and_falls_back_to_index(tmp_path, monkeypatch):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>spa</html>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    monkeypatch.setenv("FRONTEND_DIST_DIR", str(tmp_path))
    get_settings.cache_clear()
    client = TestClient(create_app())

    assert client.get("/").text == "<html>spa</html>"
    assert client.get("/historico").text == "<html>spa</html>"  # rota do React Router
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/api/nao-existe").status_code == 404
    assert client.get("/api/health").status_code == 200
    get_settings.cache_clear()
