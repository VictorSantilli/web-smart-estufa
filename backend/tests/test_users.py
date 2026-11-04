import pytest

from tests.conftest import PASSWORD


@pytest.fixture
def setup(make_user, make_greenhouse, login):
    g1, g2 = make_greenhouse("Estufa 01"), make_greenhouse("Estufa 02")
    make_user("admin@estufa.com", admin=True)
    make_user("ana@estufa.com", greenhouses=(g1,))
    return {
        "g1": g1,
        "g2": g2,
        "admin": login("admin@estufa.com"),
        "common": login("ana@estufa.com"),
    }


def new_user(**overrides):
    return {
        "email": "bia@estufa.com",
        "name": "Bia",
        "password": "Segura123",
        "is_admin": False,
        "greenhouse_ids": [],
    } | overrides


def test_admin_creates_user_with_greenhouses(client, setup):
    response = client.post(
        "/api/users", json=new_user(greenhouse_ids=[setup["g2"].id]), headers=setup["admin"]
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "bia@estufa.com"
    assert body["is_active"] is True
    assert [g["name"] for g in body["greenhouses"]] == ["Estufa 02"]
    assert "password" not in body and "senha_hash" not in body
    # O novo usuário consegue logar
    login = client.post(
        "/api/auth/login", json={"email": "bia@estufa.com", "password": "Segura123"}
    )
    assert login.status_code == 200


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/users"),
        ("post", "/api/users"),
        ("get", "/api/users/1"),
        ("patch", "/api/users/1"),
        ("post", "/api/users/1/deactivate"),
        ("post", "/api/users/1/activate"),
        ("put", "/api/users/1/greenhouses"),
    ],
)
def test_common_user_cannot_use_admin_routes(client, setup, method, path):
    payload = {"greenhouse_ids": [1]} if method == "put" else new_user()
    kwargs = {} if method == "get" else {"json": payload}
    response = getattr(client, method)(path, headers=setup["common"], **kwargs)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "forbidden"


def test_anonymous_cannot_use_admin_routes(client, setup):
    assert client.get("/api/users").status_code == 401
    assert client.post("/api/users", json=new_user()).status_code == 401


def test_duplicate_email_conflict(client, setup):
    response = client.post(
        "/api/users", json=new_user(email="ANA@estufa.com"), headers=setup["admin"]
    )
    assert response.status_code == 409


@pytest.mark.parametrize("password", ["curta1", "semnumero", "12345678"])
def test_weak_password_rejected(client, setup, password):
    response = client.post("/api/users", json=new_user(password=password), headers=setup["admin"])
    assert response.status_code == 422


def test_invalid_email_rejected(client, setup):
    response = client.post("/api/users", json=new_user(email="nao-e-email"), headers=setup["admin"])
    assert response.status_code == 422


def test_unknown_greenhouse_rejected(client, setup):
    response = client.post(
        "/api/users", json=new_user(greenhouse_ids=[999]), headers=setup["admin"]
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "greenhouse_not_found"


def test_list_with_search_and_pagination(client, setup):
    response = client.get("/api/users?q=ana&page=1&page_size=10", headers=setup["admin"])
    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 1
    assert body["items"][0]["email"] == "ana@estufa.com"
    assert client.get("/api/users?page_size=500", headers=setup["admin"]).status_code == 422


def test_update_user(client, setup):
    response = client.patch("/api/users/2", json={"name": "Ana Paula"}, headers=setup["admin"])
    assert response.status_code == 200
    assert response.json()["name"] == "Ana Paula"


def test_password_change_revokes_sessions(client, setup):
    client.patch("/api/users/2", json={"password": "NovaSenha9"}, headers=setup["admin"])
    assert client.get("/api/auth/me", headers=setup["common"]).status_code == 401
    old = client.post("/api/auth/login", json={"email": "ana@estufa.com", "password": PASSWORD})
    assert old.status_code == 401


def test_deactivate_and_activate(client, setup):
    response = client.post("/api/users/2/deactivate", headers=setup["admin"])
    assert response.json()["is_active"] is False
    assert client.get("/api/auth/me", headers=setup["common"]).status_code == 401
    response = client.post("/api/users/2/activate", headers=setup["admin"])
    assert response.json()["is_active"] is True


def test_admin_cannot_deactivate_or_demote_self(client, setup):
    assert client.post("/api/users/1/deactivate", headers=setup["admin"]).status_code == 400
    response = client.patch("/api/users/1", json={"is_admin": False}, headers=setup["admin"])
    assert response.status_code == 400


def test_set_greenhouses_replaces_access(client, setup):
    response = client.put(
        "/api/users/2/greenhouses",
        json={"greenhouse_ids": [setup["g2"].id]},
        headers=setup["admin"],
    )
    assert response.status_code == 200
    assert [g["id"] for g in response.json()["greenhouses"]] == [setup["g2"].id]
    # A permissão nova vale imediatamente
    assert (
        client.get(f"/api/greenhouses/{setup['g1'].id}", headers=setup["common"]).status_code == 404
    )
    assert (
        client.get(f"/api/greenhouses/{setup['g2'].id}", headers=setup["common"]).status_code == 200
    )


def test_user_not_found(client, setup):
    assert client.get("/api/users/999", headers=setup["admin"]).status_code == 404
