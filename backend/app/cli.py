"""Comandos administrativos.

Criar o primeiro administrador (ou promover/redefinir um existente):
    python -m app.cli create-admin --email admin@exemplo.com --name "Administrador"
A senha é pedida no terminal (não fica no histórico do shell).
"""

import argparse
import getpass
import sys

from pydantic import ValidationError

from app.core.clock import utcnow
from app.core.security import hash_password
from app.database.session import _session_factory
from app.models import Usuario
from app.repositories.user_repository import UserRepository
from app.schemas.user import PASSWORD_RULE, UserCreate


def create_admin(email: str, name: str) -> None:
    password = getpass.getpass("Senha: ")
    if password != getpass.getpass("Confirme a senha: "):
        sys.exit("As senhas não conferem.")
    try:
        UserCreate(email=email, name=name, password=password)
    except ValidationError:
        sys.exit(f"Dados inválidos. {PASSWORD_RULE}")

    with _session_factory()() as db:
        user = UserRepository(db).get_by_email(email)
        if user:
            user.adm = True
            user.ativo = True
            user.senha_hash = hash_password(password)
            user.token_versao += 1
            action = "atualizado"
        else:
            db.add(
                Usuario(
                    email=email.lower(),
                    nome=name,
                    senha_hash=hash_password(password),
                    data_criacao=utcnow(),
                    adm=True,
                    ativo=True,
                    tentativas_falhas=0,
                    token_versao=0,
                )
            )
            action = "criado"
        db.commit()
    print(f"Administrador {email} {action}.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    admin = sub.add_parser("create-admin", help="Criar ou promover um administrador")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name", required=True)
    args = parser.parse_args()
    if args.command == "create-admin":
        create_admin(args.email, args.name)


if __name__ == "__main__":
    main()
