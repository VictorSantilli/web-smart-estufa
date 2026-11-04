from datetime import date

from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UsuarioEstufa(Base):
    """Vínculo N:N entre usuários e estufas (permissão de acesso).

    A chave primária composta é criada pela migração 001_web_app.sql.
    """

    __tablename__ = "UsuarioEstufa"

    usuario_id: Mapped[int] = mapped_column(
        "UsuarioId", Integer, ForeignKey("Usuarios.Id"), primary_key=True
    )
    estufa_id: Mapped[int] = mapped_column(
        "EstufaId", Integer, ForeignKey("Estufas.Id"), primary_key=True
    )
    data_vinculo: Mapped[date] = mapped_column("DataVinculo", Date)

    usuario: Mapped["Usuario"] = relationship(back_populates="vinculos")  # noqa: F821
    estufa: Mapped["Estufa"] = relationship(back_populates="vinculos")  # noqa: F821
