import pytest

from app import cli
from app.core.security import verify_password
from app.models import Usuario


def run(monkeypatch, *passwords: str, email="novo@estufa.com", name="Novo ADM"):
    answers = iter(passwords)
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt="": next(answers))
    monkeypatch.setattr("sys.argv", ["app.cli", "create-admin", "--email", email, "--name", name])
    cli.main()


def test_creates_admin(monkeypatch, db, capsys):
    run(monkeypatch, "Senha123", "Senha123", email="Novo@Estufa.com")
    user = db.query(Usuario).filter_by(email="novo@estufa.com").one()
    assert user.adm and user.ativo
    assert verify_password("Senha123", user.senha_hash)[0]
    assert "criado" in capsys.readouterr().out


def test_promotes_existing_user_and_revokes_sessions(monkeypatch, db, make_user):
    user = make_user("comum@estufa.com", active=False)
    run(monkeypatch, "Outra456", "Outra456", email="comum@estufa.com")
    db.refresh(user)
    assert user.adm and user.ativo and user.token_versao == 1
    assert verify_password("Outra456", user.senha_hash)[0]


@pytest.mark.parametrize("passwords", [("Senha123", "Diferente1"), ("curta", "curta")])
def test_rejects_bad_password(monkeypatch, db, passwords):
    with pytest.raises(SystemExit):
        run(monkeypatch, *passwords)
    assert db.query(Usuario).count() == 0
