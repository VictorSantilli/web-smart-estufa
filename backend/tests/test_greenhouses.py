import pytest


@pytest.fixture
def setup(make_user, make_greenhouse, login):
    g1, g2 = make_greenhouse("Estufa 01"), make_greenhouse("Estufa 02")
    make_user("admin@estufa.com", admin=True)
    make_user("a@estufa.com", greenhouses=(g1,))
    make_user("b@estufa.com", greenhouses=(g2,))
    make_user("semacesso@estufa.com")
    return {
        "g1": g1.id,
        "g2": g2.id,
        "admin": login("admin@estufa.com"),
        "a": login("a@estufa.com"),
        "b": login("b@estufa.com"),
        "none": login("semacesso@estufa.com"),
    }


def names(response):
    return [g["name"] for g in response.json()]


def test_common_user_lists_only_authorized_greenhouses(client, setup):
    assert names(client.get("/api/greenhouses", headers=setup["a"])) == ["Estufa 01"]
    assert names(client.get("/api/greenhouses", headers=setup["b"])) == ["Estufa 02"]
    assert client.get("/api/greenhouses", headers=setup["none"]).json() == []


def test_admin_lists_all_greenhouses(client, setup):
    assert names(client.get("/api/greenhouses", headers=setup["admin"])) == [
        "Estufa 01",
        "Estufa 02",
    ]


def test_changing_id_in_url_does_not_grant_access(client, setup):
    """Usuário A tentando abrir a Estufa 02 trocando o ID: 404, igual a uma estufa inexistente."""
    other = client.get(f"/api/greenhouses/{setup['g2']}", headers=setup["a"])
    missing = client.get("/api/greenhouses/999", headers=setup["a"])
    assert other.status_code == missing.status_code == 404
    assert other.json() == missing.json()
    assert client.get(f"/api/greenhouses/{setup['g1']}", headers=setup["a"]).status_code == 200


def test_admin_sees_any_greenhouse(client, setup):
    assert client.get(f"/api/greenhouses/{setup['g2']}", headers=setup["admin"]).status_code == 200


def test_greenhouse_users_is_admin_only(client, setup):
    response = client.get(f"/api/greenhouses/{setup['g1']}/users", headers=setup["admin"])
    assert response.status_code == 200
    assert [u["email"] for u in response.json()] == ["a@estufa.com"]
    assert (
        client.get(f"/api/greenhouses/{setup['g1']}/users", headers=setup["a"]).status_code == 403
    )


def test_anonymous_cannot_list(client, setup):
    assert client.get("/api/greenhouses").status_code == 401
