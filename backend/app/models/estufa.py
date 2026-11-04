from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Estufa(Base):
    __tablename__ = "Estufas"

    id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str | None] = mapped_column("NomeEstufa", String(100))
    data_criacao: Mapped[datetime | None] = mapped_column("DataCriacao", DateTime)

    vinculos: Mapped[list["UsuarioEstufa"]] = relationship(back_populates="estufa")  # noqa: F821
    dispositivos: Mapped[list["Dispositivo"]] = relationship(back_populates="estufa")  # noqa: F821
