"""Testes de segurança transversais (Etapa 6)."""

import re

import pytest
from fastapi.testclient import TestClient

from app.core.client_ip import client_ip
from app.core.config import Settings, get_settings
from app.core.rate_limit import SlidingWindowLimiter
from app.main import create_app

# Rotas que respondem sem access token, por desenho.
PUBLIC_ROUTES = {
    ("GET", "/api/health"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/refresh"),
    ("POST", "/api/auth/logout"),
}


def api_routes():
    """Todas as rotas da API, lidas do OpenAPI (inclui routers aninhados)."""
    schema = create_app().openapi()
    for path, operations in schema["paths"].items():
        for method in operations:
            yield method.upper(), path


def concrete(path: str, greenhouse_id: int = 1) -> str:
    path = path.replace("{greenhouse_id}", str(greenhouse_id))
    return re.sub(r"\{[^}]+\}", "1", path)


# ---------- inventário de rotas: nenhuma rota nova fica aberta por engano ----------


@pytest.mark.parametrize(("method", "path"), sorted(set(api_routes()) - PUBLIC_ROUTES))
def test_every_private_route_requires_token(client, method, path):
    response = client.request(method, concrete(path), json={})
    assert response.status_code == 401, f"{method} {path} respondeu {response.status_code}"


GREENHOUSE_ROUTES = sorted((m, p) for m, p in api_routes() if "{greenhouse_id}" in p and m == "GET")


@pytest.mark.parametrize(("method", "path"), GREENHOUSE_ROUTES)
def test_every_greenhouse_route_hides_unauthorized_greenhouse(
    client, make_user, make_greenhouse, login, method, path
):
    mine, other = make_greenhouse("Minha"), make_greenhouse("Outra")
    make_user("comum@estufa.com", greenhouses=(mine,))
    headers = login("comum@estufa.com")
    response = client.request(method, concrete(path, other.id), headers=headers)
    # 404 (ou 403 em rotas só de ADM): nunca os dados da estufa de outra pessoa.
    assert response.status_code in (403, 404), f"{path} respondeu {response.status_code}"


def test_route_inventory_is_complete():
    # Garante que os testes parametrizados acima não ficaram vazios.
    routes = set(api_routes())
    assert len(routes) >= 15
    assert ("PATCH", "/api/users/{user_id}") in routes
    paths = {p for _, p in GREENHOUSE_ROUTES}
    assert {"/api/dashboard/{greenhouse_id}", "/api/history/{greenhouse_id}"} <= paths


# ---------- cabeçalhos ----------


def test_security_headers_on_api(client):
    response = client.get("/api/health")
    h = response.headers
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert h["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in h["Content-Security-Policy"]
    assert "script-src 'self'" in h["Content-Security-Policy"]
    assert "unsafe-inline" not in h["Content-Security-Policy"].split("script-src")[1].split(";")[0]
    assert "camera=()" in h["Permissions-Policy"]
    assert "Strict-Transport-Security" not in h  # só em produção


def test_docs_get_their_own_csp(client):
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "cdn.jsdelivr.net" in response.headers["Content-Security-Policy"]


def test_spa_gets_strict_csp_without_no_store(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<html>spa</html>")
    monkeypatch.setenv("FRONTEND_DIST_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        response = TestClient(create_app()).get("/historico")
        assert "cdn.jsdelivr.net" not in response.headers["Content-Security-Policy"]
        assert "Cache-Control" not in response.headers
    finally:
        get_settings.cache_clear()


# ---------- configuração de produção ----------


def prod(**kwargs) -> Settings:
    base = {
        "app_env": "production",
        "jwt_secret": "p" * 40,
        "database_url": "mssql+pyodbc://u:p@h/db?driver=ODBC+Driver+18+for+SQL+Server",
    }
    return Settings(_env_file=None, **{**base, **kwargs})


def test_docs_off_by_default_in_production():
    assert prod().docs_enabled is False
    assert prod(enable_docs=True).docs_enabled is True
    assert Settings(_env_file=None, app_env="development").docs_enabled is True


@pytest.mark.parametrize("algorithm", ["none", "RS256"])
def test_only_hmac_jwt_algorithms(algorithm):
    with pytest.raises(ValueError):
        Settings(_env_file=None, jwt_algorithm=algorithm)


# ---------- IP do cliente e limite de login ----------


class FakeRequest:
    def __init__(self, peer: str, forwarded: str | None = None) -> None:
        self.client = type("C", (), {"host": peer})()
        self.headers = {"x-forwarded-for": forwarded} if forwarded else {}


@pytest.fixture
def hops(monkeypatch):
    def _set(value: int) -> None:
        monkeypatch.setenv("TRUSTED_PROXY_HOPS", str(value))
        get_settings.cache_clear()

    yield _set
    monkeypatch.delenv("TRUSTED_PROXY_HOPS", raising=False)
    get_settings.cache_clear()


def test_client_ip_ignores_forwarded_header_without_trusted_proxy(hops):
    hops(0)
    assert client_ip(FakeRequest("10.0.0.5", "1.2.3.4")) == "10.0.0.5"


def test_client_ip_uses_entry_added_by_trusted_proxy(hops):
    hops(1)
    # O cliente forjou "6.6.6.6"; o ingress acrescentou o IP real no fim.
    assert client_ip(FakeRequest("10.0.0.5", "6.6.6.6, 200.1.2.3")) == "200.1.2.3"
    assert client_ip(FakeRequest("10.0.0.5")) == "10.0.0.5"


def test_spoofed_forwarded_for_does_not_bypass_login_limit(client, hops):
    hops(1)
    for i in range(10):
        client.post(
            "/api/auth/login",
            json={"email": "x@estufa.com", "password": "a"},
            headers={"X-Forwarded-For": f"9.9.9.{i}, 200.1.2.3"},
        )
    response = client.post(
        "/api/auth/login",
        json={"email": "x@estufa.com", "password": "a"},
        headers={"X-Forwarded-For": "9.9.9.99, 200.1.2.3"},
    )
    assert response.status_code == 429


def test_limiter_discards_stale_keys(monkeypatch):
    limiter = SlidingWindowLimiter(max_hits=1, window_seconds=60)
    monkeypatch.setattr(SlidingWindowLimiter, "SWEEP_THRESHOLD", 3)
    clock = iter([0, 1, 2, 100])
    monkeypatch.setattr("app.core.rate_limit.time.monotonic", lambda: next(clock))
    for key in ("a", "b", "c"):
        limiter.hit(key)
    assert len(limiter) == 3
    limiter.hit("d")  # 100 s depois: a, b e c já saíram da janela
    assert len(limiter) == 1


# ---------- senhas ----------


def test_password_longer_than_bcrypt_limit_is_rejected(client, make_user, login):
    make_user("admin@estufa.com", admin=True)
    headers = login("admin@estufa.com")
    body = {"email": "longa@estufa.com", "name": "Longa", "password": "a1" * 37}  # 74 bytes
    response = client.post("/api/users", json=body, headers=headers)
    assert response.status_code == 422
    body["password"] = "a1" * 36  # 72 bytes
    assert client.post("/api/users", json=body, headers=headers).status_code == 201


def test_password_limit_counts_bytes_not_characters(client, make_user, login):
    make_user("admin@estufa.com", admin=True)
    body = {"email": "acento@estufa.com", "name": "Acento", "password": "1" + "é" * 36}
    response = client.post("/api/users", json=body, headers=login("admin@estufa.com"))
    assert response.status_code == 422  # 37 caracteres, 73 bytes


# ---------- dados enviados pelo cliente ----------


def test_user_update_ignores_unknown_fields(client, make_user, login, db):
    make_user("admin@estufa.com", admin=True)
    target = make_user("alvo@estufa.com")
    headers = login("admin@estufa.com")
    response = client.patch(
        f"/api/users/{target.id}",
        json={"name": "Novo Nome", "token_versao": 99, "senha_hash": "x", "is_active": False},
        headers=headers,
    )
    assert response.status_code == 200
    db.refresh(target)
    assert target.nome == "Novo Nome"
    assert target.token_versao == 0 and target.ativo is True and target.senha_hash != "x"


def test_search_with_sql_characters_is_safe(client, make_user, login):
    make_user("admin@estufa.com", admin=True)
    headers = login("admin@estufa.com")
    response = client.get("/api/users", params={"q": "' OR 1=1 --"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_errors_do_not_leak_internals(client, make_user, login, monkeypatch):
    make_user("admin@estufa.com", admin=True)
    headers = login("admin@estufa.com")

    def boom(*args, **kwargs):
        raise RuntimeError("SELECT * FROM Usuarios -- senha do banco")

    monkeypatch.setattr("app.services.user_service.UserService.list_users", boom)
    response = TestClient(client.app, raise_server_exceptions=False).get(
        "/api/users", headers=headers
    )
    assert response.status_code == 500
    assert "Usuarios" not in response.text and "senha" not in response.text
