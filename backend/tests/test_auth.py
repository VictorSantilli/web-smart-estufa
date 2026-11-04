import bcrypt
import jwt

from app.core.config import get_settings
from app.core.security import REFRESH_COOKIE_NAME, create_token
from tests.conftest import PASSWORD


def test_login_success_returns_token_and_refresh_cookie(client, make_user):
    make_user("ana@estufa.com")
    response = client.post(
        "/api/auth/login", json={"email": "ana@estufa.com", "password": PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 15 * 60
    cookie = response.headers["set-cookie"]
    assert REFRESH_COOKIE_NAME in cookie
    assert "HttpOnly" in cookie
    assert "samesite=strict" in cookie.lower()
    assert "Path=/api/auth" in cookie
    assert "SenhaHash" not in response.text and "senha" not in response.text.lower()


def test_login_email_is_case_insensitive(client, make_user):
    make_user("ana@estufa.com")
    response = client.post(
        "/api/auth/login", json={"email": " ANA@Estufa.com ", "password": PASSWORD}
    )
    assert response.status_code == 200


def test_wrong_password_and_unknown_email_get_same_error(client, make_user):
    make_user("ana@estufa.com")
    wrong = client.post("/api/auth/login", json={"email": "ana@estufa.com", "password": "errada1"})
    unknown = client.post("/api/auth/login", json={"email": "x@estufa.com", "password": "errada1"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert wrong.json()["detail"]["code"] == "invalid_credentials"


def test_inactive_user_cannot_login(client, make_user):
    make_user("ana@estufa.com", active=False)
    response = client.post(
        "/api/auth/login", json={"email": "ana@estufa.com", "password": PASSWORD}
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"


def test_account_locks_after_max_attempts(client, make_user, db):
    user = make_user("ana@estufa.com")
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "ana@estufa.com", "password": "errada1"})
    # Mesmo com a senha certa, a conta fica bloqueada
    response = client.post(
        "/api/auth/login", json={"email": "ana@estufa.com", "password": PASSWORD}
    )
    assert response.status_code == 429
    db.refresh(user)
    assert user.bloqueado_ate is not None


def test_ip_rate_limit(client, make_user):
    for _ in range(10):
        client.post("/api/auth/login", json={"email": "x@estufa.com", "password": "a"})
    response = client.post("/api/auth/login", json={"email": "x@estufa.com", "password": "a"})
    assert response.status_code == 429


def test_login_validation_error(client):
    response = client.post("/api/auth/login", json={"email": "", "password": ""})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_accepts_existing_bcrypt_hash_from_mobile(client, make_user, db):
    """Hashes $2a$/$2b$ já gravados pelo app mobile continuam válidos."""
    user = make_user("mobile@estufa.com")
    user.senha_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(prefix=b"2a")).decode()
    db.commit()
    response = client.post(
        "/api/auth/login", json={"email": "mobile@estufa.com", "password": PASSWORD}
    )
    assert response.status_code == 200


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "not_authenticated"


def test_me_returns_current_user(client, make_user, login):
    make_user("ana@estufa.com", admin=True)
    response = client.get("/api/auth/me", headers=login("ana@estufa.com"))
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "ana@estufa.com",
        "name": "Ana",
        "is_admin": True,
    }


def test_rejects_tampered_and_wrong_type_tokens(client, make_user):
    user = make_user("ana@estufa.com")
    forged = jwt.encode(
        {"sub": str(user.id), "tv": 0, "type": "access", "exp": 9999999999}, "outra-chave"
    )
    refresh_as_access = create_token(user.id, 0, "refresh")
    for token in (forged, refresh_as_access, "lixo"):
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_expired_token_is_rejected(client, make_user):
    user = make_user("ana@estufa.com")
    settings = get_settings()
    expired = jwt.encode(
        {"sub": str(user.id), "tv": 0, "type": "access", "exp": 1},
        settings.jwt_secret.get_secret_value(),
    )
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_refresh_issues_new_access_token(client, make_user):
    make_user("ana@estufa.com")
    client.post("/api/auth/login", json={"email": "ana@estufa.com", "password": PASSWORD})
    response = client.post("/api/auth/refresh")
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert (
        client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    )


def test_refresh_without_cookie_fails(client):
    response = client.post("/api/auth/refresh")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "session_expired"


def test_deactivation_revokes_existing_sessions(client, make_user, login, db):
    user = make_user("ana@estufa.com")
    headers = login("ana@estufa.com")
    user.ativo = False
    user.token_versao += 1
    db.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.post("/api/auth/refresh").status_code == 401


def test_logout_clears_cookie(client, make_user):
    make_user("ana@estufa.com")
    client.post("/api/auth/login", json={"email": "ana@estufa.com", "password": PASSWORD})
    response = client.post("/api/auth/logout")
    assert response.status_code == 204
    assert client.post("/api/auth/refresh").status_code == 401
