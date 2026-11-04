from app.core.security import hash_password, verify_password


def test_bcrypt_hash_by_default():
    assert hash_password("Senha123").startswith("$2b$")


def test_verify_rejects_garbage_hash():
    assert verify_password("x", "nao-e-hash") == (False, None)


def test_argon2id_scheme_and_rehash(monkeypatch):
    from app.core import security
    from app.core.config import get_settings

    old_bcrypt = hash_password("Senha123")
    monkeypatch.setenv("PASSWORD_HASH_SCHEME", "argon2id")
    get_settings.cache_clear()
    security._password_hash.cache_clear()
    try:
        assert hash_password("Senha123").startswith("$argon2id$")
        valid, new_hash = verify_password("Senha123", old_bcrypt)
        assert valid and new_hash and new_hash.startswith("$argon2id$")
    finally:
        monkeypatch.delenv("PASSWORD_HASH_SCHEME")
        get_settings.cache_clear()
        security._password_hash.cache_clear()
