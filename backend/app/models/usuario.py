from datetime import datetime

from sqlalchemy import Boolean, DateTime, FetchedValue, Integer, String, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Usuario(Base):
    __tablename__ = "Usuarios"

    id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column("Email", String(255), unique=True)
    nome: Mapped[str | None] = mapped_column("Nome", String(255))
    senha_hash: Mapped[str] = mapped_column("SenhaHash", String(255))
    data_criacao: Mapped[datetime] = mapped_column("DataCriacao", DateTime)
    adm: Mapped[bool] = mapped_column("Adm", Boolean)
    push_token: Mapped[str | None] = mapped_column("PushToken", Unicode(255))

    # Colunas adicionadas pela migração 001_web_app.sql
    ativo: Mapped[bool] = mapped_column("Ativo", Boolean, server_default=FetchedValue())
    tentativas_falhas: Mapped[int] = mapped_column(
        "TentativasFalhas", Integer, server_default=FetchedValue()
    )
    bloqueado_ate: Mapped[datetime | None] = mapped_column("BloqueadoAte", DateTime)  # UTC
    token_versao: Mapped[int] = mapped_column("TokenVersao", Integer, server_default=FetchedValue())

    vinculos: Mapped[list["UsuarioEstufa"]] = relationship(  # noqa: F821
        back_populates="usuario", cascade="all, delete-orphan"
    )
